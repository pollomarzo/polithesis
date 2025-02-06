import logging
from bisect import bisect_left
from collections import defaultdict
from contextlib import ExitStack
from itertools import batched
import math
from math import ceil
from pathlib import PurePath
from typing import Iterable, List

import brian2 as b2
from brian2 import Hz
import brian2hears as b2h
from brian2hears import erbspace
import dill
import graphviz
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from sorcery import dict_of

from analyze import sound_analysis as SA
from analyze.graph import generate_flow_chart
from cochleas.consts import CFMAX, CFMIN
from cochleas.GammatoneCochlea import run_hrtf
from utils.custom_sounds import Tone, ToneBurst
from utils.log import logger, tqdm

plt.rcParams["axes.grid"] = True
plt.rcParams["figure.figsize"] = (6, 3)

PLTWIDTH = 10


def take_closest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return (myList[0], 0)
    if pos == len(myList):
        return (myList[-1], len(myList))
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return (after, pos)
    else:
        return (before, pos - 1)


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
    "returns {neuron_id: num_spikes}.keys()"
    n2s = {id: 0 for id in x["global_ids"]}
    for sender in x["senders"]:
        n2s[sender] += 1
    return n2s.values()


def shift_senders(x, hist_logscale=False):
    "returns list of 'senders' with ids shifted to [0,num_neurons]. optionally ids are CFs"
    if hist_logscale:
        cf = b2h.erbspace(CFMIN, CFMAX, len(x["global_ids"])) / b2.Hz
        old2newid = {oldid: cf[i] for i, oldid in enumerate(x["global_ids"])}
    else:
        old2newid = {oldid: i for i, oldid in enumerate(x["global_ids"])}
    return [old2newid[i] for i in x["senders"]]


