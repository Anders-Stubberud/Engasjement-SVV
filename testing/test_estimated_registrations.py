from source.features_dir import estimated_registrations
import pandas as pd
from source.config import TESTING_DATA_DIR
import pytest

def test_estimated_registrations():

    estimated_registrations.main(road_coordinates=estimated_registrations.COORDINATE_POINTS_ROADS, testing=True)

    df_output = pd.read_csv(TESTING_DATA_DIR / 'estimated_registrations/output.csv')
    df_expected = pd.read_csv(TESTING_DATA_DIR / 'estimated_registrations/expected.csv')

    assert df_output.equals(df_expected)

def test_updated_boundaries():
    estimated_registrations.main(
        road_coordinates=estimated_registrations.COORDINATES_BWIM_74T,
        testing=True,
        testfile='test_boundaries_input.csv',
        testoutput='test_output_boundaries.csv'
    )

    df_output = pd.read_csv(TESTING_DATA_DIR / 'estimated_registrations/test_output_boundaries.csv')
    df_expected = pd.read_csv(TESTING_DATA_DIR / 'estimated_registrations/test_expected_boundaries.csv')

    try:
        pd.testing.assert_frame_equal(df_output, df_expected, check_dtype=False)
    except AssertionError as e:
        pytest.fail(f"DataFrames are not equal:\n{e}")
