import math
import os
import pickle
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import pandas as pd
from geopy.distance import geodesic
from shapely import MultiLineString
from shapely.geometry import Point
from shapely.ops import unary_union
from tqdm import tqdm
import numpy as np

from source.config import INTERIM_DATA_DIR
from source.config import PROCESSED_DATA_DIR
from source.config import RAW_DATA_DIR
from source.config import TESTING_DATA_DIR
from source.utils import sanitize_filename

tonnages = (60, 65, 68, 74)
years = range(2021, 2025)

COORDINATES_TESTING = {
    "Aasvegen": (60.748064, 11.322768),
    "Skytragutua": (60.744695, 11.247904),
}

COORDINATE_POINTS_ROADS = {  # fant disse med https://vegkart.atlas.vegvesen.no/
    "Fv24 S7": (60.620318692686524, 11.45732868472923),
    "Fv24 S8": (60.68464568378821, 11.34488939729827),
    "Fv227 S2": (60.84417394856876, 11.189843853440689),
    "Fv1796 S2": (60.87926155709279, 11.175477138285103),
    "Fv1798 S2": (60.871887232207996, 11.225880476273057),
    "Fv1820 S1": (60.85597322615382, 11.240456370570067),
    "Fv1844 S1": (60.82551243698731, 11.322549441663224),
    "Fv1900 S1": (60.672633328131525, 11.298307776875701),
}

with open(INTERIM_DATA_DIR / "bridges" / "bridge_coordinates.pkl", "rb") as f:
    BRIDGE_COORDINATES = pickle.load(f)

COORDINATES_BWIM_74T = {
    "Sørbryn bru (Svartelva)": (60.790036291522725, 11.298908392781641),
    "Tangensvingen bru (Tangensvingen vest)": (60.88848554945865, 11.570661932248345),
}

##################################################
# region Setup                                   #
ROAD_COORDINATES = COORDINATES_BWIM_74T  #
SUBPATH = "bwim74t"  #
# endregion                                      #
##################################################

DELTA_LOGGING_SECONDS = 350
THRESHOLD_HIGH_SPEED_KMH = 90
THRESHOLD_SLOW_SPEED_KMH = 26

THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT = (
    THRESHOLD_HIGH_SPEED_KMH * DELTA_LOGGING_SECONDS / 60**2 / 2
)
"""
Defines the threshold in kilometers of the radius from the specified coordinate point of a road
for which a vehicle-position-registration is considered to be within the road.
"""

THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT = (
    THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT * 1000
)

THRESHOLD_HOUR_AVOID_COUNTING_DUPLICATE_REGISTRATIONS = (
    2 * THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT / THRESHOLD_SLOW_SPEED_KMH
)
"""
Defines the threshold in hours of which to NOT to count a vehicle-position-registration if another
registration with the same VIN has already been counted within the threshold.
"""

MAP_EQUIPAGE_TO_TONNAGE = {
    "3-akslet trekkvogn med 4-akslet tilhenger": 60,
    "3-akslet trekkvogn med 5-akslet tilhenger": 65,
    "4-akslet trekkvogn med 4-akslet tilhenger": 68,
    "4-akslet trekkvogn med 5-akslet tilhenger": 74,
}


def vins_of_interest(interest):
    df_matching = pd.read_csv(
        os.path.join(RAW_DATA_DIR / "estimated_registrations", "bil_tilhenger_matching.csv"),
        low_memory=False,
    )

    if interest == "trailer_only":
        VINs_of_interest = df_matching["VIN_tilhenger"].unique().tolist()
    elif interest == "truck_only":
        VINs_of_interest = df_matching["VIN_lastebil"].unique().tolist()
    else:
        VINs_of_interest = (
            df_matching["VIN_lastebil"].unique().tolist()
            + df_matching["VIN_tilhenger"].unique().tolist()
        )

    return VINs_of_interest


