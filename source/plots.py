from pathlib import Path

import typer

from source.config import FIGURES_DIR
from source.config import PROCESSED_DATA_DIR
from source.plot_scripts import axle_load_w_N200_and_esal
from source.plot_scripts import total_vehicle_weight

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = FIGURES_DIR / "plot.png",
    # -----------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----

    ## Crunches out axle load distributions for single, boggi and triple axles, and compares with N200.
    ## Stores the results in the figures dir.
    axle_load_w_N200_and_esal.main()

    total_vehicle_weight.main()
    # -----------------------------------------


if __name__ == "__main__":
    app()
