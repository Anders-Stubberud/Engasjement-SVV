from pathlib import Path

import pandas as pd
import typer

from source.config import MODE_AXLE_LOAD
from source.config import MODE_VEHICLE_WEIGHT_WIM
from source.config import PROCESSED_DATA_DIR
from source.config import RAW_DATA_DIR
from source.utils import should_run_task

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    mode: int = 0,
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----

    ## Data on axle load distributions, calculated from the WIM sensors during the summer job
    if should_run_task(mode, MODE_AXLE_LOAD):
        pd.read_csv(
            "https://raw.githubusercontent.com/Anders-Stubberud/toianalyser/refs/heads/main/resultater/aksellastfordeling.csv"
        ).to_csv(RAW_DATA_DIR / "axle load distribution.csv", index=False)

    ## Data on total vehicle weights, calculated from the WIM sensors during the summer job.
    ## This data comes binned with roughly a 1-ton interval, as a menas not to crunch thourgh all the dataset again.
    ## Even though it is binned, the granularity should still be adequate to display the distribution (which is the main goal here).
    if should_run_task(mode, MODE_VEHICLE_WEIGHT_WIM):
        pd.read_csv(
            "https://raw.githubusercontent.com/Anders-Stubberud/toianalyser/refs/heads/main/resultater/totalvekter.csv"
        ).to_csv(RAW_DATA_DIR / "total vehicle weight.csv", index=False)

    # -----------------------------------------


if __name__ == "__main__":
    app()
