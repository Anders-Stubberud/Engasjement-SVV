from pathlib import Path

import pandas as pd
import typer

from source.config import PROCESSED_DATA_DIR
from source.config import RAW_DATA_DIR

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----

    ## Data on axle load distributions, calculated from the WIM sensors during the summer job
    pd.read_csv(
        "https://raw.githubusercontent.com/Anders-Stubberud/toianalyser/refs/heads/main/resultater/aksellastfordeling.csv"
    ).to_csv(RAW_DATA_DIR / "axle load distribution.csv", index=False)

    # -----------------------------------------


if __name__ == "__main__":
    app()
