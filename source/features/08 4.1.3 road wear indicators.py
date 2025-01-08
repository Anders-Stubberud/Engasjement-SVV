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

# Imports

import os
import re
import pandas as pd
from datetime import datetime
from typing import Tuple
from tqdm import tqdm

import numpy as np
import polars as pl

from source import config

# region Konstanter

TIME = "StartTimeStr"
STARTTIME = "StartTime"
STARTDATE = "StartDate"
AXLES_COUNT = "AxlesCount"
AXLE_WEIGHT = "AxleWeight"
STARTTIME_UNIX = "StartTime"
AXLE_DISTANCE = "AxleDistance"
VEHICLE_LENGTH = "VehicleLength"
LIMIT_AXLES_SAME_GROUP = 1.8
OLD_LIMIT_HEAVY_VEHICLE = 5.6
NEW_LIMIT_HEAVY_VEHICLE = 7.5
MILLISECONDS_IN_YEAR = 1000 * 60 * 60 * 24 * 365
P = 1  # P er forventet årlig trafikkvekst for tunge kjøretøy, antar her at trafikkveksten holder seg konstant

# endregion


def determine_f(dataset):
    if "Øysand" in dataset:
        return 0.5  # antar 2-feltsveg basert på google-streetview bilder fra området rundt øysand, vet ikke nøyaktig hvor sensoren er
    if "Skibotn" in dataset:
        return 0.5  # antar 2-feltsveg basert på google-streetview bilder fra området rundt skibotn, vet ikke nøyaktig hvor sensoren er
    if "Verdal" in dataset:
        return 0.5  # antar 2-feltsveg basert på google-streetview bilder fra området rundt verdal, vet ikke nøyaktig hvor sensoren er
    if "Aanestad" in dataset:
        return 0.45  # antar 4-feltsveg basert på google-streetview bilder fra området rundt Ånestad, vet ikke nøyaktig hvor sensoren er


datasets = (
    "../WIM-data/Kistler_Øysand/20160808-31_Kistler Øysand_4913151-export(1).csv",
    "../WIM-data/Kistler_Øysand/20160901-30_Kistler Øysand_4913151-export(2).csv",
    "../WIM-data/Kistler_Øysand/20161001-31_Kistler Øysand_4913151-export(3)-fixed.csv",
    "../WIM-data/Kistler_Øysand/20161101-30_Kistler Øysand_4913151-export(4).csv",
    "../WIM-data/Kistler_Øysand/20161201-31_Kistler Øysand_4913151-export(5).csv",
    "../WIM-data/Kistler_Øysand/20170101-31_Kistler Øysand_4913151-export(6).csv",
    "../WIM-data/Kistler_Øysand/20170201-28_Kistler Øysand_4913151-export(7).csv",
    "../WIM-data/Kistler_Øysand/20170301-31_Kistler Øysand_4913151-export(8).csv",
    "../WIM-data/Kistler_Øysand/20170401-05_Kistler Øysand_4913151-export(9)-fixed.csv",
    "../WIM-data/Kistler_Øysand/20180316_1.3.1_Kistler Øysand_4913151-export(24).csv",
    "../WIM-data/Kistler_Øysand/20180401-30_Kistler Øysand_4796227-export(12).csv",
    "../WIM-data/Kistler_Øysand/20180501-31(21-26)_Kistler Øysand_4796227-export(13).csv",
    "../WIM-data/Kistler_Øysand/20180601-30(11-30)_Kistler Øysand_4796227-export(14).csv",
    "../WIM-data/Kistler_Øysand/20180701-31(01-11)_Kistler Øysand_4796227-export(15).csv",
    "../WIM-data/Kistler_Øysand/20180801-31(10-31)_Kistler Øysand_4796227-export(16).csv",
    "../WIM-data/Kistler_Øysand/20180901-30_Kistler Øysand 4796227-export(17).csv",
    "../WIM-data/Kistler_Skibotn/combinedFiles_E8_2018_kalibrert_4okt.csv",
    "../WIM-data/Kistler_Skibotn/combinedFiles_E8_2019.csv",
    "../WIM-data/Kistler_Skibotn/combinedFiles_E8_2020.csv",
    "../WIM-data/Kistler_Verdal/20150513-20150531_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20150601-20150630_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20150701-20150731_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20150801-20150831_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20150901-20150930_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20151001-20151031_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20151101-20151130_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20151201-20151231_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20160101-20160131_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20160201-20160229_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20160301-20160331_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20160401-20160430_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Verdal/20160501-20160531_Kistler Verdal 4796227.csv",
    "../WIM-data/Kistler_Aanestad/20221014-20 Kistler_R3_ostg.csv",
    "../WIM-data/Kistler_Aanestad/20221014-20 Kistler_R3_vestg.csv",
    "../WIM-data/Kistler_Aanestad/20231001-20240123_Aanestad_Ostgående.csv",
    "../WIM-data/Kistler_Aanestad/20231001-20240123_Aanestad_Vestgående.csv",
    "../WIM-data/Kistler_Aanestad/20240122-20240612_R3 vestgående.csv",
    "../WIM-data/Kistler_Aanestad/20240123-20240612_R3 østgående.csv",
)


