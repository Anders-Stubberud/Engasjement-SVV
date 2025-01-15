import pandas as pd
from geopy.distance import geodesic
from tqdm import tqdm
import os
from source.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, INTERIM_DATA_DIR

tonnages = (60, 65, 68, 74)
years = range(2021, 2025)

COORDINATE_POINTS_ROADS = { # fant disse med https://vegkart.atlas.vegvesen.no/
    'Fv24 S7': (60.620318692686524, 11.45732868472923), 
    'Fv24 S8': (60.68464568378821, 11.34488939729827), 
    'Fv227 S2': (60.84417394856876, 11.189843853440689), 
    'Fv1796 S2': (60.87926155709279, 11.175477138285103),
    'Fv1798 S2': (60.871887232207996, 11.225880476273057),
    'Fv1820 S1': (60.85597322615382, 11.240456370570067), 
    'Fv1844 S1': (60.82551243698731, 11.322549441663224), 
    'Fv1900 S1': (60.672633328131525, 11.298307776875701),
}

DELTA_LOGGING_SECONDS = 350
THRESHOLD_HIGH_SPEED_KMH = 90
THRESHOLD_SLOW_SPEED_KMH = 26 

THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT = THRESHOLD_HIGH_SPEED_KMH * DELTA_LOGGING_SECONDS / 60**2 / 2
"""
Defines the threshold in kilometers of the radius from the specified coordinate point of a road
for which a vehicle-position-registration is considered to be within the road.
"""

THRESHOLD_HOUR_AVOID_COUNTING_DUPLICATE_REGISTRATIONS = 2 * THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT / THRESHOLD_SLOW_SPEED_KMH
"""
Defines the threshold in hours of which to NOT to count a vehicle-position-registration if another
registration with the same VIN has already been counted within the threshold.
"""

MAP_EQUIPAGE_TO_TONNAGE = {
    '3-akslet trekkvogn med 4-akslet tilhenger': 60,
    '3-akslet trekkvogn med 5-akslet tilhenger': 65,
    '4-akslet trekkvogn med 4-akslet tilhenger': 68,
    '4-akslet trekkvogn med 5-akslet tilhenger': 74,
}

def vins_of_interest(interest):
    df_matching = pd.read_csv(os.path.join(RAW_DATA_DIR /  'estimated_registrations', 'bil_tilhenger_matching.csv'), low_memory=False)
    
    if interest == 'trailer_only':
        VINs_of_interest = df_matching['VIN_tilhenger'].unique().tolist()
    elif interest == 'truck_only':
        VINs_of_interest = df_matching['VIN_lastebil'].unique().tolist()
    else:
        VINs_of_interest = df_matching['VIN_lastebil'].unique().tolist() + df_matching['VIN_tilhenger'].unique().tolist()

    return VINs_of_interest

def vin_to_tonnage(vin):
    df_matching = pd.read_csv(os.path.join(RAW_DATA_DIR /  'estimated_registrations', 'bil_tilhenger_matching.csv'), low_memory=False)
    VIN_to_equipage = df_matching.set_index('VIN_tilhenger')['ekvipasje'].to_dict()
    VIN_to_equipage.update(df_matching.set_index('VIN_lastebil')['ekvipasje'].to_dict())
    VIN_to_equipage = {k: v for k, v in VIN_to_equipage.items() if k in vin}
    return {VIN: MAP_EQUIPAGE_TO_TONNAGE[equipage] for VIN, equipage in VIN_to_equipage.items()}

