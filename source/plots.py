from pathlib import Path

import typer

from source.config import FIGURES_DIR
from source.config import MODE_AXLE_LOAD
from source.config import MODE_VEHICLE_WEIGHT_74T
from source.config import MODE_VEHICLE_WEIGHT_WIM
from source.config import PROCESSED_DATA_DIR
from source.plot_scripts import axle_load_w_N200_and_esal
from source.plot_scripts import total_vehicle_weight
from source.plot_scripts import weight_data_74t
from source.utils import should_run_task

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = FIGURES_DIR / "plot.png",
    mode: int = 0,
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----

    ## Crunches out axle load distributions for single, boggi and triple axles, and compares with N200.
    ## Stores the results in the figures dir.
    if should_run_task(mode, MODE_AXLE_LOAD):
        axle_load_w_N200_and_esal.main()

    if should_run_task(mode, MODE_VEHICLE_WEIGHT_WIM):
        total_vehicle_weight.main()

    if should_run_task(mode, MODE_VEHICLE_WEIGHT_74T):
        weight_data_74t.main()
    # -----------------------------------------


if __name__ == "__main__":
    app()
