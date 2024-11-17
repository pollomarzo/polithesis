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


def sigmoid(x: np.ndarray, L: float, k: float, x0: float, b: float) -> np.ndarray:
    """
    General sigmoid function: f(x) = L/(1 + exp(-k*(x-x0))) + b

    Parameters:
    - L: maximum value
    - k: steepness
    - x0: midpoint (x value at sigmoid's center)
    - b: minimum value
    """
    return L / (1 + np.exp(-k * (x - x0))) + b


def find_zero_crossing(params):
    """
    Find where the sigmoid crosses zero given parameters [L, k, x0, b].
    Returns None if mathematically impossible (no zero crossing).
    """
    L, k, x0, b = params
    try:
        if k != 0 and b != 0:  # Avoid division by zero
            return x0 - (1 / k) * np.log(-L / b - 1)
        return None
    except (
        ValueError,
        RuntimeError,
    ):  # For cases where log arg is negative or other math errors
        return None


def analyze_population_differential(angle_to_rate: Dict, pop: str) -> Dict:
    """
    Analyze response by fitting sigmoid to the difference between L and R spike counts.

    Parameters:
    - angle_to_rate: Dictionary mapping angles to spike data
    - pop: Population to analyze ('LSO' or 'ICC')

    Returns:
    - Dictionary containing differential analysis results
    """
    angles = np.array(sorted([int(angle) for angle in angle_to_rate.keys()]))

    # Calculate spike count differences between L and R
    spike_diffs = []
    for angle in angles:
        l_spikes = len(angle_to_rate[angle]["L"][pop]["times"])
        r_spikes = len(angle_to_rate[angle]["R"][pop]["times"])
        spike_diffs.append(l_spikes - r_spikes)

    try:
        # Initial parameter guess
        p0 = [max(spike_diffs) - min(spike_diffs), 0.1, 0.0, np.mean(spike_diffs)]

        # Fit sigmoid
        params, _ = curve_fit(sigmoid, angles, spike_diffs, p0=p0)

        # Calculate predicted values for R-squared
        y_pred = sigmoid(angles, *params)
        ss_res = np.sum((np.array(spike_diffs) - y_pred) ** 2)
        ss_tot = np.sum((np.array(spike_diffs) - np.mean(spike_diffs)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        zero_crossing = find_zero_crossing(params)

        return {
            "raw_data": spike_diffs,
            "sigmoid_params": {
                "L": params[0],
                "k": params[1],
                "x0": params[2],
                "b": params[3],
            },
            "metrics": {
                "steepness": abs(params[1]),
                "range": params[0],
                "center": params[2],
                "r_squared": r_squared,
                "zero_crossing": zero_crossing,
            },
        }
    except RuntimeError as e:
        return {"error": f"Failed to fit sigmoid: {str(e)}"}


def compare_populations(results_dir: Path) -> Dict:
    """
    Compare LSO and ICC responses across frequencies, accounting for contralateral projections.

    Returns:
    - Dictionary containing comparisons for each frequency
    """
    results = [i for i in results_dir.glob("*.pic")]
    population_comparison = {}

    for result_path in results:
        with open(result_path, "rb") as f:
            res = dill.load(f)

        # Extract frequency from the base sound
        basesound = res["basesound"]
        if not isinstance(basesound, Tone):
            print(f"Skipping non-tone sound in {result_path}")
            continue

        freq = basesound.frequency / b2.Hz

        # Analyze both populations
        lso_analysis = analyze_population_differential(res["angle_to_rate"], "LSO")
        icc_analysis = analyze_population_differential(res["angle_to_rate"], "ICC")

        if "error" in lso_analysis or "error" in icc_analysis:
            print(f"Skipping frequency {freq}Hz due to fitting errors")
            continue

        # Compare metrics, considering contralateral projection
        metric_comparison = {}

        for metric in ["steepness", "r_squared", "range"]:
            lso_value = lso_analysis["metrics"][metric]
            if metric == "range":
                lso_value = -lso_value
            icc_value = icc_analysis["metrics"][metric]
            improvement = (
                ((icc_value - lso_value) / abs(lso_value)) * 100
                if lso_value != 0
                else float("inf")
            )

            metric_comparison[metric] = {
                "LSO": lso_value,
                "ICC": icc_value,
                "difference": icc_value - lso_value,
                "improvement_%": improvement,
            }

        metric_comparison[metric] = {
            "LSO": lso_value,
            "ICC": icc_value,
            "difference": icc_value - lso_value,
            "improvement_%": improvement,
        }

        # For zero crossing, compare absolute distances from 0°
        if (
            lso_analysis["metrics"]["zero_crossing"] is not None
            and icc_analysis["metrics"]["zero_crossing"] is not None
        ):
            lso_zc = abs(lso_analysis["metrics"]["zero_crossing"])
            icc_zc = abs(icc_analysis["metrics"]["zero_crossing"])
            improvement = (
                ((lso_zc - icc_zc) / lso_zc) * 100 if lso_zc != 0 else float("inf")
            )

            metric_comparison["zero_crossing_accuracy"] = {
                "LSO": lso_zc,
                "ICC": icc_zc,
                "difference": lso_zc - icc_zc,
                "improvement_%": improvement,
            }

        population_comparison[freq] = metric_comparison

    return population_comparison


def print_population_comparison(comparison: Dict):
    """Print a formatted comparison of LSO and ICC metrics across frequencies."""
    print("\nPopulation Comparison Analysis")
    print("=" * 80)

    # Get all metrics to compare
    metrics = list(next(iter(comparison.values())).keys())

    # First, print a summary for each metric
    for metric in metrics:
        print(f"\n{metric.upper()}")
        print("-" * 80)
        print(
            f"{'Frequency':>10} | {'LSO':>10} | {'ICC':>10} | {'Diff':>10} | {'Improvement':>10}"
        )
        print("-" * 80)

        # Calculate average improvement
        improvements = []

        for freq in sorted(comparison.keys()):
            metric_data = comparison[freq][metric]
            improvements.append(metric_data["improvement_%"])

            print(
                f"{freq:>10.0f} | {metric_data['LSO']:>10.3f} | {metric_data['ICC']:>10.3f} | "
                f"{metric_data['difference']:>10.3f} | {metric_data['improvement_%']:>10.1f}%"
            )

        avg_improvement = np.mean(improvements)
        print("-" * 80)
        print(
            f"{'Average':>10} | {' ':>10} | {' ':>10} | {' ':>10} | {avg_improvement:>10.1f}%"
        )

    print(
        "\nNote: Positive improvement percentages indicate ICC performs better than LSO"
    )
    print("      For zero_crossing_accuracy, smaller values are better")
    print(
        "      LSO values for steepness and range are inverted due to contralateral projection"
    )


if __name__ == "__main__":

    import dill

    import consts as C

    results_dir = (
        Path(C.Paths.RESULTS_DIR).absolute()
        / "v_shaped_diff_ICC"
        / "withICC&TanCarney&hrtf1"
    )

    # Compare populations and print results
    comparison = compare_populations(results_dir)
    print_population_comparison(comparison)