def calculate_n(c, e, ådtt, f, p):
    return 365 * c * e * ådtt * f * ((1 + 0.01 * p) ** 20 - 1) / (0.01 * p)


def calculate_c(df: pl.DataFrame) -> float:
    axles_heavy_vehicles = df.select(pl.col(AXLES_COUNT)).to_series().to_list()
    axles_heavy_vehicles = np.array([int(axle) for axle in axles_heavy_vehicles])
    n = len(axles_heavy_vehicles)
    c = np.sum(axles_heavy_vehicles) / n

    return c


def calculate_e_and_b(df: pl.DataFrame) -> Tuple[float, float]:
    """
    Regner ut E (gjennomsnittlig ekvivalensfaktor for akslene på tunge kjøretøy) og B-faktor (gjennomsnittlig nedbrytende effekt).
    Samlet i en funksjon etterom begge verdier baserer seg på summen av ESALS-verdier, som har blitt implementert med iterasjon gjennom
    hver rad i datasettet (kostbar beregning; tar lang tid).

    Parameters
    ----------
    df : pl.DataFrame
        Polars dataframe som det skal beregnes E og B-faktor for.

    Returns
    -------
    calculate_e_and_b : Tuple[float, float]
        Float's som representerer E og B-faktor.
    """

    def calculate_esal_and_number_of_axel_groups(df: pl.DataFrame) -> float:

        def calculate_esal_individual(row: tuple) -> float:

            def k_value(axles: int) -> float:
                return 1 if axles == 1 else (10 / (6 + 6 * axles)) ** 4

            def row_has_axle(row, axle):
                return (
                    f"{AXLE_DISTANCE}{axle}" in row
                    and row[f"{AXLE_DISTANCE}{axle}"] != None
                    and row[f"{AXLE_WEIGHT}{axle}"] != None
                )

            def store_previous_axle_group(weight_in_group, axles_in_group):
                nonlocal weights, k_values
                weights = np.append(weights, weight_in_group)
                k_values = np.append(k_values, k_value(axles_in_group))

            weights = np.array([])
            k_values = np.array([])

            axle = 1
            axles_in_group = 0
            weight_in_group = 0

            while row_has_axle(row, axle):

                distance_from_previous_axle = float(row[f"{AXLE_DISTANCE}{axle}"])

                if distance_from_previous_axle <= LIMIT_AXLES_SAME_GROUP:
                    axles_in_group += 1
                    weight_in_group += float(row[f"{AXLE_WEIGHT}{axle}"]) / 1000

                else:
                    store_previous_axle_group(weight_in_group, axles_in_group)
                    axles_in_group = 1
                    weight_in_group = float(row[f"{AXLE_WEIGHT}{axle}"]) / 1000

                axle += 1

            store_previous_axle_group(weight_in_group, axles_in_group)

            return weights, k_values

        esal_values_individual_vehicles = np.array([])
        number_of_axel_groups = (
            0  # ngrp, antall akselgrupper (dvs. enkeltaksler + boggiaksler + trippelaksler osv.)
        )

        for row in df.iter_rows(named=True):
            weights, k_values = calculate_esal_individual(row)
            esal_values_individual_vehicles = np.append(
                esal_values_individual_vehicles, np.sum((weights / 10) ** 4 * k_values)
            )
            number_of_axel_groups += len(weights)

        return esal_values_individual_vehicles, number_of_axel_groups

    esals, ngrp = calculate_esal_and_number_of_axel_groups(df)  # ngrp er antall akselgrupper
    sigma_esals = np.sum(esals)
    nkjt = len(df)  # antall kjøretøy

    e = sigma_esals / ngrp
    b = sigma_esals / nkjt

    return e, b


