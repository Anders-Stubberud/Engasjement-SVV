from pathlib import Path

import pandas as pd
import typer

from source.config import INTERIM_DATA_DIR
from source.config import MODE_AXLE_LOAD
from source.config import MODE_VEHICLE_WEIGHT_74T
from source.config import MODE_VEHICLE_WEIGHT_WIM
from source.config import PROCESSED_DATA_DIR
from source.config import RAW_DATA_DIR
from source.utils import should_run_task

app = typer.Typer()


def calculate_axle_load_distributions(df: pd.DataFrame) -> None:
    """
    Calculate the axle load distributions for each location and save the results to csv files.
    Args:
        df (pd.DataFrame): The dataframe containing the axle load distribution data.
    Returns:
        None
    """
    for axlegroup in ["Enkeltaksler", "Boggiaksler", "Trippelaksler"]:
        dfs = df[df["axlegroup"] == axlegroup]
        weight_columns = [col for col in df.columns if "-" in col]
        dfs = dfs.groupby("location", as_index=False)[weight_columns].sum()
        column_sums = dfs[weight_columns].sum().to_dict()
        sum_row = {"location": "Total", **column_sums}
        updated_df = pd.concat([dfs, pd.DataFrame([sum_row])], ignore_index=True)
        dics = []
        for _, row in updated_df.iterrows():
            sted = row["location"]
            sum_vekt = sum(row[vektspenn] for vektspenn in weight_columns)
            dic = {"Sted": sted} | {
                vektspenn: 100 * row[vektspenn] / sum_vekt if sum_vekt != 0 else 0
                for vektspenn in weight_columns
            }
            dics.append(dic)
        percentage_df = pd.DataFrame(dics)
        percentage_df.to_csv(
            INTERIM_DATA_DIR / f"{axlegroup} axle load distribution.csv", index=False
        )


def group_by_locations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group the total vehicle weight data by location.
    Drops the date-like features.

    Args:
        df (pd.DataFrame): The dataframe containing the total vehicle weight data.
    Returns:
        pd.DataFrame: The grouped dataframe.
    """
    return df.drop(columns=["startdate", "enddate"]).groupby("location").sum()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "features.csv",
    mode: int = 0,
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    if should_run_task(mode, MODE_AXLE_LOAD):
        df_axle_load_distribution = pd.read_csv(RAW_DATA_DIR / "axle load distribution.csv")
        calculate_axle_load_distributions(df_axle_load_distribution)

    if should_run_task(mode, MODE_VEHICLE_WEIGHT_WIM):
        df_total_vehicle_weight = pd.read_csv(RAW_DATA_DIR / "total vehicle weight.csv")
        df_total_vehicle_weight_grouped_by_location = group_by_locations(df_total_vehicle_weight)
        df_total_vehicle_weight_grouped_by_location.to_csv(
            INTERIM_DATA_DIR / "total vehicle weight grouped by location.csv"
        )

    if should_run_task(mode, MODE_VEHICLE_WEIGHT_74T):

        pd.concat(
            [
                pd.read_csv(f, parse_dates=["Dato"], dayfirst=False, sep=";")
                for f in (RAW_DATA_DIR / "vehicle_data_74t").glob("*.csv")
            ],
            ignore_index=True,
        ).sort_values("Dato").to_csv(INTERIM_DATA_DIR / "vehicle weight from 74t.csv", index=False)
    # -----------------------------------------


if __name__ == "__main__":
    app()
