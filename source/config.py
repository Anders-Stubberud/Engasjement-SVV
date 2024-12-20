from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Constants
Axle_load_distribution_10_ton_road_percentage_N200 = {
    "0-1 tonn": 4,
    "1-2 tonn": 8,
    "2-3 tonn": 11,
    "3-4 tonn": 14,
    "4-5 tonn": 11,
    "5-6 tonn": 10,
    "6-7 tonn": 9,
    "7-8 tonn": 8,
    "8-9 tonn": 7,
    "9-10 tonn": 6.5,
    "10-11 tonn": 5.5,
    "11-12 tonn": 3.5,
    "12-13 tonn": 1.6,
    "13-14 tonn": 0.6,
    "14-15 tonn": 0.3,
}

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