def calculate_ådtt(df: pl.DataFrame, start_daterange: datetime = None) -> float:

    # dersom veiens åpningsdato ikke er eksplisitt definert benyttes den første registrerte verdien i filen
    if start_daterange is None:
        start_unix = df.select(pl.col(STARTTIME_UNIX).min()).to_numpy()[0, 0]
    else:
        start_unix = int(start_daterange.timestamp() * 1000)
    end_unix = start_unix + MILLISECONDS_IN_YEAR

    heavy_vehicles_first_year = df.filter(
        (pl.col(STARTTIME_UNIX) >= start_unix) & (pl.col(STARTTIME_UNIX) <= end_unix)
    )

    df = df.with_columns(
        (
            pl.col(STARTTIME_UNIX).map_elements(
                lambda ts: datetime.fromtimestamp(int(ts) / 1000).strftime("%Y-%m-%d"),
                return_dtype=pl.String,
            )
        ).alias(STARTDATE)
    )

    unique_days_in_range = df.select(pl.col(STARTDATE)).n_unique()
    number_of_heavy_vehicles = len(heavy_vehicles_first_year)
    ådtt = number_of_heavy_vehicles / unique_days_in_range

    return ådtt


def calculate_factors(
    filepath: str, length_limit_1: float, length_limit_2: float
) -> Tuple[float, float, float, float, float, float, float, float, float, float, float, float]:
    """
    Samlefunksjon som hovedsakelig beregner N for gammel og ny lengdegrense for tunge kjøretøy.
    Beregner videre endringen i N endringen i lengdegrensen fører med seg (absolutt og prosentvis endring).
    Beregner videre B-faktor for begge lengdegrenser, samt endringen (absolutt og prosentvis endring).
    Inkluderer ÅDTT for begge lengdegrenser, samt endringen (absolutt og prosentvis endring).

    Parameters
    ----------
    filepath : str
        Filstien til datasettet beregningene skal gjøres på.
    length_limit_1: float
        Første lengdegrense for tunge kjøretøy.
    length_limit_2: flaot
        Andre lengregrense for tunge kjøretøy

    Returns
    -------
    N for første lengdegrense: float
    N for andre lengdegrense: float
    Absolutt endring av N ved overgang fra første til andre lengdegrense: float
    Prosentvis endring av N ved overgang fra første til andre lengdegrense: float
    ÅDTT for første lengdegrense: float
    ÅDTT for andre lengdegrense: float
    Absolutt endring av ÅDTT ved overgang fra første til andre lengdegrense: float
    Prosentvis endring av ÅDTT ved overgang fra første til andre lengdegrense: float
    B-faktor for første lengdegrense: float
    B-faktor for andre lengdegrense: float
    Absolutt endring av B-faktor ved overgang fra første til andre lengdegrense: float
    Prosentvis endring av B-faktor ved overgang fra første til andre lengdegrense: float
    """

    def calculate_factors_individual_lengthlimit(
        filepath: str, length_limit
    ) -> Tuple[float, float, float]:
        df = pl.read_csv(
            filepath, skip_rows=6, separator=";", truncate_ragged_lines=True, ignore_errors=True
        )
        df = df.filter(pl.col(VEHICLE_LENGTH) >= length_limit)
        df = df.with_columns(
            pl.col(STARTTIME).cast(pl.Datetime(time_unit="ms")).alias("unix_timestamp")
        )

        earliest_date = df["unix_timestamp"].min().date().isoformat()
        latest_date = df["unix_timestamp"].max().date().isoformat()

        ådtt = calculate_ådtt(df)
        e, b = calculate_e_and_b(df)
        c = calculate_c(df)
        f = determine_f(filepath)
        n = calculate_n(c, e, ådtt, f, P)

        return n, ådtt, b, earliest_date, latest_date

    n_1, ådtt_1, b_1, startdate, enddate = calculate_factors_individual_lengthlimit(
        filepath, length_limit_1
    )
    n_2, ådtt_2, b_2, _, _ = calculate_factors_individual_lengthlimit(filepath, length_limit_2)

    absolute_change_n = n_2 - n_1
    relative_change_n = ((n_2 - n_1) / n_1) * 100

    absolute_change_ådtt = ådtt_2 - ådtt_1
    relative_change_ådtt = ((ådtt_2 - ådtt_1) / ådtt_1) * 100

    absolute_change_b = b_2 - b_1
    relative_change_b = ((b_2 - b_1) / b_1) * 100

    result = (
        n_1,
        n_2,
        absolute_change_n,
        relative_change_n,
        ådtt_1,
        ådtt_2,
        absolute_change_ådtt,
        relative_change_ådtt,
        b_1,
        b_2,
        absolute_change_b,
        relative_change_b,
    )

    result = tuple(round(value, 2) for value in result)

    return startdate, enddate, *result


