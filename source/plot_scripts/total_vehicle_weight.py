import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from source import config

N_BINS = [10, 20, 25]

PLOT_FILE_NAMES = lambda plot, location, n_bins: (
    f"Totalvekter, {location}, {plot}" f"{f', {n_bins} intervaller' if n_bins else ''}"
)

ALL_LOCATIONS = "samtlige lokasjoner"

LABEL_X_AXIS_LINEPLOT = "Vekt (KG)"
LABEL_Y_AXIS_LINEPLT = "Relativ andel"
LABEL_X_AXIS_BARPLOT = "Vektintervaller (KG)"
LABEL_Y_AXIS_BARPLOT = "Antall registreringer"

DELTA_LINEPLOT_CUTOFF = 10e-4

color = {
    "barplot": "dodgerblue",
    "lineplot": "black",
}


def plot_bars(df: pd.DataFrame) -> None:
    locations = df["location"].unique()
    weight_columns = df.columns[1:]

    for location in locations:
        df_location = df[df["location"] == location]

        for n_bins in N_BINS:
            bin_size = len(weight_columns) // n_bins
            binned_values = (
                df_location[weight_columns]
                .T.groupby(np.arange(len(weight_columns)) // bin_size)
                .sum()
                .T
            )

            # Create bin labels for each interval
            bin_labels = [
                f'{weight_columns[i].split("-")[0]}-{weight_columns[min(i + bin_size - 1, len(weight_columns) - 1)].split("-")[-1]}'
                for i in range(0, len(weight_columns), bin_size)
            ]
            binned_values.columns = bin_labels

            title = PLOT_FILE_NAMES("barplot", location, n_bins)
            plt.figure(figsize=(12, 6))
            binned_values.mean().plot(kind="bar", color=color["barplot"], width=0.8)
            plt.title(title)
            plt.xlabel(LABEL_X_AXIS_BARPLOT)
            plt.ylabel(LABEL_Y_AXIS_BARPLOT)
            plt.xticks(ticks=np.arange(len(bin_labels)), labels=bin_labels, rotation=45)
            plt.tight_layout()

            file_path = f"{config.VEHICLE_WEIGHT_FIGURES_DIR_WIM / title}.png"
            plt.savefig(file_path)
            plt.close()


def plot_lines(df: pd.DataFrame) -> None:
    locations = df["location"].unique()
    weight_columns = df.columns[1:]
    midpoint_labels = []

    for column in weight_columns:
        try:
            start, end = column.split("-")
            midpoint = (float(start) + float(end)) / 2
            midpoint_labels.append(midpoint)
        except ValueError as e:
            print(f"Error parsing column '{column}': {e}")
            midpoint_labels.append(None)

    # Define cutoff for all charts
    cutoff_midpoint = None

    # Plot relative weights for each location
    for location in locations:
        df_location = df[df["location"] == location]
        df_location_rel = df_location[weight_columns].div(
            df_location[weight_columns].sum(axis=1), axis=0
        )

        plt.figure(figsize=(12, 6))
        for _, row in df_location_rel.iterrows():
            cutoff_idx = (
                np.where(row >= DELTA_LINEPLOT_CUTOFF)[0][-1]
                if np.any(row >= DELTA_LINEPLOT_CUTOFF)
                else 0
            )
            cutoff_midpoint = max(cutoff_midpoint or 0, midpoint_labels[cutoff_idx])
            plt.plot(
                midpoint_labels[: cutoff_idx + 1],
                row[: cutoff_idx + 1],
                alpha=1,
                color=color["lineplot"],
            )

        title = PLOT_FILE_NAMES("lineplot", location, None)
        plt.title(title)
        plt.xlabel(LABEL_X_AXIS_LINEPLOT)
        plt.ylabel(LABEL_Y_AXIS_LINEPLT)
        plt.xticks(
            ticks=np.arange(5000, cutoff_midpoint + 1, 5000),
            labels=[f"{int(x)}" for x in np.arange(5000, cutoff_midpoint + 1, 5000)],
            rotation=45,
        )
        plt.tight_layout()

        file_path = f"{config.VEHICLE_WEIGHT_FIGURES_DIR_WIM / title}.png"
        plt.savefig(file_path)
        plt.close()

    # Plot average relative weights across all locations
    plt.figure(figsize=(12, 6))
    for location in locations:
        df_location = df[df["location"] == location]
        df_location_rel = df_location[weight_columns].div(
            df_location[weight_columns].sum(axis=1), axis=0
        )
        avg_relative = df_location_rel.mean()
        cutoff_idx = (
            np.where(avg_relative >= DELTA_LINEPLOT_CUTOFF)[0][-1]
            if np.any(avg_relative >= DELTA_LINEPLOT_CUTOFF)
            else 0
        )
        cutoff_midpoint = max(cutoff_midpoint, midpoint_labels[cutoff_idx])

        plt.plot(
            midpoint_labels[: cutoff_idx + 1],
            avg_relative[: cutoff_idx + 1],
            label=f"{location}",
            alpha=0.75,
        )

    title = PLOT_FILE_NAMES("lineplot", ALL_LOCATIONS, None)
    plt.title(title)
    plt.xlabel(LABEL_X_AXIS_LINEPLOT)
    plt.ylabel(LABEL_Y_AXIS_LINEPLT)
    plt.legend(loc="best")
    plt.xticks(
        ticks=np.arange(5000, cutoff_midpoint + 1, 5000),
        labels=[f"{int(x)}" for x in np.arange(5000, cutoff_midpoint + 1, 5000)],
        rotation=45,
    )
    plt.tight_layout()

    file_path = f"{config.VEHICLE_WEIGHT_FIGURES_DIR_WIM / title}.png"
    plt.savefig(file_path)
    plt.close()


def main():
    os.makedirs(config.VEHICLE_WEIGHT_FIGURES_DIR_WIM, exist_ok=True)

    df = pd.read_csv(config.INTERIM_DATA_DIR / "total vehicle weight grouped by location.csv")

    plot_bars(df)
    plot_lines(df)
