import logging
from collections import defaultdict
from contextlib import ExitStack
from itertools import batched
from math import ceil
from pathlib import PurePath
from typing import Iterable, List

import brian2 as b2
import brian2hears as b2h
import dill
import graphviz
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from analyze import sound_analysis as SA
from analyze.graph import generate_flow_chart
from cochleas.consts import CFMAX, CFMIN
from cochleas.GammatoneCochlea import run_hrtf
from utils.custom_sounds import Tone
from utils.log import logger, tqdm

plt.rcParams["axes.grid"] = True
plt.rcParams["figure.figsize"] = (6, 3)

PLTWIDTH = 8


def flatten(items):
    """Yield items from any nested iterable.
    from https://stackoverflow.com/a/40857703
    """
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


def merge_in_column(images):
    logger.debug("merging in column..")
    total_height = images[0].size[1]
    for img in images[1:]:
        # only resize horizontally
        img.thumbnail([images[0].size[0], img.size[1]])
        total_height += img.size[1]

    im = Image.new(
        "RGBA",
        (images[0].size[0], total_height),
    )
    curr_height = 0
    for img in images:
        im.paste(img, (0, curr_height))
        curr_height += img.size[1]
    return im


def merge_in_rows(images, img_per_row):
    "all images converted to the size of the first image, except for column layout"
    if img_per_row == 1:
        return merge_in_column(images)

    for img in images[1:]:
        img.thumbnail([images[0].size[0], images[0].size[1]])

    rows = ceil(len(images) / img_per_row)
    im = Image.new(
        "RGBA",
        (min(img_per_row, len(images)) * images[0].size[0], images[0].size[1] * rows),
    )
    curr_height = 0
    for imgs in batched(images, img_per_row):
        curr_width = 0
        for img in imgs:
            im.paste(img, (curr_width, curr_height))
            curr_width += img.size[0]
        curr_height += images[0].size[1]
    return im


def merge_rows_files(filepaths, destination_path=None, img_per_row=4, cleanup=True):
    with ExitStack() as stack:
        files = [stack.enter_context(open(file_path, "rb")) for file_path in filepaths]
        images = [Image.open(f) for f in files]
        merged = merge_in_rows(images, img_per_row)
        if destination_path is not None:
            merged.save(destination_path)
    if cleanup:
        logger.debug("deleting tmp images")
        for path in filepaths:
            path.unlink()
    return merged


## draw_rate_vs_angle helpers


def avg_fire_rate_actv_neurons(x):
    active_neurons = set(x["senders"])
    return (len(x["times"]) / len(active_neurons)) if len(active_neurons) > 0 else 0


def firing_neurons_distribution(x):
    n2s = defaultdict(int)
    for sender in x["senders"]:
        n2s[sender] += 1
    return list(n2s.values())


def shift_senders(x, hist_logscale=False):
    "returns list of 'senders' with ids shifted to [0,num_neurons]. optionally ids are CFs"
    if hist_logscale:
        cf = b2h.erbspace(CFMIN, CFMAX, len(x["global_ids"])) / b2.Hz
        old2newid = {oldid: cf[i] for i, oldid in enumerate(x["global_ids"])}
    else:
        old2newid = {oldid: i for i, oldid in enumerate(x["global_ids"])}
    return [old2newid[i] for i in x["senders"]]


