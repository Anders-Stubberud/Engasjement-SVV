import os
import pickle
import math
from io import BytesIO
import time
import folium
import geopandas as gpd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from PIL import Image
from source.config import ESTIMATED_REGISTRATIONS_74T_DIR
from source.config import INTERIM_DATA_DIR
from source.features_dir import estimated_registrations
from source.utils import sanitize_filename


def meters_to_degrees(meters, lat):
    """
    Convert distance in meters to degrees for latitude and longitude. Roughly, close enough.
    """
    lat_degrees = meters / 111320
    lon_degrees = meters / (111320 * math.cos(math.radians(lat)))
    return lat_degrees, lon_degrees


def main(road_coordinates, pickle_path, figures_dir):
    """
    Generate maps for roads with corresponding boundary buffers and save them as PNG images.
    """
    # Create output directory if not exists
    os.makedirs(figures_dir, exist_ok=True)

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    service = FirefoxService(executable_path='/snap/bin/geckodriver')
    driver = webdriver.Firefox(service=service, options=options)

    keys = list(road_coordinates.keys())
    pickle_files = [pickle_path / f"{sanitize_filename(key)}_boundary.pkl" for key in keys]

    # Loop through roads and generate maps
    for key, pickle_file in zip(keys, pickle_files):
        lat, lon = road_coordinates[key]
        lat_buf, lon_buf = meters_to_degrees(
            estimated_registrations.THRESHOLD_METER_REGISTRATION_RADIUS_FROM_COORDINATE_POINT
            + 1000,
            lat,
        )

        zoom = 12 if key == "Fv1900 S1" else 13
        m = folium.Map(location=[lat, lon], zoom_start=zoom)

        # Add polygon buffer area
        buffer_coords = [
            [lat - lat_buf, lon - lon_buf],
            [lat - lat_buf, lon + lon_buf],
            [lat + lat_buf, lon + lon_buf],
            [lat + lat_buf, lon - lon_buf],
        ]
        folium.Polygon(
            locations=buffer_coords, color="none", fill=True, tooltip="Buffer Area"
        ).add_to(m)

        # Load boundary from pickle
        with open(pickle_file, "rb") as f:
            boundary = pickle.load(f)

        # Ensure boundary is a GeoDataFrame
        boundary_gdf = gpd.GeoDataFrame(geometry=[boundary], crs="EPSG:4326") if not isinstance(boundary, gpd.GeoDataFrame) else boundary

        # Add boundary as GeoJSON
        folium.GeoJson(
            boundary_gdf,
            name="Boundary",
            style_function=lambda x: {"color": "red", "weight": 2, "fillOpacity": 0.2},
        ).add_to(m)

        # Add marker for center point
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>Key:</b> {key}",
            tooltip="Center Point",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

        # Save map to HTML file
        map_html_path = figures_dir / f"{sanitize_filename(key)}.html"
        m.save(map_html_path)

        # Open the HTML file in the headless browser and take a screenshot
        driver.get(f"file://{map_html_path}")
        time.sleep(0.5)
        img_data = driver.get_screenshot_as_png()

        # Save the image
        img = Image.open(BytesIO(img_data))
        img.save(figures_dir / f"{sanitize_filename(key)}.png", "PNG")
        map_html_path.unlink()
    driver.quit()


if __name__ == "__main__":
    main(
        estimated_registrations.ROAD_COORDINATES,
        INTERIM_DATA_DIR / "estimated_registrations" / estimated_registrations.SUBPATH,
        ESTIMATED_REGISTRATIONS_74T_DIR / estimated_registrations.SUBPATH / "figures",
    )