def vin_to_tonnage(vin):
    df_matching = pd.read_csv(
        os.path.join(RAW_DATA_DIR / "estimated_registrations", "bil_tilhenger_matching.csv"),
        low_memory=False,
    )
    VIN_to_equipage = df_matching.set_index("VIN_tilhenger")["ekvipasje"].to_dict()
    VIN_to_equipage.update(df_matching.set_index("VIN_lastebil")["ekvipasje"].to_dict())
    VIN_to_equipage = {k: v for k, v in VIN_to_equipage.items() if k in vin}
    return {VIN: MAP_EQUIPAGE_TO_TONNAGE[equipage] for VIN, equipage in VIN_to_equipage.items()}


def process_and_save_df(mode):
    output_file = f"{INTERIM_DATA_DIR / 'estimated_registrations'}/processed-{mode}.csv"

    if os.path.exists(output_file):
        os.remove(output_file)

    dfs_paths = [
        os.path.join(RAW_DATA_DIR / "estimated_registrations", "2021-01-01_2021-12-31.csv"),
        os.path.join(RAW_DATA_DIR / "estimated_registrations", "2022-01-01_2022-12-31.csv"),
        os.path.join(RAW_DATA_DIR / "estimated_registrations", "2023-01-01_2023-12-31.csv"),
        os.path.join(RAW_DATA_DIR / "estimated_registrations", "2024-01-01_2024-12-31.csv"),
    ]

    VINs_of_interest = vins_of_interest(mode)
    VIN_to_tonnage = vin_to_tonnage(VINs_of_interest)

    for df_path in dfs_paths:
        df = pd.read_csv(df_path, low_memory=False)
        df = df[df["VIN"].isin(VINs_of_interest)]
        df["Tonnage"] = df["VIN"].map(VIN_to_tonnage)
        df["Hastighet"] = df["Hastighet"].replace(",", ".", regex=True).astype(float)
        df["Dato"] = pd.to_datetime(df["Dato"].str.replace(r"\.\d+$", "", regex=True))
        df = df[["VIN", "Dato", "Latitude", "Longitude", "Hastighet", "Tonnage"]]
        df.sort_values(by="Dato", inplace=True)
        df.to_csv(output_file, mode="a", header=not os.path.exists(output_file), index=False)


def get_polygon_boundary(lat, lon):

    def meters_to_degrees(meters):
        """
        Convert distance in meters to degrees for latitude and longitude. Roughly, close enough.
        """
        # Conversion for latitude (1 degree latitude ~ 111,320 meters)
        lat_degrees = meters / 111320

        # Conversion for longitude depends on the latitude (1 degree longitude varies)
        lon_degrees = meters / (111320 * math.cos(math.radians(lat)))

        return lat_degrees, lon_degrees

    def get_road_characteristics(map):
        return {
            "highway": map.get("highway", "unknown"),
            "lanes": map.get("lanes", "unknown"),
            "maxspeed": map.get("maxspeed", "unknown"),
            "name": map.get("name", "unknown"),
            "oneway": map.get("oneway", "unknown"),
        }

    def get_graph_within_distance(G, lat, lon, max_distance_meters):
        """
        Get a subgraph containing only the edges within a specified distance from a point (lat, lon).

        Args:
            G: The graph representing the road network.
            lat, lon: Coordinates of the point (latitude, longitude).
            max_distance_meters: The maximum distance to search for edges in meters.

        Returns:
            A subgraph containing only the edges within the max distance from the point.
        """
        point = Point(lon, lat)
        nearest_edge = ox.distance.nearest_edges(G, X=lon, Y=lat)
        u, v, key = nearest_edge
        road_characteristics = get_road_characteristics(G[u][v][key])
        edges_within_distance = []
        for u, v, key in G.edges(keys=True):
            cur_road_characteristics = get_road_characteristics(G[u][v][key])
            geometry = G[u][v][key].get("geometry", None)
            distance_from_point = point.distance(geometry) if geometry else math.inf
            if (
                cur_road_characteristics == road_characteristics
                and distance_from_point <= max_distance_meters
            ):
                edges_within_distance.append((u, v, key))

        return G.edge_subgraph(edges_within_distance).copy()

    def filter_edges(road_segment):
        edges = ox.graph_to_gdfs(road_segment, nodes=False)
        filtered_edges = []
        for idx, row in edges.iterrows():
            road_geometry = row["geometry"]
            if road_geometry is not None:

                for geom in (
                    road_geometry.geoms
                    if isinstance(road_geometry, MultiLineString)
                    else [road_geometry]
                ):
                    for coord in geom.coords:
                        road_point = Point(coord[0], coord[1])
                        distance = geodesic((lat, lon), (road_point.y, road_point.x)).meters
                        if distance <= THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT:
                            filtered_edges.append(row)

        return gpd.GeoDataFrame(filtered_edges, crs=edges.crs)

    _, lon_buf = meters_to_degrees(THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT)

    G = ox.graph_from_point((lat, lon), dist=5000, network_type="drive")
    road_segment = get_graph_within_distance(G, lat, lon, lon_buf)

    # veg
    edges = filter_edges(road_segment)

    # punkt
    # coord_point_gpd = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs=edges.crs)

    # buffer
    road_lines = unary_union(edges["geometry"])
    return road_lines.buffer(meters_to_degrees(50)[1])