def draw_hist(
    ax, senders_renamed, angles, num_neurons, max_spikes_single_neuron, logscale=True
):
    """draws a low opacity horizontal histogram for each angle position

    includes a secondary y-axis, optionally logarithmic.
    if logscale, expects senders to be renamed to CFs
    """
    histogram_height = 0.25
    bin_count = 50
    alpha = 0.3
    if logscale:
        bins = b2h.erbspace(CFMIN, CFMAX, bin_count) / b2.Hz

        for j, angle in enumerate(angles):
            left_data = senders_renamed["L"][j]
            right_data = senders_renamed["R"][j]

            left_hist, _ = np.histogram(left_data, bins=bins)
            right_hist, _ = np.histogram(right_data, bins=bins)
            left_hist_normalized = (
                left_hist / max_spikes_single_neuron * histogram_height
            )
            right_hist_normalized = (
                right_hist / max_spikes_single_neuron * histogram_height
            )

            ax.barh(
                bins[:-1],
                -left_hist_normalized,
                height=np.diff(bins),  # bins have different sizes
                left=angle,
                color="C0",
                alpha=alpha,
                align="edge",
            )
            ax.barh(
                bins[:-1],
                right_hist_normalized,
                height=np.diff(bins),
                left=angle,
                color="C1",
                alpha=alpha,
                align="edge",
            )
        ax.set_yscale("log")
        ax.set_ylim(CFMIN, CFMAX)
        yticks = [20, 100, 500, 1000, 5000, 10000, 20000]
        ax.set_yticks(yticks)
        ax.set_yticklabels([f"{freq} Hz" for freq in yticks])
        ax.set_ylabel("approx CF (Hz)")
    else:
        bins = np.linspace(0, num_neurons, bin_count)

        for j, angle in enumerate(angles):
            left_data = senders_renamed["L"][j]
            right_data = senders_renamed["R"][j]

            left_hist, _ = np.histogram(left_data, bins=bins)
            right_hist, _ = np.histogram(right_data, bins=bins)
            left_hist_normalized = (
                left_hist / max_spikes_single_neuron * histogram_height
            )
            right_hist_normalized = (
                right_hist / max_spikes_single_neuron * histogram_height
            )

            ax.barh(
                bins[:-1],
                -left_hist_normalized,
                height=num_neurons / bin_count,
                left=angle,
                color="C0",
                alpha=alpha,
                align="edge",
            )
            ax.barh(
                bins[:-1],
                right_hist_normalized,
                height=num_neurons / bin_count,
                left=angle,
                color="C1",
                alpha=alpha,
                align="edge",
            )
        ax.set_ylabel("neuron id")
        ax.set_ylim(0, num_neurons)
    ax.yaxis.set_minor_locator(plt.NullLocator())  # remove minor ticks


def draw_rate_vs_angle(
    data, filename, show_lso=True, show_mso=True, rate=True, hist_logscale=True
):
    version = data["angle_to_rate"][0].get("version", None)
    angle_to_rate = data["angle_to_rate"]
    name = data["conf"]["model_desc"]["name"]
    sound_key = data["conf"]["sound_key"]
    show_pops = ["LSO", "MSO", "ICC"]
    if not show_lso:
        show_pops.remove("LSO")
    if not show_mso:
        show_pops.remove("MSO")

    angles = list(angle_to_rate.keys())
    sides = ["L", "R"]

    with plt.ioff():
        fig, ax = plt.subplots(len(show_pops), figsize=(8, 2 * len(show_pops)))

    for i, pop in enumerate(show_pops):
        num_active = {
            side: [len(set(angle_to_rate[angle][side][pop])) for angle in angles]
            for side in sides
        }
        tot_spikes = {
            side: [len(angle_to_rate[angle][side][pop]["times"]) for angle in angles]
            for side in sides
        }
        active_neuron_rate = {
            side: [
                avg_fire_rate_actv_neurons(angle_to_rate[angle][side][pop])
                for angle in angles
            ]
            for side in sides
        }
        distr = {
            side: [
                firing_neurons_distribution(angle_to_rate[angle][side][pop])
                for angle in angles
            ]
            for side in sides
        }

        if version > 2:  # needed for global ids
            senders_renamed = {
                side: [
                    shift_senders(angle_to_rate[angle][side][pop], hist_logscale)
                    for angle in angles
                ]
                for side in sides
            }

        ax[i].plot(angles, active_neuron_rate["L"], label=f"left  {pop}")
        ax[i].plot(angles, active_neuron_rate["R"], label=f"right {pop}")
        ax[i].set_ylabel("actv neur spk/sec (Hz)" if rate else "total pop spk/sec")
        _ = ax[i].legend()

        v = ax[i].twinx()
        v.grid(visible=False)  # or use linestyle='--'
        draw_hist(
            v,
            senders_renamed,
            angles,
            num_neurons=len(angle_to_rate[0]["L"][pop]["global_ids"]),
            max_spikes_single_neuron=max(flatten(distr.values())),
            logscale=hist_logscale,
        )

        # v.set_ylabel("spike distribution")
        # parts = [
        #     v.violinplot(
        #         distr["L"],
        #         positions=angles,
        #         widths=10,
        #         side="low",
        #         showextrema=True,
        #         showmedians=True,
        #     ),
        #     v.violinplot(
        #         distr["R"],
        #         positions=angles,
        #         widths=10,
        #         side="high",
        #         showextrema=True,
        #         showmedians=True,
        #     ),
        # ]
        # for pc in flatten([parts[0].values(), parts[1].values()]):
        #     pc.set_alpha(0.3)

    plt.suptitle(filename)
    plt.setp([ax], xticks=angles)
    plt.tight_layout()
    return fig


