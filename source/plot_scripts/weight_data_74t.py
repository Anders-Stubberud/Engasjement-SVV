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
import pandas as pd

from source.config import EXTERNAL_DATA_DIR
from source.config import INTERIM_DATA_DIR
from source.config import VEHICLE_WEIGHT_FIGURES_DIR_74T

FILTER_THRESHOLD_LOWER = 40000
FILTER_THRESHOLD_UPPER = 94000

plot = False
save = True


def main():

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

    for tonnage, equipage in [
        (60, "3-akslet trekkvogn med 4-akslet tilhenger"),
        (65, "3-akslet trekkvogn med 5-akslet tilhenger"),
        (68, "4-akslet trekkvogn med 4-akslet tilhenger"),
        (74, "4-akslet trekkvogn med 5-akslet tilhenger"),
        (None, "samtlige konfigurasjoner"),
        (None, "samtlige konfigurasjoner, individuelle bidrag"),
    ]:

        weights = df_74t_vehicle_weight_only_trucks["Max vekt"].dropna()
        if 'trekkvogn' in equipage:
            weights = weights[df_74t_vehicle_weight_only_trucks["ekvipasje"] == equipage]

        filtered_weights = weights[
            (FILTER_THRESHOLD_LOWER <= weights) & (weights <= FILTER_THRESHOLD_UPPER)
        ]

        title = f"{equipage} {f'({tonnage}T)'if tonnage else ''}"
        plt.figure(figsize=(8, 6))
        plt.hist(filtered_weights, bins=50, color="blue", edgecolor="black")
        plt.title(title)
        plt.xlabel("Max vekt under hver registrerte kjøretur (KG)")
        plt.ylabel("Antall")
        plt.tight_layout()

        if save:
            plt.savefig(
                VEHICLE_WEIGHT_FIGURES_DIR_74T
                / f"Totalvekter, {equipage}.png"
            )

        if plot:
            plt.show()