def load_polygon_boundary_from_file(road, subpath):
    file_path = os.path.join(
        INTERIM_DATA_DIR / "estimated_registrations",
        subpath,
        f"{sanitize_filename(road)}_boundary.pkl",
    )
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            polygon_boundary = pickle.load(f).to_crs("EPSG:4326").geometry.iloc[0]
        return polygon_boundary
    else:
        file_path = os.path.join(
            INTERIM_DATA_DIR / "estimated_registrations",
            subpath,
            f"{road}_boundary.pkl",
        )
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                polygon_boundary = pickle.load(f).to_crs("EPSG:4326").geometry.iloc[0]
            return polygon_boundary
        else:
            file_path = os.path.join(
                TESTING_DATA_DIR
                / "estimated_registrations"
                / f"{sanitize_filename(road)}_boundary.pkl",
            )
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    polygon_boundary = pickle.load(f).to_crs("EPSG:4326").geometry.iloc[0]
                return polygon_boundary
            else:
                raise FileNotFoundError(f"No polygon boundary file found for road: {file_path}")


def filter_points_near_road(
    df: pd.DataFrame, road_lon: float, road_lat: float, radius_km: float = 5
):
    """
    Filters points within a given radius (in km) from a single road location.

    Parameters:
        df (pd.DataFrame): DataFrame with 'Latitude' and 'Longitude' columns.
        road_lon (float): Longitude of the road.
        road_lat (float): Latitude of the road.
        radius_km (float): Radius in kilometers for filtering points.

    Returns:
        pd.DataFrame: Filtered DataFrame with points within the radius.
    """
    # Convert points and road coordinates to radians
    lat1, lon1 = np.radians(road_lat), np.radians(road_lon)
    lat2, lon2 = np.radians(df["Latitude"].values), np.radians(df["Longitude"].values)

    # Compute Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distances = 6371 * c  # Earth's radius in km

    # Filter points within the radius
    df_filtered = df[distances <= radius_km].reset_index(drop=True)
    df_filtered = df_filtered[(df_filtered['Hastighet'] > 40) & (df_filtered['Hastighet'].notna()) & (df_filtered['Hastighet'].notnull())]
    return df_filtered

