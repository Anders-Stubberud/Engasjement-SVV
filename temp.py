from google.colab import drive
drive.mount('/content/drive')

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
from datetime import datetime
from typing import Tuple
from pathlib import Path
import numpy as np
import pandas as pd
!pip install polars
import polars as pl
from tqdm import tqdm

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

basedir = Path('/content/drive/My Drive/Engasjement SVV')
raw_data_dir = basedir / 'WIM_flat_folder'
interim_data_dir = basedir / 'WIM_merged_new'
# endregion


def determine_f(dataset):
    dataset = str(dataset)
    if "Øysand" in dataset:
        return 0.5  # antar 2-feltsveg basert på google-streetview bilder fra området rundt øysand, vet ikke nøyaktig hvor sensoren er
    if "Skibotn" in dataset:
        return 0.5  # antar 2-feltsveg basert på google-streetview bilder fra området rundt skibotn, vet ikke nøyaktig hvor sensoren er
    if "Verdal" in dataset:
        return 0.5  # antar 2-feltsveg basert på google-streetview bilder fra området rundt verdal, vet ikke nøyaktig hvor sensoren er
    if "Aanestad" in dataset or 'Ånestad' in dataset:
        return 0.45  # antar 4-feltsveg basert på google-streetview bilder fra området rundt Ånestad, vet ikke nøyaktig hvor sensoren er

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

    def calculate_esal_and_number_of_axel_groups(df: pl.DataFrame):
        def calculate_esal_individual(row: tuple):
            def k_value(axles: int) -> float:
                return 1 if axles == 1 else (10 / (6 + 6 * axles)) ** 4

            def row_has_axle(row, axle):
                return (
                    f"{AXLE_DISTANCE}{axle}" in row
                    and row[f"{AXLE_DISTANCE}{axle}"] is not None
                    and row[f"{AXLE_WEIGHT}{axle}"] is not None
                )

            def store_previous_axle_group(weight_in_group, axles_in_group):
                nonlocal weights, k_values
                weights.append(weight_in_group)
                k_values.append(k_value(axles_in_group))

            weights_single_axles_single_vehicle = []  # Use lists instead of np.append
            weights = []  # Use lists instead of np.append
            k_values = []  # Use lists instead of np.append

            axle = 1
            axles_in_group = 0
            weight_in_group = 0

            while row_has_axle(row, axle):
                weights_single_axles_single_vehicle.append(float(row[f"{AXLE_WEIGHT}{axle}"]) / 1000)

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

            return weights, k_values, weights_single_axles_single_vehicle

        weights_single_axles_all_vehicles = []  # Use lists instead of np.append
        esal_values_individual_vehicles = []  # Use lists instead of np.append
        number_of_axel_groups = 0  # Number of axle groups

        for row in tqdm(list(df.iter_rows(named=True)), 'Iterating rows'):
            weights, k_values, singe_axle_weights = calculate_esal_individual(row)

            # Convert weights and k_values to numpy arrays to perform operations
            weights = np.array(weights)
            k_values = np.array(k_values)

            weights_single_axles_all_vehicles.extend(singe_axle_weights)  # Use list extend to add multiple items
            esal_values_individual_vehicles.append(np.sum((weights / 10) ** 4 * k_values))
            number_of_axel_groups += len(weights)

        return esal_values_individual_vehicles, number_of_axel_groups, np.array(weights_single_axles_all_vehicles)

    esals, ngrp, weights_single_axles_all_vehicles = calculate_esal_and_number_of_axel_groups(df)
    sigma_esals = np.sum(esals)
    nkjt = len(df)  # Number of vehicles

    e = np.sum((weights_single_axles_all_vehicles / 10)**4) / len(weights_single_axles_all_vehicles)
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
            filepath, separator=",", truncate_ragged_lines=True, ignore_errors=True
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

        return n, ådtt, b, earliest_date, latest_date, e, c

    n_1, ådtt_1, b_1, startdate, enddate, e1, c1 = calculate_factors_individual_lengthlimit(
        filepath, length_limit_1
    )
    n_2, ådtt_2, b_2, _, _, e2, c2 = calculate_factors_individual_lengthlimit(filepath, length_limit_2)

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
        e1,
        e2,
        c1,
        c2
    )

    result = tuple(round(value, 2) for value in result)

    return startdate, enddate, *result


def extract_location(filepath):
    filepath = str(filepath)
    if 'vestg' in filepath or 'Vestgående' in filepath or 'vestgående' in filepath:
        return "Ånestad (vestgående)"
    if 'ostg' in filepath or 'Ostgående' in filepath or 'østgående' in filepath:
        return "Ånestad (østgående)"
    if "Øysand" in filepath:
        return "Øysand"
    if "Skibotn" in filepath or "combinedFiles_E8" in filepath:
        return "Skibotn"
    if "Verdal" in filepath:
        return "Verdal"


