from pathlib import Path

import pandas as pd
import typer

from source.config import INTERIM_DATA_DIR
from source.config import PROCESSED_DATA_DIR
from source.config import RAW_DATA_DIR

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


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "features.csv",
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    df = pd.read_csv(RAW_DATA_DIR / "axle load distribution.csv")
    calculate_axle_load_distributions(df)
    # -----------------------------------------


if __name__ == "__main__":
    app()
