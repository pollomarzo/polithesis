import math
import os
import pprint
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum, auto
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import brian2 as b2
import brian2hears as b2h
import dill
import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
import scipy as scp
from IPython.display import display
from scipy.optimize import curve_fit
from sorcery import dict_of

import consts as C
from cochleas.anf_utils import CheckThreshold, create_sound_key
from cochleas.consts import ANGLES, CFMAX, CFMIN, NUM_CF
from cochleas.GammatoneCochlea import run_hrtf
from generate_results import CURRENT_TEST
from utils.custom_sounds import Tone

RES_PER_ROW = 2


def plot_icc_diff_by_result(results):
    lenr = len(results.keys())
    n_rows = math.ceil(lenr / RES_PER_ROW)
    fig = plt.figure(figsize=(4 * RES_PER_ROW, 2.5 * n_rows))
    for i, (folder, r) in enumerate(results.items()):
        ax = fig.add_subplot(n_rows, RES_PER_ROW, i + 1)
        for label, values in r.items():
            ax.plot(ANGLES, values, ".-", label=label)
        ax.set_title(folder)
        ax.set_xticks(ANGLES)
        ax.set_ylabel("total pop spike")
        ax.set_xlabel("angles")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right")
    fig.tight_layout()
    plt.show()


def plot_icc_diff_by_input(results):
    "assumes inputs are the same in all results"
    input_to_result = defaultdict(lambda: defaultdict(dict))
    for param_name, r in results.items():
        for sound_key, values in r.items():
            input_to_result[sound_key][param_name] = values

    lenr = len(input_to_result.keys())
    n_rows = math.ceil(lenr / RES_PER_ROW)
    fig = plt.figure(figsize=(4 * RES_PER_ROW, 2.5 * n_rows))
    fig.suptitle("Difference in IC spikes depending on noise")
    for i, (sound_key, r) in enumerate(input_to_result.items()):
        ax = fig.add_subplot(n_rows, RES_PER_ROW, i + 1)
        for label, values in r.items():
            ax.plot(ANGLES, values, ".-", label=label)
        ax.set_title(sound_key)
        ax.set_xticks(ANGLES)
        ax.set_ylabel("total spike number")
        ax.set_xlabel("angles")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right")
    fig.tight_layout()
    plt.show()


tot_spikes = lambda d, side, pop: len(d[side][pop]["times"])


def rework_result(i, extract_pop="ICC"):
    # label = create_sound_key(i["basesound"])
    label = f"tone at {i['basesound'].frequency}"
    a2r = i["angle_to_rate"]
    iccdiff = [
        tot_spikes(pops, "L", extract_pop) - tot_spikes(pops, "R", extract_pop)
        for angle, pops in a2r.items()
    ]
    return label, iccdiff


if __name__ == "__main__":
    import dill

    from consts import Paths
    from utils.log import tqdm

    test_dir = Path(Paths.RESULTS_DIR).absolute() / "v_shaped_diff_ICC" / "noise_check"
    results_parsed = defaultdict(dict)
    for results_dir in tqdm([i for i in test_dir.iterdir()], desc="fldr: "):
        results = [i for i in results_dir.glob("*.pic")]
        for i in results:
            with open(i, "rb") as f:
                res = dill.load(f, ignore=False)
                label, iccdiff = rework_result(res)
                del res
            results_parsed[results_dir.name][label] = iccdiff
    plot_icc_diff_by_input(results_parsed)
    # plot_icc_diff_by_result(results_parsed)