def draw_hist(
    ax,
    senders_renamed,
    angles,
    num_neurons,
    max_spikes_single_neuron,
    logscale=True,
    freq=None,
):
    """draws a low opacity horizontal histogram for each angle position

    includes a secondary y-axis, optionally logarithmic.
    if logscale, expects senders to be renamed to CFs
    if freq, include a horizontal line at corresponding frequency
    """
    max_histogram_height = 0.25
    bin_count = 50
    alpha = 0.5
    freqlinestyle = {
        "color": "black",
        "linestyle": ":",
        "label": "freq_in",
        "alpha": 0.4,
    }
    if logscale:
        bins = b2h.erbspace(CFMIN, CFMAX, bin_count) / b2.Hz

        for j, angle in enumerate(angles):
            left_data = senders_renamed["L"][j]
            right_data = senders_renamed["R"][j]

            left_hist, _ = np.histogram(left_data, bins=bins)
            right_hist, _ = np.histogram(right_data, bins=bins)
            max_value = max(max(left_hist), max(right_hist))
            left_hist_normalized = left_hist / (max_value * max_histogram_height)
            right_hist_normalized = right_hist / (max_value * max_histogram_height)

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
        if freq is not None:
            ax.axhline(y=freq / b2.Hz, **freqlinestyle)
        ax.set_ylabel("approx CF (Hz)")
    else:
        bins = np.linspace(0, num_neurons, bin_count)

        for j, angle in enumerate(angles):
            left_data = senders_renamed["L"][j]
            right_data = senders_renamed["R"][j]

            left_hist, _ = np.histogram(left_data, bins=bins)
            right_hist, _ = np.histogram(right_data, bins=bins)
            left_hist_normalized = (
                left_hist / max_spikes_single_neuron * max_histogram_height
            )
            right_hist_normalized = (
                right_hist / max_spikes_single_neuron * max_histogram_height
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

        if freq is not None:
            cf = b2h.erbspace(CFMIN, CFMAX, num_neurons)
            freq, neur_n = take_closest(cf, freq)
            ax.axhline(y=neur_n)
    ax.yaxis.set_minor_locator(plt.NullLocator())  # remove minor ticks

def draw_rate_vs_angle2(
    data,
    title,
    rate=True,
    hist_logscale=True,
    show_pops=["LSO"],
    ylim=None,
    show_hist=True,
):
    logger.debug(dict_of(title, show_pops, rate, hist_logscale))
    version = data["angle_to_rate"][0].get("version", None)
    angle_to_rate = data["angle_to_rate"]
    name = data["conf"]["model_desc"]["name"]
    sound_key = data["conf"]["sound_key"]
    duration = (
        data.get("simulation_time", data["basesound"].sound.duration / b2.ms) * b2.ms
    )
    logger.debug(f"simulation time={duration}")

    angles = list(angle_to_rate.keys())
    sides = ["L", "R"]

    with plt.ioff():
        fig, ax = plt.subplots(math.ceil(len(show_pops)/2),2, figsize=(20, 2*len(show_pops)))
    ax = list(flatten([ax]))

    for i, pop in tqdm(list(enumerate(show_pops)), desc="pop"):
        num_active = {
            side: [len(set(angle_to_rate[angle][side][pop])) for angle in angles]
            for side in sides
        }
        tot_spikes = {
            side: [
                len(angle_to_rate[angle][side][pop]["times"] / duration)
                for angle in angles
            ]
            for side in sides
        }
        active_neuron_rate = {
            side: [
                avg_fire_rate_actv_neurons(angle_to_rate[angle][side][pop])
                * (1 * b2.second)
                / duration
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
        plotted_rate = active_neuron_rate if rate else tot_spikes
        ax[i].plot(angles, plotted_rate["L"], 'o-', color = 'm')
        ax[i].set_title(pop)
        ax[i].plot(angles, plotted_rate["R"], 'o-', color = 'g')
        ax[i].set_ylabel("active neuron spikes/s [Hz]" if rate else "overall spikes/s")
        ax[i].set_ylim(ylim)
        ax[i].set_xticks(angles)
        ax[i].set_xticklabels([f"{j}°" for j in angle_to_rate.keys()])
        ax[i].spines['right'].set_visible(False)
        ax[i].spines['top'].set_visible(False)

        if show_hist:
            v = ax[i].twinx()
            v.grid(visible=False)  # or use linestyle='--'

            senders_renamed = {
                side: [
                    shift_senders(angle_to_rate[angle][side][pop], hist_logscale)
                    for angle in angles
                ]
                for side in sides
            }
            max_spikes_single_neuron = max(flatten(distr.values()))
            draw_hist(
                v,
                senders_renamed,
                angles,
                num_neurons=len(angle_to_rate[0]["L"][pop]["global_ids"]),
                max_spikes_single_neuron=max_spikes_single_neuron,
                logscale=hist_logscale,
            )
    # _ = ax[i].legend(loc="lower right")
    
    if len(show_pops) < 8:
        ax[len(show_pops)].axis('off')  # Turn off the 8th subplot (or any remaining one)

    plt.suptitle(title)
    #plt.setp([ax], xticks=angles)
    #[ax.set_xticklabels([f"{i}°" for i in angle_to_rate.keys()]) for ax in ax]

    plt.tight_layout()

    return fig

def draw_rate_vs_angle(
    data,
    title,
    rate=True,
    hist_logscale=True,
    show_pops=["parrot_ANF", "GBC", "SBC", "LNTBC", "MNTBC", "LSO", "MSO", "ICC"],
    ylim=None,
    show_hist=True,
    show_freq=False,
):
    logger.debug(dict_of(title, show_pops, rate, hist_logscale))
    version = data["angle_to_rate"][0].get("version", None)
    angle_to_rate = data["angle_to_rate"]
    name = data["conf"]["model_desc"]["name"]
    input = data["basesound"]
    sound_key = data["conf"]["sound_key"]
    duration = (
        data.get("simulation_time", data["basesound"].sound.duration / b2.ms) * b2.ms
    )
    logger.debug(f"simulation time={duration}")

    angles = list(angle_to_rate.keys())
    sides = ["L", "R"]

    with plt.ioff():
        fig, ax = plt.subplots(len(show_pops), figsize=(8, 2 * len(show_pops)))
    ax = list(flatten([ax]))

    for i, pop in tqdm(list(enumerate(show_pops)), desc="pop"):
        num_active = {
            side: [len(set(angle_to_rate[angle][side][pop])) for angle in angles]
            for side in sides
        }
        tot_spikes = {
            side: [
                len(angle_to_rate[angle][side][pop]["times"] / duration)
                for angle in angles
            ]
            for side in sides
        }
        active_neuron_rate = {
            side: [
                avg_fire_rate_actv_neurons(angle_to_rate[angle][side][pop])
                * (1 * b2.second)
                / duration
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
        plotted_rate = active_neuron_rate if rate else tot_spikes
        ax[i].plot(angles, plotted_rate["L"], label=f"left  {pop}")
        ax[i].plot(angles, plotted_rate["R"], label=f"right {pop}")
        ax[i].set_ylabel("actv neur spk/sec (Hz)" if rate else "total pop spks/sec")
        ax[i].set_ylim(ylim)

        if show_hist:
            v = ax[i].twinx()
            v.grid(visible=False)  # or use linestyle='--'
            if version > 2:  # needed for global ids
                senders_renamed = {
                    side: [
                        shift_senders(angle_to_rate[angle][side][pop], hist_logscale)
                        for angle in angles
                    ]
                    for side in sides
                }
                max_spikes_single_neuron = max(flatten(distr.values()))
                draw_hist(
                    v,
                    senders_renamed,
                    angles,
                    num_neurons=len(angle_to_rate[0]["L"][pop]["global_ids"]),
                    max_spikes_single_neuron=max_spikes_single_neuron,
                    logscale=hist_logscale,
                    freq=(
                        input.frequency
                        if (show_freq and (isinstance(input, Tone)))
                        else None
                    ),
                )
        _ = ax[i].legend(loc="lower right")

    plt.suptitle(title)
    plt.setp([ax], xticks=angles)
    [ax.set_xticklabels([f"{i}°" for i in angle_to_rate.keys()]) for ax in ax]

    plt.tight_layout()
    return fig


def draw_single_angle_histogram(data, angle, population="SBC", fontsize=16, alpha=0.8):
    """
    Draw horizontal histograms of spike distributions across frequencies for a single angle,
    with left population growing downward and right population growing upward from a central axis.

    Parameters:
    -----------
    data : dict
        The full dataset containing angle_to_rate information
    angle : float
        The specific angle to visualize
    population : str
        Name of the neural population to visualize
    fontsize : int
        Base fontsize for the plot. Other elements will scale relative to this.

    Returns:
    --------
    matplotlib.figure.Figure
        The generated figure
    """
    # Constants
    bin_count = 50

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 2.42))

    # Get data for this angle and population
    pop_data = {
        "L": data["angle_to_rate"][angle]["L"][population],
        "R": data["angle_to_rate"][angle]["R"][population],
    }

    # Create logarithmic bins for frequency
    bins = b2h.erbspace(CFMIN, CFMAX, bin_count) / b2.Hz

    # Process data for histograms
    senders_renamed = {
        side: shift_senders(pop_data[side], True)  # True for logscale
        for side in ["L", "R"]
    }

    # Create histograms
    left_hist, _ = np.histogram(senders_renamed["L"], bins=bins)
    right_hist, _ = np.histogram(senders_renamed["R"], bins=bins)

    # Normalize histograms
    max_value = max(max(left_hist), max(right_hist))
    if max_value > 0:  # Avoid division by zero
        left_hist = left_hist / max_value
        right_hist = right_hist / max_value

    # Plot histograms - note the negative values for left histogram
    ax.bar(
        bins[:-1],
        -left_hist,
        width=np.diff(bins),
        color="C0",
        alpha=alpha,
        label="Left",
        align="edge",
    )
    ax.bar(
        bins[:-1],
        right_hist,
        width=np.diff(bins),
        color="C1",
        alpha=alpha,
        label="Right",
        align="edge",
    )

    # Configure axes
    ax.set_xscale("log")
    ax.set_xlim(CFMIN, CFMAX)
    xticks = [20, 100, 500, 1000, 5000, 20000]
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{freq} Hz" for freq in xticks], fontsize=fontsize)

    # Set y-axis limits symmetrically around zero
    ylim = 1.1  # Slightly larger than 1 to give some padding
    ax.set_ylim(-ylim, ylim)
    ax.tick_params(axis="y", labelsize=fontsize)  # Set y-tick font size

    # Add horizontal line at y=0
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    # Set font sizes for labels and title
    ax.set_xlabel("Characteristic Frequency (Hz)", fontsize=fontsize)
    ax.set_ylabel("Normalized spikes", fontsize=fontsize)
    # ax.legend(fontsize=fontsize)

    # plt.title(
    #     f"{population} population response at {angle}° azimuth\n"
    #     f'Sound: {data["conf"]["sound_key"]}',
    #     fontsize=fontsize * 1.2,
    # )  # Title slightly larger

    plt.tight_layout()

    return fig


def synthetic_angle_to_itd(angle, w_head: int = 22, v_sound: int = 33000):
    delta_x = w_head * np.sin(np.deg2rad(angle))
    return round(1000 * delta_x / v_sound, 2)


def draw_ITD_ILD(data):
    previous_level = logger.level
    # itd and ild functions are VERY verbose
    tone: Tone = data["basesound"]
    angle_to_ild = {}
    angle_to_itd = {}
    angles = list(data["angle_to_rate"].keys())
    coc = data["conf"]["cochlea_type"]
    angle_to_hrtfed_sound = data.get("angle_to_hrtfed_sound", None)
    if coc != "ppg":
        logger.debug(
            f"used cochlea {coc}, with parameters {
                data["conf"]["parameters"]["cochlea"][coc]["hrtf_params"]
            }"
        )
        for angle in angles:
            if angle_to_hrtfed_sound is None:
                logger.info(
                    "old result file, does not include HRTFed sounds. Generating (beware of possible differences)..."
                )
                binaural_sound = run_hrtf(
                    tone,
                    angle,
                    data["conf"]["parameters"]["cochlea"][coc]["hrtf_params"],
                )
                left = binaural_sound.left
                right = binaural_sound.right
            else:
                left, right = (
                    angle_to_hrtfed_sound[angle]["left"],
                    angle_to_hrtfed_sound[angle]["right"],
                )
            logger.setLevel(logging.WARNING)
            angle_to_itd[angle] = SA.itd(left, right)
            ild_res, all_freq_diff = SA.ild(left, right, tone.sound)
            logger.setLevel(logging.DEBUG)
            angle_to_ild[angle] = ild_res

            # total_diff = np.sum(all_freq_diff)
    else:
        angle_to_itd = {angle: synthetic_angle_to_itd(angle) for angle in angles}
        angle_to_ild = {angle: 0 for angle in angles}

    fig, ild = plt.subplots(1, sharex=True, figsize=(PLTWIDTH, 2.3))
    fig.suptitle(
        f"diff = RMS(left)-RMS(right), freq={tone.frequency}"
        # f"diff = max(|spectrum(left)|)-max(|spectrum(right)|), freq={tone.frequency}"
    )

    ild.set_ylabel("Level diff (dB)", color="r")
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


def generate_single_result(
    result_filepath: PurePath,
    cleanup=True,
    title=None,
    include_rate_vs_angle=True,
    include_itd_ild=True,
):
    with open(result_filepath, "rb") as f:
        res = dill.load(f, ignore=True)
    RATE_VS_ANGLE, ILD_ITD, NETVIS, RESULT = paths(result_filepath)
    if title is not None:
        RESULT.name = title

    fig = draw_rate_vs_angle(res, result_filepath.name)
    fig.savefig(RATE_VS_ANGLE)

    itd_ild_fig = draw_ITD_ILD(res)
    itd_ild_fig.savefig(ILD_ITD)

    generate_network_vis(res, NETVIS)

    return merge_rows_files([RATE_VS_ANGLE, ILD_ITD, NETVIS], RESULT, 1, cleanup)


import matplotlib


def generate_multi_inputs_single_net(
    results_paths: List[PurePath],
    cleanup=True,
    rate=True,  # plot whole population (False) or active neurons (True)
    include_netvis=True,
    show_pops=["parrot_ANF", "GBC", "SBC", "LNTBC", "MNTBC", "LSO", "MSO", "ICC"],
):
    font = {"size": 13}
    matplotlib.rc("font", **font)
    logger.debug(
        f"generating report for {results_paths}, with cleanup={cleanup} and rate={rate}"
    )
    img_paths = []
    for path in tqdm(results_paths, desc="single imgs"):
        filename = path.name
        logger.debug(f"now working on result file {path}")
        with open(path, "rb") as f:
            res = dill.load(f, ignore=True)
        RATE_VS_ANGLE, ILD_ITD, NETVIS, RESULT = paths(path)
        fig = draw_rate_vs_angle(
            res,
            # f"Tan Carney periph, tone at {res['basesound'].frequency}, HRTF{hrtf_params['subj_number']}{'ILDonly' if hrtf_params['ild_only'] else ""}",
            filename,
            rate=rate,
            hist_logscale=True,
            show_pops=show_pops,
        )
        fig.savefig(RATE_VS_ANGLE)
        itd_ild_fig = draw_ITD_ILD(res)
        itd_ild_fig.savefig(ILD_ITD)
        merge_rows_files(
            [RATE_VS_ANGLE, ILD_ITD], RESULT, img_per_row=1, cleanup=cleanup
        )
        img_paths.append(RESULT)
    plt.close("all")

    _, _, NETVIS, RESULT = paths(results_paths[0])

    if include_netvis:
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
        4 if len(results_paths) <= 6 else 4,
        cleanup,
    )
    return result

def take_closest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return (myList[0], 0)
    if pos == len(myList):
        return (myList[-1], len(myList))
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return (after, pos)
    else:
        return (before, pos - 1)


def get_spike_phases(spike_times: np.ndarray, frequency: float) -> np.ndarray:
    times_sec = spike_times
    return 2 * np.pi * frequency * (times_sec % (1 / frequency))


def calculate_vector_strength(spike_times: np.ndarray, frequency: float) -> float:
    if len(spike_times) == 0:
        return 0
    phases = get_spike_phases(spike_times, frequency)
    x = np.mean(np.cos(phases))
    y = np.mean(np.sin(phases))
    return np.sqrt(x**2 + y**2)
    
def range_around_center(center, radius, min_val=0, max_val=np.iinfo(np.int64).max):
    start = max(min_val, center - radius)
    end = min(max_val + 1, center + radius + 1)
    return np.arange(start, end)

def calculate_vector_strength_from_result(
        # result file (loaded)
        res,
        angle,
        side,
        pop,
        freq = None, # if None: freq = res['basesound'].frequency
        cf_target = None,
        bandwidth=0,
        n_bins = 7,
        display=False # if True also return fig, show() in caller function
        ):
    
    spikes = res["angle_to_rate"][angle][side][pop]
    sender2times = defaultdict(list)
    for sender, time in zip(spikes["senders"], spikes["times"]):
        sender2times[sender].append(time)
    sender2times = {k: np.array(v) / 1000 for k, v in sender2times.items()}
    num_neurons = len(spikes["global_ids"])
    cf = erbspace(CFMIN, CFMAX, num_neurons)

    if(freq == None):
        if(type(res['basesound'])  in (Tone,ToneBurst)):
            freq = res['basesound'].frequency
        else:
            logger.error("Frequency needs to be specified for non-Tone sounds")
    else:
        freq = freq * Hz

    if(cf_target == None):    
        cf_neuron, center_neuron_for_freq = take_closest(cf, freq)
    else:
        cf_neuron, center_neuron_for_freq = take_closest(cf, cf_target *Hz)

    old2newid = {oldid: i for i, oldid in enumerate(spikes["global_ids"])}
    new2oldid = {v: k for k, v in old2newid.items()}

    relevant_neurons = range_around_center(
        center_neuron_for_freq, radius=bandwidth, max_val=num_neurons - 1
    )
    relevant_neurons_ids = [new2oldid[i] for i in relevant_neurons]

    spike_times_list = [sender2times[i] for i in relevant_neurons_ids]  
    spike_times_array = np.concatenate(spike_times_list)  # Flatten into a single array

    phases = get_spike_phases(
        spike_times= spike_times_array, frequency=freq / Hz
    )
    vs = calculate_vector_strength(
        spike_times=spike_times_array, frequency=freq / Hz
    )


    if not display:
        return (vs, None)
    
    # plot phases
    bins = np.linspace(0, 2 * np.pi, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    fig, ax = plt.subplots(1, 1, figsize=(10,5))
    hist1, _ = np.histogram(phases, bins=bins)
    ax.bar(bin_centers, hist1, width=2 * np.pi / n_bins, alpha=0.7)
    if(bandwidth == 0):
        ax.set_title(
            f"Neuron {relevant_neurons_ids[0]} (CF: {cf_neuron:.1f} Hz)\nVS={vs:.3f}"
        )
    else:
        ax.set_title(
            f"Neurons {relevant_neurons_ids[0]} : {relevant_neurons_ids[-1]} (center CF: {cf_neuron:.1f} Hz)\nVS={vs:.3f}"
        )
    ax.set_xlabel("Phase (radians)")
    ax.set_ylabel("Spike Count")
    fig.show()

    return (fig,vs)