def table(
    df: pd.DataFrame,
    road_coordinates: dict[str, tuple[float, float]],
    threshold_radius_km: float,
    threshold_time_hours: float,
    subpath: Path,
    valid_dates: tuple[pd.TimedeltaIndex] = None,
) -> pd.DataFrame:
    """
    Generates a table with counts of registrations per road, tonnage, and year based on proximity and time criteria.

    Args:
        df (pd.DataFrame): DataFrame containing VIN, Latitude, Longitude, Date, and Tonnage columns. Sorted by date, ascending.
        road_coordinates (dict): A dictionary mapping road names to (latitude, longitude) tuples.
        threshold_radius_km (float): Maximum distance in kilometers to consider a registration near a road.
        threshold_time_hours (float): Minimum time in hours to avoid counting duplicate registrations.
        subpath (Path): Path to the directory where the polygon boundaries are stored.
        valid_dates (tuple): A tuple of valid dates to consider (BWIM som kun er oppe i perioder). If None, all dates are considered.
    Returns:
        pd.DataFrame: A summary DataFrame with counts of registrations per road, year, and tonnage.
    """
    df["Dato"] = pd.to_datetime(df["Dato"])
    columns = ["Vei", *[f"{year} {tonnage}t" for year in years for tonnage in tonnages]]
    result = {col: [] for col in columns}
    VINs = df["VIN"].unique().tolist()

    for road, (road_lat, road_lon) in tqdm(road_coordinates.items(), desc="Processing roads"):
        most_recent_entry = {VIN: None for VIN in VINs}
        road_counts = {f"{year} {tonnage}t": 0 for year in years for tonnage in tonnages}
        polygon_boundary = load_polygon_boundary_from_file(road, subpath)
        df_relevant = filter_points_near_road(
            df, road_lon, road_lat, radius_km=5
        )
        df_relevant = df_relevant[df_relevant.apply(
            lambda entry: polygon_boundary.contains(Point(entry["Longitude"], entry["Latitude"])), axis=1)
        ]
        df_relevant = df_relevant.sort_values(by="Dato", ascending=True) if len(df_relevant) > 0 else df_relevant
        print(len(df_relevant))
        for _, entry in df_relevant.iterrows():
            VIN = entry["VIN"]
            entry_time = entry["Dato"]
            if (
                most_recent_entry[VIN] is None
                or (entry_time - most_recent_entry[VIN]).total_seconds() / 3600
                > threshold_time_hours
            ):
                most_recent_entry[VIN] = entry_time
                year = entry_time.year
                tonnage = entry["Tonnage"]
                key = f"{year} {tonnage}t"
                if (key in road_counts) and (valid_dates is None or entry_time.date() in valid_dates):
                    road_counts[key] += 1
        result["Vei"].append(road)

        for key, value in road_counts.items():
            result[key].append(value)

    return pd.DataFrame(result)


