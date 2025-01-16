import math
import os
import pickle
from io import BytesIO

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image

from source.config import ESTIMATED_REGISTRATIONS_74T_FIGURES_DIR
from source.config import INTERIM_DATA_DIR, ESTIMATED_REGISTRATIONS_74T_DIR
from source.features_dir import estimated_registrations


def meters_to_degrees(meters, lat):
    """
    Convert distance in meters to degrees for latitude and longitude. Roughly, close enough.
    """
    lat_degrees = meters / 111320
    lon_degrees = meters / (111320 * math.cos(math.radians(lat)))
    return lat_degrees, lon_degrees


def main(road_coordinates, pickle_path, figures_dir):
    """
    Bruker veger og koordinater fra road_coords til å generere kart med det tilhørende polygon-bufferet fra pickel_path.
    Lagrer kartet som en png-fil i figures_dir/vegnavn.png.

    Parameters:
        road_coordinates (dict): A dictionary where keys are road identifiers and values are coordinate points.
        pickle_path (Path): Path to the directory containing pickle files with boundary data.
        figures_dir (Path): Directory where the generated figures will be saved.
    Returns:
        None
    """


    # Retrieve coordinate keys and pickle files
    keys = list(road_coordinates.keys())
    pickle_files = [
        pickle_path / f"{key}_boundary.pkl" for key in keys
    ]

    # Loop through keys and pickle files
    for key, pickle_file in zip(keys, pickle_files):
        # Get coordinates and buffer dimensions
        lat, lon = road_coordinates[key]
        lat_buf, lon_buf = meters_to_degrees(
            estimated_registrations.THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT
            + 1000,
            lat,
        )

        if key == "Fv1900 S1":
            zoom = 12
        else:
            zoom = 13

        m = folium.Map(location=[lat, lon], zoom_start=zoom)

        # Add the buffer area as a polygon
        buffer_coords = [
            [lat - lat_buf, lon - lon_buf],
            [lat - lat_buf, lon + lon_buf],
            [lat + lat_buf, lon + lon_buf],
            [lat + lat_buf, lon - lon_buf],
        ]
        folium.Polygon(
            locations=buffer_coords, color="none", fill=True, tooltip="Buffer Area"
        ).add_to(m)

        # Load the boundary from the pickle file
        with open(pickle_file, "rb") as f:
            boundary = pickle.load(f)

        # If the boundary is a GeoDataFrame, use it directly, otherwise create one
        if isinstance(boundary, gpd.GeoDataFrame):
            boundary_gdf = boundary
        else:
            boundary_gdf = gpd.GeoDataFrame(geometry=[boundary], crs="EPSG:4326")

        # Add the boundary as a GeoJSON layer to the map
        folium.GeoJson(
            boundary_gdf,
            name="Boundary",
            style_function=lambda x: {"color": "red", "weight": 2, "fillOpacity": 0.2},
        ).add_to(m)

        # Add a marker for the center point
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>Key:</b> {key}",
            tooltip="Center Point",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

        img_data = m._to_png(5)  # 5 for higher DPI

        os.makedirs(figures_dir, exist_ok=True)

        # Open the image data using Pillow
        img = Image.open(BytesIO(img_data))
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.axis("off")
        ax.set_title(f"{key} ({lat}, {lon})")
        ax.imshow(img)
        plt.savefig(
            figures_dir / f"{key}.png",
            format="png",
            bbox_inches="tight",
            pad_inches=0,
            dpi=300,
        )


if __name__ == "__main__":

    main(
        estimated_registrations.ROAD_COORDINATES,
        INTERIM_DATA_DIR / "estimated_registrations" / estimated_registrations.SUBPATH,
        ESTIMATED_REGISTRATIONS_74T_DIR / estimated_registrations.SUBPATH / 'figures',
    )
