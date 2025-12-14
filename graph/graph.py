import math
import pickle
from collections import Counter
from collections.abc import Iterator

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from shapely import MultiPolygon, convex_hull


def get_routes_in_area(gdf: gpd.GeoDataFrame, route_file: str) -> Iterator[tuple[int, gpd.GeoDataFrame]]:
    """Get an iterator of all routes that are at least partially within the area of interest.

    Args:
        gdf (gpd.GeoDataFrame): The gdf for the area of interest.
        route_file (str): The filenmae of the route pickle file.

    Yields:
        Iterator[tuple[int, gpd.GeoDataFrame]]: An iterator that yields route ids and valid routes.
    """
    with open(route_file, "rb") as file:
        routes: dict[int, gpd.GeoDataFrame] = pickle.load(file)

    for route_id, route in routes.items():
        # project route to gdf crs
        route = ox.projection.project_gdf(route, to_crs=gdf.crs)

        # yield routes that intersect the area of interest
        if gdf.sindex.query(route.geometry, predicate="intersects", output_format="dense").any():
            yield route_id, route


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


def graph_to_gdf(G: nx.DiGraph) -> gpd.GeoDataFrame:
    """Convert a graph to a gdf containing both nodes and edges.

    Args:
        G (nx.DiGraph): The input graph.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing all nodes and edges in the graph.
    """
    # convert graph to gdf
    nodes, edges = ox.convert.graph_to_gdfs(nx.MultiDiGraph(G))

    # add radian columns for nodes
    nodes["y_rad"] = np.deg2rad(nodes["y"])
    nodes["x_rad"] = np.deg2rad(nodes["x"])

    # merge nodes and edges
    edges = edges.reset_index()
    gdf = pd.merge(nodes, edges, how="right", left_on="osmid", right_on="u", suffixes=("_node", None))

    # rename columns and keep only necessary ones
    gdf[["geometry", "geometry_edge"]] = gdf[["geometry_node", "geometry"]]
    return gdf[["osmid", "u", "v", "y", "x", "y_rad", "x_rad", "geometry", "geometry_edge", "name", "length"]]


def subgraph_from_gdf_mask(G: nx.DiGraph, gdf: gpd.GeoDataFrame, mask: gpd.GeoSeries, buffer: float) -> nx.DiGraph:
    """Get the subgraph of the given graph found by only including nodes within some buffered distance of the mask.

    Args:
        G (nx.DiGraph): The input graph.
        gdf (gpd.GeoDataFrame): The GeoDataFrame containing the graph nodes. Expects output from `graph.graph_to_gdf`.
        mask (gpd.GeoSeries): The GeoSeries containing the mask geometries.
        buffer (float): The buffer distance to apply to the mask.

    Returns:
        nx.DiGraph: The subgraph containing only the nodes within the buffered mask.
    """
    # buffer mask points and take the union
    mask = mask.buffer(buffer).union_all()

    # if union has multiple unconnected polygons, take convex hull
    if isinstance(mask, MultiPolygon):
        mask = convex_hull(mask)

    # get indices of gdf that intersect mask
    idxs = gdf.sindex.query(mask, predicate="intersects", output_format="dense")

    # use idxs to get list of nodes to keep
    to_keep = gdf.loc[idxs, ["u", "v"]]
    to_keep = np.unique(to_keep.values, sorted=False)

    # remove all nodes not in keep list
    to_remove = [node for node in G.nodes if node not in to_keep]

    # remove from graph and return
    G_sub = G.copy()
    G_sub.remove_nodes_from(to_remove)
    return G_sub


def add_visited_counts(G: nx.DiGraph, route_edges: dict[int, list[tuple[int, int]]]):
    """Add `visited` attribute to all edges in the graph equal to the number of times each edge was traversed across all routes.

    Args:
        G (nx.DiGraph): The input graph.
        route_edges (dict[int, list[tuple[int, int]]]): A dictionary mapping route IDs to lists of edges.
    """
    # count number of times each edge was visited across all routes
    visited_counts = Counter([edge for edges in route_edges.values() for edge in edges])

    # set visited counts for each edge in the graph
    nx.set_edge_attributes(G, 0, "visited")
    nx.set_edge_attributes(G, {edge: math.log10(count) for edge, count in visited_counts.items()}, "visited")


def graph_difference(G: nx.DiGraph, H: nx.DiGraph) -> nx.DiGraph:
    G_diff = G.copy()
    G_diff.remove_edges_from(edge for edge in G.edges if H.has_edge(*edge))
    G_diff.remove_nodes_from(list(nx.isolates(G_diff)))
    return G_diff


def walk_network(G: nx.DiGraph) -> nx.DiGraph:
    G_walk = G.copy()
    G_walk.remove_edges_from(
        (u, v)
        for u, v, highway in G.edges.data("highway")
        if highway not in ["footway", "bridleway", "steps", "corridor", "path"]
    )
