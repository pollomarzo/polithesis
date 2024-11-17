"generated with help with claude AI"

import logging
import os
import pprint
from abc import ABC, abstractmethod
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sorcery import dict_of

import consts as C
from analyze import sound_analysis as SA
from cochleas.anf_utils import CheckThreshold
from cochleas.consts import ANGLES, CFMAX, CFMIN, NUM_CF
from cochleas.GammatoneCochlea import run_hrtf
from generate_results import CURRENT_TEST
from utils.custom_sounds import Tone
from utils.log import logger


class METRIC(StrEnum):
    SPIKE_COUNTS = auto()
    SPIKE_RATES = auto()
    ICC_COUNTS = auto()


@dataclass
class ActivityMetrics:
    """Stores activity metrics for a single simulation"""

    angle: float
    left_activity: float
    right_activity: float

    @property
    def activity_difference(self) -> float:
        return self.right_activity - self.left_activity


class AnglePredictor:

    def __init__(self, metric_type=METRIC.SPIKE_COUNTS, angle_tolerance=15.0):
        """
        Args:
            metric_type: Either 'spike_count' or 'firing_rate'
            angle_tolerance: Acceptable error in degrees for "soft" accuracy
        """
        self.metric_type = metric_type
        self.angle_tolerance = angle_tolerance
        self.model = None
        self.scaler = StandardScaler()

    def prepare_data(self, results_list: List[Dict]) -> List[ActivityMetrics]:
        """
        Process raw results into ActivityMetrics objects
        Args:
            results_list: List of simulation results, each containing angle and spike data
        Returns:
            List of ActivityMetrics objects
        """
        metrics_list = []

        for result in results_list:
            sim_time = result["simulation_time"]
            for angle in result["angle_to_rate"].keys():
                l_lso_spikes = len(result["angle_to_rate"][angle]["L"]["LSO"]["times"])
                r_lso_spikes = len(result["angle_to_rate"][angle]["R"]["LSO"]["times"])
                l_mso_spikes = len(result["angle_to_rate"][angle]["L"]["MSO"]["times"])
                r_mso_spikes = len(result["angle_to_rate"][angle]["R"]["MSO"]["times"])

                if self.metric_type == METRIC.SPIKE_COUNTS:
                    l_activity = l_lso_spikes + l_mso_spikes
                    r_activity = r_lso_spikes + r_mso_spikes
                elif self.metric_type == METRIC.SPIKE_RATES:  # firing_rate
                    # todo: this is without active_neurons
                    l_activity = (l_lso_spikes + l_mso_spikes) / (sim_time / 1000)
                    r_activity = (r_lso_spikes + r_mso_spikes) / (sim_time / 1000)
                elif self.metric_type == METRIC.ICC_COUNTS:
                    l_activity = len(
                        result["angle_to_rate"][angle]["L"]["ICC"]["times"]
                    )
                    r_activity = len(
                        result["angle_to_rate"][angle]["R"]["ICC"]["times"]
                    )
                else:
                    raise Exception("unknown metric")

                metrics_list.append(
                    ActivityMetrics(
                        angle=angle,
                        left_activity=l_activity,
                        right_activity=r_activity,
                    )
                )

        return metrics_list

    def prepare_training_data(
        self, metrics_list: List[ActivityMetrics]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert ActivityMetrics list to X, y arrays for training"""
        X = np.array([m.activity_difference for m in metrics_list]).reshape(-1, 1)
        y = np.array([m.angle for m in metrics_list])
        X = self.scaler.fit_transform(X)
        return X, y

    def train(self, X: np.ndarray, y: np.ndarray, model_type: str = "logistic"):
        """Train the selected model with probability support"""
        if model_type == "logistic":
            self.model = LogisticRegression()
        elif model_type == "svm":
            # Note: Using probability=True for SVM to get prediction probabilities
            self.model = SVC(kernel="rbf", probability=True)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        self.model.fit(X, y)

    def predict_with_probability(
        self, activity_difference: float
    ) -> Tuple[float, np.ndarray]:
        """Predict angle with probability distribution"""
        if self.model is None:
            raise ValueError("Model not trained yet")

        X = self.scaler.transform([[activity_difference]])
        angle = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]

        return angle, probabilities

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        if self.model is None:
            raise ValueError("Model not trained yet")

        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        # Basic metrics
        accuracy = accuracy_score(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred)

        # Soft accuracy (predictions within tolerance)
        angle_differences = np.abs(y_test - y_pred)
        soft_accuracy = np.mean(angle_differences <= self.angle_tolerance)

        # Mean absolute error
        mae = np.mean(angle_differences)

        # Confidence analysis
        max_probabilities = np.max(y_pred_proba, axis=1)
        mean_confidence = np.mean(max_probabilities)

        # Analyze prediction spread
        angle_errors = []
        spread_by_angle = {}

        for true_angle in np.unique(y_test):
            mask = y_test == true_angle
            if np.any(mask):
                errors = np.abs(y_test[mask] - y_pred[mask])
                spread_by_angle[true_angle] = {
                    "mean_error": np.mean(errors),
                    "std_error": np.std(errors),
                    "confidence": np.mean(max_probabilities[mask]),
                }

        return {
            "accuracy": accuracy,
            "soft_accuracy": soft_accuracy,
            "mae": mae,
            "mean_confidence": mean_confidence,
            "confusion_matrix": conf_matrix,
            "angle_analysis": spread_by_angle,
        }

    def plot_inputs(self, metrics: List[ActivityMetrics]) -> plt.Figure:
        plt.plot(ANGLES, [i.activity_difference for i in metrics])
        plt.xlabel("angles")
        plt.ylabel(f"activity difference {self.metric_type.name}")
        plt.show(block=False)
        # plt.pause(0.001)


def analyze_prediction_quality(
    predictor: AnglePredictor, metrics_list: List[ActivityMetrics]
) -> Dict:
    """Analyze where the model performs well/poorly"""

    results = []
    for metric in metrics_list:
        pred_angle, probabilities = predictor.predict_with_probability(
            metric.activity_difference
        )
        max_prob = np.max(probabilities)

        results.append(
            {
                "true_angle": metric.angle,
                "predicted_angle": pred_angle,
                "confidence": max_prob,
                "error": abs(metric.angle - pred_angle),
                "activity_diff": metric.activity_difference,
            }
        )

    # Convert to numpy for analysis
    results_arr = np.array(
        [(r["true_angle"], r["error"], r["confidence"]) for r in results]
    )

    # Analyze performance by angle regions
    angle_regions = {
        "center": lambda x: abs(x) <= 30,
        "intermediate": lambda x: 30 < abs(x) <= 60,
        "peripheral": lambda x: abs(x) > 60,
    }

    region_analysis = {}
    for region, condition in angle_regions.items():
        mask = [condition(i) for i in results_arr[:, 0]]
        if np.any(mask):
            region_analysis[region] = {
                "mean_error": np.mean(results_arr[mask, 1]),
                "mean_confidence": np.mean(results_arr[mask, 2]),
                "samples": np.sum(mask),
            }

    return {"detailed_predictions": results, "region_analysis": region_analysis}


from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def plot_decision_boundaries(
    predictor: AnglePredictor, metrics: List[ActivityMetrics], title: str = None
):
    """
    Visualize model decision boundaries and data points

    Args:
        predictor: Trained AnglePredictor instance
        metrics: List of ActivityMetrics used for training
        title: Optional plot title
    """
    # Prepare data
    differences = np.array([m.activity_difference for m in metrics])
    angles = np.array([m.angle for m in metrics])

    # Create a range of activity differences for prediction
    x_min, x_max = differences.min() - 0.1 * (
        differences.max() - differences.min()
    ), differences.max() + 0.1 * (differences.max() - differences.min())
    x_test = np.linspace(x_min, x_max, 300).reshape(-1, 1)

    # Scale the test data
    x_test_scaled = predictor.scaler.transform(x_test)

    # Get predictions and probabilities
    predictions = predictor.model.predict(x_test_scaled)
    probabilities = predictor.model.predict_proba(x_test_scaled)

    # Create the main plot
    plt.figure(figsize=(12, 8))

    # Plot data points
    scatter = plt.scatter(
        differences,
        angles,
        c=angles,
        cmap="viridis",
        s=100,
        alpha=0.6,
        label="Training Data",
    )
    plt.colorbar(scatter, label="Angle (degrees)")

    # Plot predicted angles
    plt.plot(x_test, predictions, "r-", label="Model Predictions", alpha=0.7)

    # Add confidence bands if using probability predictions
    angles_unique = np.sort(np.unique(angles))
    max_probs = np.max(probabilities, axis=1)

    # Plot confidence bands
    plt.fill_between(
        x_test.flatten(),
        predictions - (1 - max_probs) * 90,  # Scale by max angle
        predictions + (1 - max_probs) * 90,
        alpha=0.2,
        color="red",
        label="Prediction Uncertainty",
    )

    # Add vertical lines at decision boundaries
    if isinstance(predictor.model, LogisticRegression):
        # For logistic regression, we can compute exact boundaries
        w = predictor.model.coef_
        b = predictor.model.intercept_
        for i in range(len(angles_unique) - 1):
            boundary = -(b[i] - b[i + 1]) / (w[i] - w[i + 1])
            boundary = predictor.scaler.inverse_transform([[boundary]])[0][0]
            plt.axvline(x=boundary, color="gray", linestyle="--", alpha=0.3)

    plt.xlabel("Activity Difference (R-L)")
    plt.ylabel("Angle (degrees)")
    plt.title(title or f"Decision Boundaries - {predictor.model.__class__.__name__}")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Add text box with performance metrics
    X = predictor.scaler.transform(differences.reshape(-1, 1))
    y_pred = predictor.model.predict(X)
    acc = np.mean(np.abs(y_pred - angles) <= predictor.angle_tolerance)
    mae = np.mean(np.abs(y_pred - angles))

    plt.text(
        0.02,
        0.98,
        f"Soft Accuracy (±{predictor.angle_tolerance}°): {acc:.2f}\n"
        f"Mean Absolute Error: {mae:.1f}°",
        transform=plt.gca().transAxes,
        bbox=dict(facecolor="white", alpha=0.8),
        verticalalignment="top",
    )


def plot_response_curves(predictor: AnglePredictor, metrics: List[ActivityMetrics]):
    """
    Plot average response curves for different angle ranges
    """
    # Group data by angle
    angle_data = {}
    for m in metrics:
        if m.angle not in angle_data:
            angle_data[m.angle] = []
        angle_data[m.angle].append(m.activity_difference)

    # Calculate mean and std for each angle
    angles = []
    means = []
    stds = []

    for angle in sorted(angle_data.keys()):
        angles.append(angle)
        means.append(np.mean(angle_data[angle]))
        stds.append(np.std(angle_data[angle]))

    angles = np.array(angles)
    means = np.array(means)
    stds = np.array(stds)

    # Create plot
    plt.figure(figsize=(10, 6))

    # Plot mean response curve
    plt.plot(angles, means, "b-", label="Mean Response")

    # Add confidence bands
    plt.fill_between(
        angles, means - stds, means + stds, alpha=0.3, color="blue", label="±1 STD"
    )

    # Add zero line
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.3)
    plt.axvline(x=0, color="k", linestyle="--", alpha=0.3)

    plt.xlabel("Angle (degrees)")
    plt.ylabel("Activity Difference (R-L)")
    plt.title("Average Response Curve")
    plt.legend()
    plt.grid(True, alpha=0.3)


def visualize_all(
    predictor: AnglePredictor,
    metrics: List[ActivityMetrics],
):
    """
    Create all visualizations

    Args:
        predictor: Trained AnglePredictor instance
        metrics: List of ActivityMetrics
        save_path: Optional path to save figures
    """

    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))

    # Plot decision boundaries
    plt.subplot(2, 1, 1)
    plot_decision_boundaries(predictor, metrics)

    # Plot response curves
    plt.subplot(2, 1, 2)
    plot_response_curves(predictor, metrics)
    plt.tight_layout()
    plt.show()


def test_predictor(results_list: List[Dict]):
    metric_type = METRIC.ICC_COUNTS
    predictor = AnglePredictor(metric_type=metric_type, angle_tolerance=10.0)
    metrics = predictor.prepare_data(results_list)
    predictor.plot_inputs(metrics)

    # X_train, y_train = predictor.prepare_training_data(metrics)
    X, y = predictor.prepare_training_data(metrics)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42
    )
    # plt.show()

    results = {}
    # for model_type in ["logistic", "svm"]:
    for model_type in ["svm"]:
        predictor.train(X_train, y_train, model_type=model_type)

        results[model_type] = {
            # "evaluation": predictor.evaluate(X_train, y_train),
            "evaluation": predictor.evaluate(X_test, y_test),
            # "quality_analysis": analyze_prediction_quality(predictor, metrics),
        }

        visualize_all(predictor, metrics)

    return results


if __name__ == "__main__":
    import dill

    from consts import Paths

    results_dir = (
        Path(Paths.RESULTS_DIR).absolute()
        / CURRENT_TEST
        / "withICC&gammatone&23lowerSBC2MSOhigherinhtoLSOsubj7"
    )
    results = [i for i in results_dir.glob("*.pic")]
    results_parsed = []
    for i in results:
        with open(i, "rb") as f:
            res = dill.load(f, ignore=False)
        results_parsed.append(res)

    res = test_predictor(results_parsed)

    # Look at performance in different regions
    for model_type, model_results in res.items():
        print(f"\n{model_type.upper()} Results:")
        print(model_results["evaluation"])
        # region_analysis = model_results["quality_analysis"]["region_analysis"]
        # for region, metrics in region_analysis.items():
        #     print(
        #         f"{region}: Error={metrics['mean_error']:.2f}°, "
        #         f"Confidence={metrics['mean_confidence']:.2f}"
        #     )
