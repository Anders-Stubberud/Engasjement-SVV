from source.features_dir import estimated_registrations
import pandas as pd
from source.config import TESTING_DATA_DIR

def test_estimated_registrations():

    estimated_registrations.main(testing=True)

    df_output = pd.read_csv(TESTING_DATA_DIR / 'estimated_registrations/output.csv')
    df_expected = pd.read_csv(TESTING_DATA_DIR / 'estimated_registrations/expected.csv')

    assert df_output.equals(df_expected)
