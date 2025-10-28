import pickle
from collections.abc import Iterator

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import LineString


def get_routes_in_area(gdf: gpd.GeoDataFrame, route_file: str) -> Iterator[pd.DataFrame]:
    """Get an iterator of all routes that are at least partially within the area of interest.

    Args:
        gdf (gpd.GeoDataFrame): The gdf for the area of interest.
        route_file (str): The filenmae of the route pickle file.

    Yields:
        Iterator[pd.DataFrame]: An iterator that yields valid routes.
    """
    with open(route_file, "rb") as file:
        routes: list[pd.DataFrame] = pickle.load(file)

    for i, route in enumerate(routes):
        # quick check: if not in bounding box, skip
        if not in_bbox(route["position_lat"], route["position_long"], gdf.iloc[0]):
            continue

        # check if route intersects geometry of area
        route_line = LineString(zip(route["position_long"].dropna(), route["position_lat"].dropna()))
        if gdf.geometry.iloc[0].intersects(route_line):
            yield route


def in_bbox(lat: pd.Series, lng: pd.Series, gdf_row: pd.Series) -> bool:
    """Returns True if any of the lat-lng pairs are within the bbox bounds of the gdf row.

    Args:
        lat (pd.Series): A Series of latitude points.
        lng (pd.Series): A Series of longitude points.
        gdf_row (pd.Series): A gdf row - must contain `bbox_north`, `bbox_south`, `bbox_east`, and `bbox_west` columns.

    Returns:
        bool: True if any of the lat-lng pairs are within the bbox bounds, False otherwise.
    """
    return (
        lat.between(gdf_row["bbox_south"], gdf_row["bbox_north"]).any()
        and lng.between(gdf_row["bbox_west"], gdf_row["bbox_east"]).any()
    )