def make_boundaries_automatically(
    road_coordinates: dict[str, tuple[float, float]], storage: str
) -> None:
    """
    Genererer .pkl filer av polygon's for veiene spesifisert i parameter.
    Lagrer i EPSG:3857.
    Baserer seg på osmnx, som mulig kutter noen av veiene litt kort (burde evt rettes manuelt i ipynb 11.)
    Lagrer file i storage/vegnavn.pkl

    Args:
        road_coordinates (dict[str, tuple[float, float]]): A dictionary where the keys are road identifiers (strings)
        and the values are tuples containing latitude and longitude coordinates (floats).
        storage (str): Path til dir der filene skal lagres.
    Returns:
        None: This function does not return any value. It performs operations to generate boundaries.
    """

    def meters_to_degrees(meters):
        """
        Convert distance in meters to degrees for latitude and longitude. Roughly, close enough.
        """
        # Conversion for latitude (1 degree latitude ~ 111,320 meters)
        lat_degrees = meters / 111320

        # Conversion for longitude depends on the latitude (1 degree longitude varies)
        lon_degrees = meters / (111320 * math.cos(math.radians(lat)))

        return lat_degrees, lon_degrees

    def get_road_characteristics(map):
        return {
            "highway": map.get("highway", "unknown"),
            "lanes": map.get("lanes", "unknown"),
            "maxspeed": map.get("maxspeed", "unknown"),
            "name": map.get("name", "unknown"),
            "oneway": map.get("oneway", "unknown"),
        }

    def get_graph_within_distance(G, lat, lon, max_distance_meters):
        """
        Get a subgraph containing only the edges within a specified distance from a point (lat, lon).

        Args:
            G: The graph representing the road network.
            lat, lon: Coordinates of the point (latitude, longitude).
            max_distance_meters: The maximum distance to search for edges in meters.

        Returns:
            A subgraph containing only the edges within the max distance from the point.
        """
        point = Point(lon, lat)
        nearest_edge = ox.distance.nearest_edges(G, X=lon, Y=lat)
        u, v, key = nearest_edge
        road_characteristics = get_road_characteristics(G[u][v][key])
        edges_within_distance = []
        for u, v, key in G.edges(keys=True):
            cur_road_characteristics = get_road_characteristics(G[u][v][key])
            geometry = G[u][v][key].get("geometry", None)
            distance_from_point = point.distance(geometry) if geometry else math.inf
            if (
                cur_road_characteristics == road_characteristics
                and distance_from_point <= max_distance_meters
            ):
                edges_within_distance.append((u, v, key))

        return G.edge_subgraph(edges_within_distance).copy()

    def filter_edges(road_segment):
        edges = ox.graph_to_gdfs(road_segment, nodes=False)
        filtered_edges = []
        for idx, row in edges.iterrows():
            road_geometry = row["geometry"]
            if road_geometry is not None:
                for geom in (
                    road_geometry.geoms
                    if isinstance(road_geometry, MultiLineString)
                    else [road_geometry]
                ):
                    for coord in geom.coords:
                        road_point = Point(coord[0], coord[1])
                        distance = geodesic((lat, lon), (road_point.y, road_point.x)).meters
                        if distance <= THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT:
                            filtered_edges.append(row)

        return gpd.GeoDataFrame(filtered_edges, crs=edges.crs)

    for road, (lat, lon) in road_coordinates.items():

        lat_buf, lon_buf = meters_to_degrees(
            THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT
        )

        G = ox.graph_from_point((lat, lon), dist=10000, network_type="drive")
        road_segment = get_graph_within_distance(G, lat, lon, lon_buf)

        # veg
        edges = filter_edges(road_segment)

        # punkt
        coord_point_gpd = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs=edges.crs)

        # buffer
        road_lines = unary_union(edges["geometry"])
        buffered_polygon = road_lines.buffer(meters_to_degrees(50)[1])
        buffer_gdf = gpd.GeoDataFrame(geometry=[buffered_polygon], crs=edges.crs).to_crs(
            "EPSG:3857"
        )

        os.makedirs(storage, exist_ok=True)

        with open(storage / f"{sanitize_filename(road)}_boundary.pkl", "wb") as f:
            pickle.dump(buffer_gdf, f)


def main(
    road_coordinates,
    testing=False,
    subpath="testing",
    testfile="input.csv",
    testoutput="output.csv",
):
    # for mode in ["trailer_only", "truck_only"]:
    for mode in ["truck_only"]:


        # process_and_save_df(mode)

        df = (
            pd.read_csv(f"{INTERIM_DATA_DIR / 'estimated_registrations'}/processed-{mode}.csv")
            if not testing
            else pd.read_csv(f"{TESTING_DATA_DIR / 'estimated_registrations' / testfile}")
        )

        df_table = table(
            df,
            road_coordinates=road_coordinates,
            threshold_radius_km=THRESHOLD_KM_REGISTRATION_RADIUS_FROM_COORDINATE_POINT,
            threshold_time_hours=THRESHOLD_HOUR_AVOID_COUNTING_DUPLICATE_REGISTRATIONS,
            subpath=subpath,
        )

        output_file = (
            PROCESSED_DATA_DIR / "estimated_registrations" / subpath / f"final-{mode}.csv"
            if not testing
            else f"{TESTING_DATA_DIR / 'estimated_registrations' / testoutput}"
        )

        os.makedirs(Path(output_file).parent, exist_ok=True)

        df_table.to_csv(output_file, index=False)

        if testing:
            break


if __name__ == "__main__":

    # make_boundaries_automatically(
    #     road_coordinates=ROAD_COORDINATES,
    #     storage=INTERIM_DATA_DIR / "estimated_registrations" / SUBPATH,
    # )

    main(ROAD_COORDINATES, subpath=SUBPATH)
