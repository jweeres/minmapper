import logging

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely import Polygon, union_all
from shapely.validation import make_valid


def download_cs_graph(place: str, logger: str = None) -> tuple[nx.MultiDiGraph, gpd.GeoDataFrame]:
    """Download the citystrides graph for the given location.

    Args:
        place (str): The name of the city/location to download the graph for.
        logger (str, optional): The name of the logger to use. Defaults to None.

    Returns:
        nx.MultiDiGraph: The downloaded citystrides graph.
        gpd.GeoDataFrame: The geodataframe of the location boundary.
    """
    logger = logging.getLogger(logger)
    logger.info(f"Downloading graph for {place}...")

    # can go either way on all path types (we're not a car!)
    ox.settings.bidirectional_network_types = ["all"]
    ox.settings.useful_tags_way = ox.settings.useful_tags_way + [
        "footway",
        "sidewalk",
        "street",
        "foot",
        "disused",
        "crossing",
    ]

    G = nx.MultiDiGraph()
    gdf = gpd.GeoDataFrame()

    for filter in get_filters():
        logger.info(f"Using filter: {filter}")

        # download the graph for this filter
        try:
            if place == "Sunshine Hills":
                if gdf.empty:
                    H, gdf = download_polygon_graph(place, filter, True)
                else:
                    H, _ = download_polygon_graph(place, filter)
            else:
                H = ox.graph_from_place(
                    place,
                    retain_all=True,
                    truncate_by_edge=True,
                    custom_filter=filter,
                    simplify=False,
                )

                if gdf.empty:
                    gdf = ox.geocode_to_gdf(place)
            logger.info(f"Downloaded subgraph with {len(H.nodes)} nodes and {len(H.edges)} edges.")
        except ox._errors.InsufficientResponseError:
            logger.warning(f"Could not download data for filter: {filter}")
            continue

        # compose with existing graph
        G = nx.compose(G, H)

    logger.info(f"Downloaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
    return G, gdf


def download_polygon_graph(
    place: str, filter: str, get_gdf: bool = False
) -> tuple[nx.MultiDiGraph, gpd.GeoDataFrame | None]:
    """Download a citystrides graph, and optionally its gdf, using a hardcoded polygon.

    Args:
        place (str): The location to download the graph for. Valid values are: "Sunshine Hills".
        filter (str): The custom filter to use for downloading the graph.
        get_gdf (bool, optional): Whether to return the gdf of the polygon used. Defaults to False.

    Raises:
        ValueError: If an invalid location is passed.

    Returns:
        nx.MultiDiGraph: The downloaded citystrides graph.
        gpd.GeoDataFrame | None: The gdf of the polygon used, if requested.
    """
    if place == "Sunshine Hills":
        polygon = Polygon(
            (
                (-122.9186029, 49.1339211),
                (-122.9182107, 49.1339005),
                (-122.9173290, 49.1339171),
                (-122.9103271, 49.1339019),
                (-122.9035110, 49.1339256),
                (-122.8936911, 49.1340445),
                (-122.8936357, 49.1303340),
                (-122.8903685, 49.1303445),
                (-122.8904716, 49.1192825),
                (-122.8977329, 49.1194226),
                (-122.9002307, 49.1190351),
                (-122.9042114, 49.1190365),
                (-122.9076843, 49.1188845),
                (-122.9154025, 49.1187948),
                (-122.9159985, 49.1188319),
                (-122.9176966, 49.1191495),
                (-122.9182936, 49.1176611),
                (-122.9218904, 49.1175943),
                (-122.9219042, 49.1190088),
                (-122.9233853, 49.1189902),
                (-122.9236629, 49.1229190),
                (-122.9209377, 49.1276241),
            )
        )
    else:
        raise ValueError(f"Polygon graph download not supported for {place}.")

    G = ox.graph.graph_from_polygon(
        make_valid(polygon),
        retain_all=True,
        truncate_by_edge=True,
        custom_filter=filter,
        simplify=False,
    )

    if get_gdf:
        # create gdf from polygon
        gdf = {
            "geometry": [polygon],
            "bbox_west": [G.nodes[min(G.nodes, key=lambda node: G.nodes[node]["x"])]["x"]],
            "bbox_south": [G.nodes[min(G.nodes, key=lambda node: G.nodes[node]["y"])]["y"]],
            "bbox_east": [G.nodes[max(G.nodes, key=lambda node: G.nodes[node]["x"])]["x"]],
            "bbox_north": [G.nodes[max(G.nodes, key=lambda node: G.nodes[node]["y"])]["y"]],
            "name": [place],
        }
        gdf = gpd.GeoDataFrame(gdf, crs="EPSG:4326")

        return G, gdf

    return G, None


def download_walk_graph(gdf: gpd.GeoDataFrame, logger: str = None) -> tuple[nx.MultiDiGraph, gpd.GeoDataFrame]:
    """Download the graph of all valid walking paths within 1 km of city.

    Args:
        gdf (gpd.GeoDataFrame): The gdf of the city area.
        logger (str, optional): The name of the logger to use. Defaults to None.

    Returns:
        nx.MultiDiGraph: The downloaded citystrides graph.
        gpd.GeoDataFrame | None: The gdf of the polygon used, if requested.
    """
    logger = logging.getLogger(logger)
    logger.info(f"Downloading walking graph for {gdf.name.iloc[0]}...")

    # can go either way on all path types (we're not a car!)
    ox.settings.bidirectional_network_types = ["all"]

    # get the list of polygons from the gdf
    try:
        geoms = gdf.geometry.iloc[0].geoms
    except AttributeError:
        geoms = [gdf.geometry.iloc[0]]

    # buffer each polygon by 1km
    geoms = [ox.utils_geo.buffer_geometry(geom, 1000) for geom in geoms]

    # join polygons together
    polygon = union_all(geoms)

    G = nx.MultiDiGraph()
    for filter in get_filters("walk"):
        logger.info(f"Using filter: {filter}")

        # download the graph for this filter
        try:
            # using a relaxed cs filter
            H = ox.graph.graph_from_polygon(
                make_valid(polygon),
                retain_all=True,
                truncate_by_edge=True,
                custom_filter=filter,
                simplify=False,
            )
            logger.info(f"Downloaded roadway subgraph with {len(H.nodes)} nodes and {len(H.edges)} edges.")

            # using osmnx's default walk filter
            H2 = ox.graph.graph_from_polygon(
                make_valid(polygon),
                network_type="walk",
                retain_all=True,
                truncate_by_edge=True,
                simplify=False,
            )
            logger.info(f"Downloaded walking subgraph with {len(H2.nodes)} nodes and {len(H2.edges)} edges.")

            # combine both graphs
            H = nx.compose(H, H2)
            logger.info(f"Combined subgraph has {len(H.nodes)} nodes and {len(H.edges)} edges.")
        except ValueError:
            logger.warning(f"Could not download data for filter: {filter}")
            continue

        # compose with existing graph
        G = nx.compose(G, H)

    # create gdf from polygon
    gdf = {
        "geometry": [polygon],
        "bbox_west": [G.nodes[min(G.nodes, key=lambda node: G.nodes[node]["x"])]["x"]],
        "bbox_south": [G.nodes[min(G.nodes, key=lambda node: G.nodes[node]["y"])]["y"]],
        "bbox_east": [G.nodes[max(G.nodes, key=lambda node: G.nodes[node]["x"])]["x"]],
        "bbox_north": [G.nodes[max(G.nodes, key=lambda node: G.nodes[node]["y"])]["y"]],
        "name": [f"{gdf.name.iloc[0]} (Walking)"],
    }
    gdf = gpd.GeoDataFrame(gdf, crs="EPSG:4326")

    logger.info(f"Downloaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
    return G, gdf


def get_filters(query_type: str = "cs") -> list[str]:
    """Get the list of custom filters for downloading citystrides graphs.
    Args:
        query_type (str, optional): The type of query to get filters for. Valid options are "cs" and "walk". Defaults to "cs".
    Returns:
        list[str]: The list of custom filters.
    """
    # get our list of filters
    with open(f"{query_type}query.txt", encoding="utf-8") as file:
        queries = file.readlines()

    # separate into filter strings
    queries = [line.strip() for line in queries]
    queries = "".join(queries)
    queries = queries.split(";")[:-1]  # last string will be empty

    return queries
