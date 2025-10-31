from typing import NamedTuple

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import Polygon


class Candidate(NamedTuple):
    node_id: str
    edge_osmid: str
    obs: tuple
    great_dist: float
    coord: tuple


def get_candidate_idxs(gdf: gpd.GeoDataFrame, boundary: Polygon, route: pd.DataFrame, radius: float) -> pd.DataFrame:
    """Get dataframe of all candidate indices for each route point index.

    Args:
        gdf (gpd.GeoDataFrame): The gdf containing candidate points.
        boundary (Polygon): The boundary polygon of the area of interest.
        route (pd.DataFrame): A dataframe containing "position_lat" and "position_long" columns.
        radius (float): The maximum distance between a route point and a potential candidate.

    Raises:
        ValueError: If the gdf is unprojected.
        ValueError: If the boundary polygon does not contain most of the points in the gdf.

    Returns:
        pd.DataFrame: A dataframe containing the route and candidate indices.
    """
    # check if gdf is projected
    if not gdf.crs.is_projected:
        raise ValueError("gdf must be in a projected coordinate reference system")

    # check if boundary contains most of gdf points
    if gdf.sindex.query(boundary, predicate="intersects", output_format="dense").sum() < len(gdf) * 0.9:
        raise ValueError("May gdf points not contained within the boundary. Did you forget to project it?")

    # convert route df to gdf and project
    route = gpd.GeoDataFrame(
        route, geometry=gpd.points_from_xy(route["position_long"], route["position_lat"]), crs="EPSG:4326"
    )
    route = ox.projection.project_gdf(route)

    # create mask of all route points within boundary
    within_bounds = route.sindex.query(boundary, predicate="intersects", output_format="dense")

    # restrict route to points within bounds and create ignore mask
    sub_route = route[within_bounds]
    ignore_point = ~within_bounds.flatten()

    idx_list = []

    while not ignore_point.all():
        # find indices of all candidate points within radius of each subroute point
        found_idxs = gdf.sindex.query(sub_route.geometry, predicate="dwithin", distance=radius)

        # convert subroute indices to original route indices and add to list of matches
        found_idxs[0] = route.index.get_indexer(sub_route.index[found_idxs[0]])
        idx_list.append(found_idxs)

        # update ignore mask and subroute for next iteration
        ignore_point = ignore_point | [idx in found_idxs[0] for idx in range(len(route))]
        sub_route = route[~ignore_point]

        # double the search radius and try again
        radius = radius * 2

    # check for points outside bounds that are close enough to have candidates
    found_idxs = gdf.sindex.query(route[~within_bounds].geometry, predicate="dwithin", distance=radius / 2)

    # if any found, convert subroute indices to original route indices and add to list of matches
    if found_idxs.size > 0:
        found_idxs[0] = route.index.get_indexer(route[~within_bounds].index[found_idxs[0]])
        idx_list.append(found_idxs)

    # concatenate indices found in each iteration and return as dataframe
    return pd.DataFrame(np.transpose(np.concatenate(idx_list, axis=1)), columns=["route", "candidate"])
