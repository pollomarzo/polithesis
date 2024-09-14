import logging
from contextlib import ExitStack
from itertools import batched
from math import ceil
from pathlib import PurePath
from typing import List

import dill
import graphviz
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from analyze import sound_analysis as SA
from analyze.graph import generate_flow_chart
from cochleas.RealisticCochlea import run_hrtf
from utils.custom_sounds import Tone
from utils.log import logger

plt.rcParams["axes.grid"] = True
plt.rcParams["figure.figsize"] = (6, 3)

PLTWIDTH = 8


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


def draw_rate_vs_angle(data, filename, show_lso=True, show_mso=True, rate=True):
    angle_to_rate = data["angle_to_rate"]
    name = data["conf"]["model_desc"]["name"]
    sound_key = data["conf"]["sound_key"]
    # cochlea = data["conf"]["cochlea_type"]

    angles = list(angle_to_rate.keys())

    def average_firing_rate(x):
        active_neurons = set(x["senders"] if rate else x)
        return (len(x["times"]) / len(active_neurons)) if len(active_neurons) > 0 else 0

    arr_n_spikes_r_lso = [
        average_firing_rate(x["R"]["LSO"]) for angle, x in angle_to_rate.items()
    ]
    arr_n_spikes_l_lso = [
        average_firing_rate(x["L"]["LSO"]) for angle, x in angle_to_rate.items()
    ]
    arr_n_spikes_r_mso = [
        average_firing_rate(x["R"]["MSO"]) for angle, x in angle_to_rate.items()
    ]
    arr_n_spikes_l_mso = [
        average_firing_rate(x["L"]["MSO"]) for angle, x in angle_to_rate.items()
    ]

    lso = {
        "spikes": [arr_n_spikes_r_lso, arr_n_spikes_l_lso],
        "show": show_lso,
        "label": "lso",
    }
    mso = {
        "spikes": [arr_n_spikes_r_mso, arr_n_spikes_l_mso],
        "show": show_mso,
        "label": "mso",
    }
    data = []
    for i in [lso, mso]:
        if i["show"]:
            data.append(i)
    num_subplots = len(data)
    fig, ax = plt.subplots(num_subplots, figsize=(PLTWIDTH, 2 * num_subplots))
    if type(ax) is not np.ndarray:
        ax = [ax]
    for axis, d in zip(ax, data):
        axis.plot(angles, d["spikes"][0], ".-", label=f"right {d["label"]}")
        axis.plot(angles, d["spikes"][1], ".-", label=f"left {d["label"]}")
        axis.set_ylabel("actv neur spk/sec (Hz)" if rate else "total pop spk/sec")
        _ = axis.legend()
    # fig.suptitle(f"{name} with {sound_key}")
    plt.suptitle(filename)
    plt.setp([ax], xticks=angles)

    plt.tight_layout()
    return fig


def draw_ITD_ILD(data, selected):
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
            data["conf"]["parameters"]["cochlea"]["realistic"]["subj_number"],
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

    itd_ild_fig = draw_ITD_ILD(res, result_filepath.name)
    itd_ild_fig.savefig(ILD_ITD)

    generate_network_vis(res, NETVIS)

    merge_rows_files([RATE_VS_ANGLE, ILD_ITD, NETVIS], RESULT, 1, cleanup)
    return 1


from utils.log import tqdm


def generate_multi_inputs_single_net(results_paths: List[PurePath], cleanup=True):
    img_paths = []
    for path in tqdm(results_paths, desc="single imgs"):
        filename = path.name
        logger.debug(f"now working on result file {path}")
        with open(path, "rb") as f:
            res = dill.load(f, ignore=True)
        RATE_VS_ANGLE, ILD_ITD, NETVIS, RESULT = paths(path)
        fig = draw_rate_vs_angle(res, filename, True, True, True)
        fig.savefig(RATE_VS_ANGLE)
        itd_ild_fig = draw_ITD_ILD(res, filename)
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