def draw_ITD_ILD(data):
    previous_level = logger.level
    # itd and ild functions are VERY verbose
    logger.setLevel(logging.WARNING)
    tone: Tone = data["basesound"]
    angle_to_ild = {}
    angle_to_itd = {}
    angles = list(data["angle_to_rate"].keys())
    for angle in angles:
        binaural_sound = run_hrtf(
            tone,
            angle,
            data["conf"]["parameters"]["cochlea"]["gammatone"]["subj_number"],
        )
        left = binaural_sound.left
        right = binaural_sound.right
        angle_to_itd[angle] = SA.itd(left, right)
        ild_res, all_freq_diff = SA.ild(left, right, tone.sound)
        angle_to_ild[angle] = ild_res
        # total_diff = np.sum(all_freq_diff)

    fig, ild = plt.subplots(1, sharex=True, figsize=(PLTWIDTH, 1.8))
    fig.suptitle(
        f"diff = max(|spectrum(left)|)-max(|spectrum(right)|), freq={tone.frequency}"
    )

    ild.set_ylabel("Power (dB/Hz)", color="r")
    ild.plot(
        angles,
        [angle_to_ild[angle] for angle in angles],
        label="ILD",
        marker=".",
        color="r",
    )
    ild.tick_params(axis="y", labelcolor="r")
    itd = ild.twinx()
    itd.set_ylabel("seconds", color="b")
    itd.plot(
        angles,
        [angle_to_itd[angle] for angle in angles],
        label="ITD",
        marker=".",
        color="b",
    )
    itd.tick_params(axis="y", labelcolor="b")
    _ = fig.legend()

    fig.tight_layout()
    # plt.subplots_adjust(hspace=0.6, wspace=1)
    plt.setp([ild, itd], xticks=angles)
    logger.setLevel(previous_level)
    return fig


def generate_network_vis(res, filename):
    dot = generate_flow_chart(
        res["conf"]["model_desc"]["networkdef"],
        res["conf"]["parameters"],
        "connect",
    )
    src = graphviz.Source(dot)
    src.render(outfile=filename, format="png", cleanup=True)


def paths(result_file_path: PurePath):
    filename = result_file_path.name
    result_dir = result_file_path.parent
    return [
        result_dir / "rate_vs_angle.png",
        result_dir / "ild_itd.png",
        result_dir / "netvis.png",
        result_dir / filename.replace(".pic", ".png"),
    ]


def generate_single_result(result_filepath: PurePath, cleanup=True):
    with open(result_filepath, "rb") as f:
        res = dill.load(f, ignore=True)
    RATE_VS_ANGLE, ILD_ITD, NETVIS, RESULT = paths(result_filepath)
    fig = draw_rate_vs_angle(res, result_filepath.name)
    fig.savefig(RATE_VS_ANGLE)

    itd_ild_fig = draw_ITD_ILD(res)
    itd_ild_fig.savefig(ILD_ITD)

    generate_network_vis(res, NETVIS)

    merge_rows_files([RATE_VS_ANGLE, ILD_ITD, NETVIS], RESULT, 1, cleanup)
    return 1


def generate_multi_inputs_single_net(results_paths: List[PurePath], cleanup=True):
    img_paths = []
    for path in tqdm(results_paths, desc="single imgs"):
        filename = path.name
        logger.debug(f"now working on result file {path}")
        with open(path, "rb") as f:
            res = dill.load(f, ignore=True)
        RATE_VS_ANGLE, ILD_ITD, NETVIS, RESULT = paths(path)
        fig = draw_rate_vs_angle(
            res, filename, True, True, rate=True, hist_logscale=True
        )
        fig.savefig(RATE_VS_ANGLE)
        itd_ild_fig = draw_ITD_ILD(res)
        itd_ild_fig.savefig(ILD_ITD)
        merge_rows_files([RATE_VS_ANGLE, ILD_ITD], RESULT, 1, cleanup)
        img_paths.append(RESULT)
    plt.close("all")

    _, _, NETVIS, RESULT = paths(results_paths[0])

    logger.debug(f"creating network vis using result file {results_paths[0]}")
    with open(results_paths[0], "rb") as f:
        res = dill.load(f, ignore=True)
    generate_network_vis(res, NETVIS)
    img_paths.append(NETVIS)

    report_name = (
        f"{results_paths[0].parent.name}&{results_paths[0].name.split('&')[0]}.png"
    )
    logger.debug(f"creating final image with name {report_name}...")

    result = merge_rows_files(
        img_paths,
        results_paths[0].parent / report_name,
        3 if len(results_paths) <= 5 else 4,
        cleanup,
    )
    return result
