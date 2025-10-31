import pickle
from collections.abc import Iterator

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import LineString, Polygon
from sklearn.neighbors import BallTree


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
        route_line = LineString(zip(route["position_long"], route["position_lat"]))
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


def to_digraph(G: nx.MultiDiGraph, priority: nx.MultiDiGraph = None) -> nx.DiGraph:
    """Convert a MultiDiGraph to a DiGraph, keeping shortest edge, optionally prioritizing edges that also exist in a second MultiDiGraph.

    Args:
        G (nx.MultiDiGraph): The MultiDiGraph to convert.
        priority (nx.MultiDiGraph, optional): The graph containing the edges to prioritize. Defaults to None.

    Returns:
        nx.DiGraph: A DiGraph containing only the shortest edges.
    """
    # make a copy to not mutate original graph object caller passed in
    G = G.copy()
    to_remove: list[tuple[int, int, int]] = []

    # identify all the parallel edges in the MultiDiGraph
    parallels = ((u, v) for u, v in G.edges(keys=False) if G.number_of_edges(u, v) > 1)

    # among all sets of parallel edges, remove all except the one with the min length
    for u, v in set(parallels):
        priority_ids = []

        # if we have a priority graph and it has an edge between u and v, add to list of priority osmids
        if priority and u in priority and v in priority and priority.number_of_edges(u, v) > 0:
            priority_ids = [data["osmid"] for _, _, data in priority.get_edge_data(u, v).items()]

        # get the key of the edge with the min length, ignoring non-priority edges if there are any priority edges
        k_min, _ = min(
            G.get_edge_data(u, v).items(),
            key=lambda x: x[1]["length"] if x[1]["osmid"] in priority_ids or not priority_ids else float("inf"),
        )

        # add all other edges to the removal list
        to_remove.extend((u, v, k) for k in G[u][v] if k != k_min)

    G.remove_edges_from(to_remove)

    return nx.DiGraph(G)


def add_visited_counts(G: nx.DiGraph, route_file: str) -> nx.DiGraph:
    get_balltree(G)
    graph_to_gdf(nx.MultiDiGraph(G))

    # for route in get_routes_in_area(gdf, route_file):


def graph_to_gdf(G: nx.MultiDiGraph) -> gpd.GeoDataFrame:
    """Convert a graph to a gdf containing both nodes and edges.

    Args:
        G (nx.MultiDiGraph): The input graph.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing all nodes and edges in the graph.
    """
    # convert graph to gdf
    nodes, edges = ox.convert.graph_to_gdfs(G)

    # add radian columns for nodes
    nodes["y_rad"] = np.deg2rad(nodes["y"])
    nodes["x_rad"] = np.deg2rad(nodes["x"])

    # merge nodes and edges
    edges = edges.reset_index()
    gdf = pd.merge(nodes, edges, how="right", left_on="osmid", right_on="u", suffixes=("_node", None))

    # rename columns and keep only necessary ones
    gdf[["geometry", "geometry_edge"]] = gdf[["geometry_node", "geometry"]]
    return gdf[["osmid", "u", "v", "y", "x", "y_rad", "x_rad", "geometry", "geometry_edge", "name", "length"]]


def buffer_gdf(gdf: gpd.GeoDataFrame, dist: float) -> gpd.GeoDataFrame:
    gdf_proj = ox.projection.project_gdf(gdf)
    gdf_proj_buff = gdf_proj.buffer(dist)
    gdf_buff = ox.projection.project_gdf(gdf_proj_buff, to_latlong=True)
    return gdf_buff


def get_balltree(G: nx.DiGraph) -> BallTree:
    pass
    # ball = BallTree(nodes[["y_rad", "x_rad"]].to_numpy(), metric="haversine")


def create_trellis(candidates):
    pass