def extract_location(filepath):
    if "Aanestad" in filepath and ("Vest" in filepath or "vest" in filepath):
        return "Ånestad (vestgående)"
    if "Aanestad" in filepath and (
        "Ost" in filepath or "ost" in filepath or "Øst" in filepath or "øst" in filepath
    ):
        return "Ånestad (østgående)"
    if "Øysand" in filepath:
        return "Øysand"
    if "Skibotn" in filepath:
        return "Skibotn"
    if "Verdal" in filepath:
        return "Verdal"


def merge_dfs_similar_location():
    datasets = []

    for root, _, files in os.walk(config.RAW_DATA_DIR / "WIM"):
        for file in files:
            if file.endswith(".csv"):
                absolute_path = os.path.abspath(os.path.join(root, file))
                datasets.append(absolute_path)

    keywords = ["Øysand", "Verdal", "Ånestad (vestgående)", "Ånestad (østgående)", "Skibotn"]
    
    dataframes = {key: [] for key in keywords}

    for file_path in tqdm(datasets, desc="Processing files"):
        for keyword in keywords:
            if extract_location(file_path) == keyword and file_path.endswith(".csv"):
                try:
                    # Read the CSV, with error handling for bad lines
                    df = pd.read_csv(
                        file_path,
                        skiprows=6,
                        sep=";",
                        nrows=50000,
                        on_bad_lines="skip",
                        low_memory=False,
                    )

                    df.columns = [col.replace(" ", "") for col in df.columns]

                    # Define required columns
                    numerical_required_columns = [VEHICLE_LENGTH, AXLES_COUNT] + [f"{AXLE_DISTANCE}{i}" for i in range(1, 65)] + [f"{AXLE_WEIGHT}{i}" for i in range(1, 65)]
                    all_required_columns = numerical_required_columns + [STARTTIME]

                    missing_columns = [col for col in all_required_columns if col not in df.columns]
                    missing_data = {col: np.nan for col in missing_columns}

                    if missing_data:
                        # Create missing columns with NaN values and correct index
                        df_missing = pd.DataFrame(missing_data, index=df.index)
                        df = pd.concat([df, df_missing], axis=1)

                    df = df[all_required_columns]

                    df_coerced = df[numerical_required_columns].apply(pd.to_numeric, errors='coerce')

                    mask = df_coerced.isna() & df[numerical_required_columns].notna()

                    df_cleaned = df[~mask]
                    dataframes[keyword].append(df_cleaned)

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    # Combine dataframes for each keyword
    grouped_dfs = {
        key: pd.concat([df.dropna(axis=1, how='all') for df in dataframes[key]], ignore_index=True)
        for key in dataframes if dataframes[key]
    }


    # Write the resulting DataFrames to CSV
    interim_storage = config.INTERIM_DATA_DIR / "WIM"
    os.makedirs(interim_storage, exist_ok=True)

    for key, df in grouped_dfs.items():
        df.to_csv(interim_storage / f"{key}.csv", index=False)

def main():
    merge_dfs_similar_location()
    # headers = ["Sted", "Startdato", "Sluttdato", "N 5.6", "N 7.5", "Absolutt endring i N", "Prosentvis endring i N",
    #         "ÅDTT 5.6", "ÅDTT 7.5", "Absolutt endring i ÅDTT", "Prosentvis endring i ÅDTT",
    #             "B-faktor 5.6", "B-faktor 7.5", "Absolutt endring i B-faktor", "Prosentvis endring i B-faktor"]

    # for dataset in datasets:
    #     try:
    #         location = extract_location(dataset)

    #         results = (location, *calculate_factors(dataset, OLD_LIMIT_HEAVY_VEHICLE, NEW_LIMIT_HEAVY_VEHICLE))

    #         df = pl.DataFrame(schema=headers, data=results)
    #         df.write_csv('../resultater/n_påvirkning_klassifisering.csv')
    #     except:
    #         pass

if __name__ == "__main__":
    main()