def merge_dfs_similar_location():
    datasets = []

    for root, _, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith(".csv"):
                absolute_path = os.path.abspath(os.path.join(root, file))
                datasets.append(absolute_path)

    keywords = ["Øysand", "Verdal", "Ånestad (vestgående)", "Ånestad (østgående)", "Skibotn"]

    dataframes = {key: [] for key in keywords}

    valid_ranges = {
        'VehicleLength': (0, 30),
        'AxlesCount': (0, 10),
        'AxleDistance': (0, 10),
        'AxleWeight': (0, 15000)
    }

    for file_path in tqdm(datasets, desc="Processing files"):
        for keyword in keywords:
            if extract_location(file_path) == keyword and file_path.endswith(".csv"):
                try:
                    # Read the CSV, with error handling for bad lines
                    df = pd.read_csv(
                        file_path,
                        skiprows=6,
                        sep=";",
                        # nrows=1000,
                        on_bad_lines="skip",
                        low_memory=False,
                    )

                    df.columns = [col.replace(" ", "") for col in df.columns]

                    # Define required columns
                    numerical_required_columns = (
                        [VEHICLE_LENGTH, AXLES_COUNT]
                        + [f"{AXLE_DISTANCE}{i}" for i in range(1, 11)] # for å unngå store frames; antar kun kjøretøy m/ <= 10 aksler
                        + [f"{AXLE_WEIGHT}{i}" for i in range(1, 11)]
                    )
                    all_required_columns = numerical_required_columns + [STARTTIME]

                    missing_columns = [
                        col for col in all_required_columns if col not in df.columns
                    ]
                    missing_data = {col: np.nan for col in missing_columns}

                    if missing_data:
                        # Create missing columns with NaN values and correct index
                        df_missing = pd.DataFrame(missing_data, index=df.index)
                        df = pd.concat([df, df_missing], axis=1)

                    df = df[all_required_columns]
                    numerical_df = df[numerical_required_columns]
                    non_numerical_df = df.drop(columns=numerical_required_columns)

                    # Apply coercion only to numerical columns
                    numerical_df = numerical_df.apply(pd.to_numeric, errors="coerce")

                    # Concatenate the coerced numerical columns with the non-numerical ones
                    df = pd.concat([numerical_df, non_numerical_df], axis=1)

                    df = df[(df['VehicleLength'] >= valid_ranges['VehicleLength'][0]) & (df['VehicleLength'] <= valid_ranges['VehicleLength'][1])]
                    df = df[(df['AxlesCount'] >= valid_ranges['AxlesCount'][0]) & (df['AxlesCount'] <= valid_ranges['AxlesCount'][1])]

                    for col in df.columns:
                        if col.startswith('AxleDistance'):
                            df = df[
                                ((df[col] >= valid_ranges['AxleDistance'][0]) & (df[col] <= valid_ranges['AxleDistance'][1])) | df[col].isna()
                            ]

                        elif col.startswith('AxleWeight'):
                            df = df[
                                ((df[col] >= valid_ranges['AxleWeight'][0]) & (df[col] <= valid_ranges['AxleWeight'][1])) | df[col].isna()
                            ]

                    dataframes[keyword].append(df)

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    # Combine dataframes for each keyword
    grouped_dfs = {
        key: pd.concat([df.dropna(axis=1, how="all") for df in dataframes[key]], ignore_index=True)
        for key in dataframes
        if dataframes[key]
    }

    # Write the resulting DataFrames to CSV
    os.makedirs(interim_data_dir, exist_ok=True)

    for key, df in grouped_dfs.items():
        df.to_csv(interim_data_dir / f"{key}.csv", index=False)


def main():

    merge_dfs_similar_location()

    datasets = [
        interim_data_dir / "Øysand.csv",
        interim_data_dir / "Verdal.csv",
        interim_data_dir / "Ånestad (vestgående).csv",
        interim_data_dir / "Ånestad (østgående).csv",
        interim_data_dir / "Skibotn.csv",
    ]

    headers = ["Sted", "Startdato", "Sluttdato", "N 5.6", "N 7.5", "Absolutt endring i N", "Prosentvis endring i N",
               "ÅDTT 5.6", "ÅDTT 7.5", "Absolutt endring i ÅDTT", "Prosentvis endring i ÅDTT",
               "B-faktor 5.6", "B-faktor 7.5", "Absolutt endring i B-faktor", "Prosentvis endring i B-faktor",
               'E 5.6', 'E 7.5', 'C 5.6', 'C 7.5'
    ]

    results = []

    for dataset in datasets:
        location = extract_location(dataset)
        results.append((location, *calculate_factors(dataset, OLD_LIMIT_HEAVY_VEHICLE, NEW_LIMIT_HEAVY_VEHICLE)))

    df = pl.DataFrame(schema=headers, data=results, orient='row')
    df.write_csv(basedir / 'WIM_road_wear_indicators.csv')

main()
