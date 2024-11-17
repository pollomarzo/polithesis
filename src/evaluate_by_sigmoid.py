"generated with help with claude AI"

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

POP = "LSO"


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


def analyze_icc_differential(angle_to_rate: Dict) -> Dict:
    """
    Analyze ICC response by fitting sigmoid to the difference between L and R spike counts.

    Parameters:
    - angle_to_rate: Dictionary mapping angles to spike data

    Returns:
    - Dictionary containing differential analysis results
    """
    angles = np.array(sorted([int(angle) for angle in angle_to_rate.keys()]))

    # Calculate spike count differences between L and R
    spike_diffs = []
    for angle in angles:
        l_spikes = len(angle_to_rate[angle]["L"][POP]["times"])
        r_spikes = len(angle_to_rate[angle]["R"][POP]["times"])
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

        # Zero crossing point (where L-R difference = 0)
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


def plot_frequency_subplots(
    all_results: List[tuple], angles: np.ndarray, save_path: str = None
):
    """
    Create a figure with subplots for each frequency showing ICC differential responses.

    Parameters:
    - all_results: List of tuples (frequency, analysis_results)
    - angles: Array of angles used
    - save_path: Optional path to save the figure
    """
    # Calculate number of rows and columns for subplots
    n_freqs = len(all_results)
    n_cols = min(3, n_freqs)  # Maximum 3 columns
    n_rows = (n_freqs + n_cols - 1) // n_cols  # Ceiling division

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    fig.suptitle(f"{POP} L-R Spike Count Difference vs Sound Angle")

    # Flatten axes array for easier iteration if needed
    if n_rows == 1 and n_cols == 1:
        axes = np.array([axes])
    axes_flat = axes.flatten()

    # Create smooth x values for sigmoid plotting
    x_smooth = np.linspace(min(angles), max(angles), 100)

    # Sort results by frequency
    all_results.sort(key=lambda x: x[0])

    # Plot each frequency in its subplot
    for idx, (freq, results) in enumerate(all_results):
        ax = axes_flat[idx]

        if "error" in results:
            ax.text(
                0.5,
                0.5,
                f'Fitting error:\n{results["error"]}',
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            continue

        # Plot raw data points
        ax.plot(angles, results["raw_data"], "bo", alpha=0.6, label="Raw Data")

        # Plot fitted sigmoid
        params = [results["sigmoid_params"][p] for p in ["L", "k", "x0", "b"]]
        y_smooth = sigmoid(x_smooth, *params)
        ax.plot(x_smooth, y_smooth, "r-", label="Fitted Sigmoid")

        # Add reference lines
        ax.axhline(y=0, color="k", linestyle="--", alpha=0.3)
        ax.axvline(x=0, color="k", linestyle="--", alpha=0.3)

        # Add metrics text
        metrics = results["metrics"]
        ax.text(
            0.05,
            0.95,
            f'Steepness: {metrics["steepness"]:.3f}\n'
            f'Range: {metrics["range"]:.1f}\n'
            f'Zero cross.: {metrics["zero_crossing"]:.1f}°\n'
            f'R²: {metrics["r_squared"]:.3f}',
            transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        ax.set_title(f"Frequency: {freq}")
        ax.set_xlabel("Angle (degrees)")
        ax.set_ylabel("L-R Spike Count Difference")
        ax.set_xticks(angles)
        ax.grid(True, alpha=0.3)
        ax.legend()

    # Remove empty subplots if any
    for idx in range(len(all_results), len(axes_flat)):
        fig.delaxes(axes_flat[idx])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
    plt.show()


# Example usage in main:
if __name__ == "__main__":
    from pathlib import Path

    import dill

    results_dir = (
        Path(C.Paths.RESULTS_DIR).absolute()
        / "v_shaped_diff_ICC"
        / "withICC&TanCarney&hrtf1"
    )
    results = [i for i in results_dir.glob("*.pic")]

    # Group results by frequency
    freq_results = []

    for result_path in results:
        with open(result_path, "rb") as f:
            res = dill.load(f)

        # Extract frequency from the base sound
        basesound = res["basesound"]
        if isinstance(basesound, Tone):
            freq = basesound.frequency
        else:
            print(f"Skipping non-tone sound in {result_path}")
            continue

        # Analyze differential response
        analysis = analyze_icc_differential(res["angle_to_rate"])
        freq_results.append((freq, analysis))

    # Plot all frequencies in subplots
    plot_frequency_subplots(freq_results, ANGLES)
