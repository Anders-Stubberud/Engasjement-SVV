from source.features_dir import road_wear_indicators
from random import randint
from datetime import datetime
import pandas as pd
import polars as pl
from math import isclose
import numpy as np

MILLISECONDS_1_DAY = 1000 * 60 * 60 * 24
STARTTIME = int(datetime(2020, 1, 11, 12, 30).timestamp())
AXLES_COUNT = "AxlesCount"


def test_ådtt():
    unique_days = randint(1, 1000)

    data = [
        STARTTIME + i * MILLISECONDS_1_DAY
        for i in range(unique_days)
        for _ in range(randint(1, 2000))
    ]
    df = pd.DataFrame(data, columns=['StartTime'])
    
    total_registrations_first_year = len([t for t in data if t < STARTTIME + 365 * MILLISECONDS_1_DAY])
    actual_ådtt = total_registrations_first_year / min(365, unique_days)
    
    calculated_ådtt = road_wear_indicators.calculate_ådtt(pl.from_pandas(df))
    assert isclose(actual_ådtt, calculated_ådtt, rel_tol=1) # tar hånd om avrundingsfeil


def test_e_and_b():
    AXLE_WEIGHT = 'AxleWeight'
    AXLE_DISTANCE = 'AxleDistance'

    df = pd.DataFrame({
        f'{AXLE_WEIGHT}1': [7000, 7000, 6000],
        f'{AXLE_WEIGHT}2': [8000, 10000, 7000],
        f'{AXLE_WEIGHT}3': [9000, 10000, 8000],
        f'{AXLE_WEIGHT}4': [8000, 10000, 9000],
        f'{AXLE_WEIGHT}5': [8000, 12000, 10000],
        f'{AXLE_WEIGHT}6': [8000, 13000, 11000],
        f'{AXLE_WEIGHT}7': [None, 11000, 12000],
        f'{AXLE_WEIGHT}8': [None, 12000, 13000],
        f'{AXLE_WEIGHT}9': [None, 13000, None],
        f'{AXLE_DISTANCE}1': [0, 0, 0],
        f'{AXLE_DISTANCE}2': [4, 3, 3],
        f'{AXLE_DISTANCE}3': [1.5, 1, 1.5],
        f'{AXLE_DISTANCE}4': [6, 1, 4],
        f'{AXLE_DISTANCE}5': [1, 6, 1],
        f'{AXLE_DISTANCE}6': [1, 1, 5],
        f'{AXLE_DISTANCE}7': [None, 4, 0.8],
        f'{AXLE_DISTANCE}8': [None, 1, 0.9],
        f'{AXLE_DISTANCE}9': [None, 1, None],
    })

    weights_individual_axles = np.array([
        7, 8, 9, 8, 8, 8,
        7, 10, 10, 10, 12, 13, 11, 12, 13, 
        6, 7, 8, 9, 10, 11, 12, 13,
    ])
    n_individual_axles = len(weights_individual_axles)

    weights_axle_groups = np.array([
        7, 17, 24,
        7, 30, 25, 36, 
        6, 15, 19, 36,
    ])
    k_values_axle_groups = [
        1, (10/18)**4, (10/24)**4, 
        1, (10/24)**4, (10/18)**4, (10/24)**4,
        1, (10/18)**4, (10/18)**4, (10/24)**4,
    ]
    n_axle_groups = len(weights_axle_groups)

    e = (1 / n_individual_axles) * np.sum((weights_individual_axles / 10)**4)
    b = (1 / n_axle_groups) * np.sum((weights_axle_groups / 10)**4 * k_values_axle_groups)

    calculated_e, calculated_b = road_wear_indicators.calculate_e_and_b(pl.from_pandas(df))

    assert isclose(e, calculated_e)
    assert isclose(b, calculated_b)


def test_calculate_c():
    num_rows = np.random.randint(50000, 100000)
    random_axles = np.random.randint(2, 11, size=num_rows)
    df = pl.DataFrame({AXLES_COUNT: random_axles})
    expected_c = random_axles.mean()
    calculated_c = road_wear_indicators.calculate_c(df)
    assert isclose(calculated_c, expected_c)
