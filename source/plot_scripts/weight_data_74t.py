# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: nomarker
#       format_version: '1.0'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: .venv
#     language: python
#     name: python3
# ---

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from source.config import EXTERNAL_DATA_DIR
from source.config import INTERIM_DATA_DIR
from source.config import VEHICLE_WEIGHT_FIGURES_DIR_74T

FILTER_THRESHOLD_LOWER = 40000
FILTER_THRESHOLD_UPPER = 94000

plot = False
save = True


def get_datasets():
    """Load and preprocess the datasets for the 74T vehicle weight analysis."""

    df_74t_vehicle_weight_interim = pd.read_csv(INTERIM_DATA_DIR / "vehicle weight from 74t.csv")[
        ["VIN", "Max vekt"]
    ]
    df_vehicle_matching = pd.read_csv(EXTERNAL_DATA_DIR / "bil_tilhenger_matching.csv")

    df_74t_vehicle_weight = (
        pd.concat(
            [
                df_74t_vehicle_weight_interim.merge(
                    df_vehicle_matching[[col, "ekvipasje"]],
                    left_on="VIN",
                    right_on=col,
                    how="inner",
                )
                for col in ["VIN_lastebil", "VIN_tilhenger"]
            ]
        )
        .drop(columns=["VIN_lastebil", "VIN_tilhenger"], errors="ignore")
        .dropna()
    )

    VINs_trucks = df_vehicle_matching["VIN_lastebil"]
    df_74t_vehicle_weight_only_trucks = df_74t_vehicle_weight[
        df_74t_vehicle_weight["VIN"].isin(VINs_trucks)
    ]

    weights = df_74t_vehicle_weight_only_trucks["Max vekt"].dropna()
    weights = weights[(FILTER_THRESHOLD_LOWER <= weights) & (weights <= FILTER_THRESHOLD_UPPER)]
    weights_60 = weights[
        df_74t_vehicle_weight_only_trucks["ekvipasje"]
        == "3-akslet trekkvogn med 4-akslet tilhenger"
    ]
    weights_65 = weights[
        df_74t_vehicle_weight_only_trucks["ekvipasje"]
        == "3-akslet trekkvogn med 5-akslet tilhenger"
    ]
    weights_68 = weights[
        df_74t_vehicle_weight_only_trucks["ekvipasje"]
        == "4-akslet trekkvogn med 4-akslet tilhenger"
    ]
    weights_74 = weights[
        df_74t_vehicle_weight_only_trucks["ekvipasje"]
        == "4-akslet trekkvogn med 5-akslet tilhenger"
    ]

    # Define datasets for individual and grouped plots (same datasets)
    datasets = [
        (60, weights_60, "3-akslet trekkvogn med 4-akslet tilhenger (60T)", "dodgerblue"),
        (65, weights_65, "3-akslet trekkvogn med 5-akslet tilhenger (65T)", "fuchsia"),
        (68, weights_68, "4-akslet trekkvogn med 4-akslet tilhenger (68T)", "limegreen"),
        (74, weights_74, "4-akslet trekkvogn med 5-akslet tilhenger (74T)", "darkorange"),
    ]

    return datasets, weights


def plot_histogram(
    data, bins, color, edgecolor, title, xlabel, ylabel, save=False, plot=False, save_dir=None
):
    """Plot a histogram with a given dataset and save or show the plot."""
    plt.figure(figsize=(8, 6))
    plt.hist(data, bins=bins, color=color, edgecolor=edgecolor)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    if save and save_dir:
        plt.savefig(save_dir / f"{title}.png")
    if plot:
        plt.show()


def plot_grouped_histograms(
    datasets, bins, bar_width, title, xlabel, ylabel, save=False, plot=False, save_dir=None
):
    """Plot multiple histograms side by side with different colors and labels."""
    plt.figure(figsize=(8, 6))
    x_positions = bins[:-1]
    for i, (_, df, label, color) in enumerate(datasets):
        counts, _ = np.histogram(df, bins=bins)
        plt.bar(
            x_positions + (i * bar_width),
            counts,
            width=bar_width,
            color=color,
            edgecolor="black",
            alpha=0.7,
            label=label,
        )
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    if save and save_dir:
        plt.savefig(save_dir / f"{title}.png")
    if plot:
        plt.show()


def main():

    datasets, weights = get_datasets()

    # Plot Totalvekter for samtlige konfigurasjoner
    title = "Totalvekter, samtlige konfigurasjoner"
    plot_histogram(
        weights,
        bins=100,
        color="blue",
        edgecolor="black",
        title=title,
        xlabel="Max vekt under hver registrerte kjøretur (KG)",
        ylabel="Antall",
        save=save,
        plot=plot,
        save_dir=VEHICLE_WEIGHT_FIGURES_DIR_74T,
    )

    # Plot individual configurations
    for _, df, equipage, color in datasets:
        plot_histogram(
            df,
            bins=100,
            color=color,
            edgecolor="black",
            title=f"Totalvekter, {equipage}",
            xlabel="Max vekt under hver registrerte kjøretur (KG)",
            ylabel="Antall",
            save=save,
            plot=plot,
            save_dir=VEHICLE_WEIGHT_FIGURES_DIR_74T,
        )

    # Plot grouped histograms
    bins = np.linspace(min(weights), max(weights), 25)
    bar_width = 350
    plot_grouped_histograms(
        datasets,
        bins=bins,
        bar_width=bar_width,
        title="Totalvekter, samtlige konfigurasjoner, individuelle bidrag",
        xlabel="Max vekt under hver registrerte kjøretur (KG)",
        ylabel="Antall",
        save=save,
        plot=plot,
        save_dir=VEHICLE_WEIGHT_FIGURES_DIR_74T,
    )
