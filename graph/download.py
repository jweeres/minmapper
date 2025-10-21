import logging

import networkx as nx
import osmnx as ox
from shapely import Polygon
from shapely.validation import make_valid


def download_graph(place: str, logger=None):
    logger = logging.getLogger(logger)
    logger.info(f"Downloading graph for {place}...")

    # can go either way on walking and biking paths
    ox.settings.bidirectional_network_types = ["walk", "bike"]

    # handle our special trial case
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
                (-122.8903550, 49.1340870),
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

    # get our list of filters
    with open("csquery.txt", encoding="utf-8") as file:
        queries = file.readlines()

    # separate into filter strings
    queries = [line.strip() for line in queries]
    queries = "".join(queries)
    queries = queries.split(";")[:-1]  # last string will be empty

    G = nx.MultiDiGraph()
    for filter in queries:
        logger.info(f"Using filter: {filter}")

        # download the graph for this filter
        try:
            if place == "Sunshine Hills":
                H = ox.graph.graph_from_polygon(
                    make_valid(polygon),
                    retain_all=True,
                    truncate_by_edge=True,
                    custom_filter=filter,
                    simplify=False,
                )
            else:
                H = ox.graph_from_place(
                    place,
                    retain_all=True,
                    truncate_by_edge=True,
                    custom_filter=filter,
                    simplify=False,
                )
        except ox._errors.InsufficientResponseError:
            logger.warning(f"Could not download data for filter: {filter}")
            continue

        # compose with existing graph
        G = nx.compose(G, H)
    logger.info(f"Downloaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