def process_and_return_df(mode):
    df_2021 = pd.read_csv(os.path.join(RAW_DATA_DIR /  'estimated_registrations', '2021-01-01_2021-12-31.csv'), low_memory=False).head(100)
    df_2022 = pd.read_csv(os.path.join(RAW_DATA_DIR /  'estimated_registrations', '2022-01-01_2022-12-31.csv'), low_memory=False).head(100)
    df_2023 = pd.read_csv(os.path.join(RAW_DATA_DIR /  'estimated_registrations', '2023-01-01_2023-12-31.csv'), low_memory=False).head(100)
    df_2024 = pd.read_csv(os.path.join(RAW_DATA_DIR /  'estimated_registrations', '2024-01-01_2024-07-09.csv'), low_memory=False).head(100)
    merged_df = pd.concat([df_2021, df_2022, df_2023, df_2024], ignore_index=True)

    VINs_of_interest = vins_of_interest(mode)
    VIN_to_tonnage = vin_to_tonnage(VINs_of_interest)

    merged_df = merged_df[merged_df['VIN'].isin(VINs_of_interest)]
    merged_df['Tonnage'] = merged_df['VIN'].map(VIN_to_tonnage)
    merged_df['Hastighet'] = merged_df['Hastighet'].replace(',', '.', regex=True).astype(float)
    merged_df['Dato'] = pd.to_datetime(merged_df['Dato'].str.replace(r'\.\d+$', '', regex=True))

    merged_df = merged_df[['VIN', 'Dato', 'Latitude', 'Longitude', 'Hastighet', 'Tonnage']]
    merged_df.sort_values(by='Dato', inplace=True)

    return merged_df

def table(
    df: pd.DataFrame, 
    road_coordinates: dict[str, tuple[float, float]],
    threshold_radius_km: float, 
    threshold_time_hours: float
) -> pd.DataFrame:
    """
    Generates a table with counts of registrations per road, tonnage, and year based on proximity and time criteria.

    Args:
        df (pd.DataFrame): DataFrame containing VIN, Latitude, Longitude, Date, and Tonnage columns. Sorted by date, ascending.
        road_coordinates (dict): A dictionary mapping road names to (latitude, longitude) tuples.
        threshold_radius_km (float): Maximum distance in kilometers to consider a registration near a road.
        threshold_time_hours (float): Minimum time in hours to avoid counting duplicate registrations.

    Returns:
        pd.DataFrame: A summary DataFrame with counts of registrations per road, year, and tonnage.
    """

    df['Dato'] = pd.to_datetime(df['Dato'])

    columns = [
        "Vei", 
        *[f"{year} {tonnage}t" for year in years for tonnage in tonnages]
    ]

    result = {col: [] for col in columns}

    VINs = df["VIN"].unique().tolist()

    for road, (road_lat, road_lon) in road_coordinates.items():
        most_recent_entry = {VIN: None for VIN in VINs}
        road_counts = {f"{year} {tonnage}t": 0 for year in years for tonnage in tonnages}

        for _, entry in df.iterrows():
            entry_coords = (entry["Latitude"], entry["Longitude"])
            distance = geodesic(entry_coords, (road_lat, road_lon)).km

            if distance <= threshold_radius_km: # denne 
                VIN = entry["VIN"]
                entry_time = entry["Dato"]

                if most_recent_entry[VIN] is None or (entry_time - most_recent_entry[VIN]).total_seconds() / 3600 > threshold_time_hours:
                    most_recent_entry[VIN] = entry_time

                    year = entry["Dato"].year
                    tonnage = entry["Tonnage"]
                    key = f"{year} {tonnage}t"
                    if key in road_counts:
                        road_counts[key] += 1

        result["Vei"].append(road)
        for key, value in road_counts.items():
            result[key].append(value)

    return pd.DataFrame(result)

def main():
    for mode in tqdm(['trailer_only', 'truck_only'], desc="Processing modes"):
        df = process_and_return_df(mode)
        df.to_csv(f'{INTERIM_DATA_DIR / 'estimated_registrations'}/processed-{mode}.csv', index=False)

        """
        Creating registration table
        """
        df = pd.read_csv(f'{INTERIM_DATA_DIR / 'estimated_registrations'}/processed-{mode}.csv')
        df_table = table(
            df, 
            road_coordinates=COORDINATE_POINTS_ROADS, 
            threshold_radius_km=THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT, 
            threshold_time_hours=THRESHOLD_HOUR_AVOID_COUNTING_DUPLICATE_REGISTRATIONS
        )
        
        df_table.to_csv(f'{PROCESSED_DATA_DIR / 'estimated_registrations'}/final-{mode}.csv', index=False)

if __name__ == "__main__":
    main()
