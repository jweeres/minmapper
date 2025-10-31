import networkx as nx
import pandas as pd

from matching.candidate import Candidate


def create_trellis(candidates: pd.DataFrame) -> nx.DiGraph:
    """Create a trellis graph of candidate points for map matching.

    Args:
        candidates (pd.DataFrame): A dataframe containing candidate points, output by `candidate.get_candidate_df`.

    Returns:
        nx.DiGraph: A directed acyclic trellis graph.
    """
    # initialize graph with start and target nodes
    G = nx.DiGraph()
    G.add_node("start", candidate=Candidate("start", None, None, None, None))
    G.add_node("target", candidate=Candidate("target", None, None, None, None))

    # get number of candidates per route point
    idx_counts = candidates["idx"].value_counts(sort=False)

    # node names are route index + unique identifier per candidate
    node_names = [f"{idx}_{j}" for idx, n_cands in idx_counts.items() for j in range(n_cands)]

    # create nodes from names and candidate data
    nodes = [
        (name, {"candidate": Candidate(node_id, edge_osmid, obs, great_dist, coord)})
        for name, node_id, edge_osmid, obs, great_dist, coord in zip(
            node_names, candidates.u, candidates.osmid, candidates.geometry_obs, candidates.dist, candidates.geometry
        )
    ]

    # convert index counts to sums for slicing
    cumsum = [0] + idx_counts.cumsum().to_list()

    # create edges between all candidates of consecutive route points
    edges = [
        (u, v) for i, j, k in zip(cumsum, cumsum[1:], cumsum[2:]) for u in node_names[i:j] for v in node_names[j:k]
    ]

    # connect start and target nodes
    edges.extend([("start", v) for v in node_names[: cumsum[1]]])
    edges.extend([(u, "target") for u in node_names[cumsum[-2] :]])

    # add node and edge lists to graph
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    return G
