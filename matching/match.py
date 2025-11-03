import math
from collections import defaultdict, deque

import networkx as nx
import pandas as pd
from shapely import distance

from matching.candidate import Candidate


class Matcher:
    SIGMA_Z = 4.07
    BETA = 3

    def __init__(self, matched_routes: dict[int, dict[int, int]] = None, beta: float = None, sigma: float = None):
        """Initialize a matcher object.

        Args:
            matched_routes (dict[int, dict[int, int]], optional): A dictionary of previously computed matched routes. Defaults to None.
            beta (float, optional): Satandard deviation of Gaussian GPS noise. Defaults to None.
            sigma (float, optional): Robust estimator of difference between route distance and great circle distances. Defaults to None.
        """
        self.beta = beta or self.BETA
        self.sigma = sigma or self.SIGMA_Z

        self.c_emission = 1 / (self.sigma * math.sqrt(2 * math.pi))
        self.known_dists = defaultdict(dict)
        self.matched_routes = matched_routes or {}

    @staticmethod
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
                node_names,
                candidates.u,
                candidates.osmid,
                candidates.geometry_obs,
                candidates.dist,
                candidates.geometry,
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

    def viterbi_search(self, G: nx.DiGraph, trellis: nx.DiGraph, start="start", target="target") -> dict[str, str]:
        """Compute Viterbi search on the trellis graph to find most probable path.

        Args:
            G (nx.DiGraph): Street network graph.
            trellis (nx.DiGraph): Trellis graph of candidate points.
            start (str, optional): Name of the start node. Defaults to "start".
            target (str, optional): Name of the target node. Defaults to "target".

        Returns:
            dict[str, str]: Mapping of each node to its predecessor in the most probable path.
        """
        # initialize joint probabilities and predecessors
        joint_prob = defaultdict(lambda: -float("inf"))
        predecessor = {}
        predecessor_val = {}

        # initialize queue
        queue = deque()
        queue.append(start)

        # set start node probability and predecessor
        joint_prob[start] = 0  # log(1), save the emission_prob computation
        predecessor[start] = None

        # initialize gap count
        gap_count = 0

        u_name = "start"
        while queue:
            # extract node u
            u_name = queue.popleft()
            u = trellis.nodes[u_name]["candidate"]

            # stop when we reach target
            if u_name == target:
                break

            # iterate through u's successors
            for v_name in list(trellis.successors(u_name)):
                # extract node v
                v = trellis.nodes[v_name]["candidate"]

                # compute new joint probability
                try:
                    new_prob = joint_prob[u_name] + self.emission_prob(v) + self.transition_prob(G, u, v)
                except nx.NetworkXNoPath:
                    # if not reachable, set new_prob to negative infinity
                    new_prob = -float("inf")

                # update v's joint probability if new_prob is higher
                if new_prob > joint_prob[v_name]:
                    joint_prob[v_name] = new_prob

                    # replace v's predecessor if not set or new_prob is higher than current value
                    if v_name not in predecessor or new_prob > predecessor_val[v_name]:
                        predecessor[v_name] = u_name
                        predecessor_val[v_name] = new_prob

                # add v to queue if not already present and is reachable
                if v_name not in queue and new_prob > -float("inf"):
                    queue.append(v_name)
            # end for

            # if queue is empty (ie, no nodes in next level reachable from this one)
            if not queue:
                # insert gap node between current and next level
                self.insert_gap_between(u_name, v_name, trellis, gap_count)

                gap_node = f"gap_{gap_count}"
                if gap_node in trellis.successors(u_name):
                    # if we added a gap node, add all reachable current level nodes to queue and increment gap count
                    queue.extend(node for node in trellis.predecessors(gap_node) if node in predecessor)
                    gap_count += 1
                else:
                    # otherwise, our current node is already a gap node, so just add it back to the queue
                    queue.append(u_name)
        # end while

        # keep only predecessors that lead to target
        preds = self.get_predecessor_chain(target, predecessor)

        return preds

    def get_path_edges(
        self, G: nx.DiGraph, trellis: nx.DiGraph, predecessor: dict[str, str], route_id: int = None
    ) -> list[tuple[int, int]]:
        """Create a list of edges in the street network graph that best match the actual GPS data.

        Args:
            G (nx.DiGraph): The street network graph.
            trellis (nx.DiGraph): The trellis graph.
            predecessor (dict[str, str]): Mapping of each node to its predecessor in the most probable path. Expects the output of `viterbi_search`.
            route_id (int, optional): The ID of the route being matched. Defaults to None.

        Returns:
            list[tuple[int, int]]: A list of edges that best match the actual GPS data.
        """
        # get list of nodes in trellis predecessor path
        u_name = list(reversed(predecessor.values()))

        # convert node list to edge list
        path = [(u_name, v_name) for u_name, v_name in zip(u_name, u_name[1:])]

        paths = []
        for u_name, v_name in path:
            # ignore edges involving gap nodes
            if u_name.startswith("gap") or v_name.startswith("gap"):
                continue

            u = trellis.nodes[u_name]["candidate"]
            v = trellis.nodes[v_name]["candidate"]

            # find shortest path between u and v in G
            paths.append(nx.shortest_path(G, u.node_id, v.node_id, weight="length"))

        # drop all single-node paths
        paths = [path for path in paths if len(path) > 1]

        # convert path list to edge list
        edges = [(u, v) for path in paths for u, v in zip(path, path[1:])]

        if route_id is not None:
            # store matched route edges
            self.matched_routes[route_id] = edges

        return edges

    @staticmethod
    def get_predecessor_chain(target: str, predecessor: dict[str, str]) -> dict[str, str]:
        """Get the chain of predecessors leading to the target node.

        Args:
            target (str): The target node.
            predecessor (dict[str, str]): A mapping of each node to its predecessor.

        Returns:
            dict[str, str]: A mapping of each node in the chain to its predecessor.
        """
        pred_chain = {}
        pred = predecessor[target]

        while pred != "start":
            # use full name for gap nodes, otherwise use only level prefix
            if target.startswith("gap"):
                pred_chain[target] = pred
            else:
                pred_chain[target.split("_")[0]] = pred

            # step back one level
            target = pred
            pred = predecessor[target]

        return pred_chain

    def emission_prob(self, u: Candidate) -> float:
        """Compute emission probability of a node.

        Args:
            u (Candidate): Node to calculate emission probability fo.

        Raises:
            ValueError: If there is a problem with the probability calculation that is not a math domain error.

        Returns:
            float: Emission probability of the node.
        """
        # if no great_dist, prob = 1, log(prob) = 0
        if not u.great_dist:
            return 0

        # emission probability calculated from Gaussian distribution
        try:
            return math.log10(self.c_emission * math.exp(-((u.great_dist / self.sigma) ** 2)))
        except ValueError as err:
            if err.args[0] == "math domain error":
                return -float("inf")
            else:
                raise err

    def transition_prob(self, G: nx.DiGraph, u: Candidate, v: Candidate) -> float:
        """Compute transition probability between node u and v.

        Args:
            G (nx.DiGraph): The street network graph containing the nodes.
            u (Candidate): The starting node.
            v (Candidate): The target node.

        Raises:
            nx.NetworkXNoPath: If no path exists between u and v.
            ValueError: If there is a problem with the probability calculation that is not a math domain error.

        Returns:
            float: Transition probability between the nodes.
        """
        # if either candidate has no great_dist, prob = 1, log(prob) = 0
        if not u.great_dist or not v.great_dist:
            return 0

        # sort u and v by node_id to avoid duplicate calculations
        u, v = sorted([u, v], key=lambda x: x.node_id)

        # correct matches will have approximately equal shortest path distance and great-circle distance
        try:
            delta = self.shortest_path_dist(G, u.node_id, v.node_id) - distance(u.coord, v.coord)
        except TypeError as err:
            # if shortest path returns None, no path exists between u and v
            raise nx.NetworkXNoPath(f"No path between {u.node_id} and {v.node_id}.") from err

        # distribution of delta is exponential
        c = 1 / self.beta
        try:
            return math.log10(c * math.exp(-abs(delta) / self.beta))
        except ValueError as err:
            if err.args[0] == "math domain error":
                return -float("inf")
            else:
                raise err

    def shortest_path_dist(self, G: nx.DiGraph, source: str, target: str) -> float | None:
        """Return the length of the shortest path between source and target, caching results.

        Args:
            G (nx.DiGraph): The graph containing the nodes.
            source (str): The start node for the path.
            target (str): The end node for the path. Search is halted when this node is reached.

        Returns:
            float | None: The length of the shortest path between source and target, or None if no path exists.
        """
        # if we have already computed this shortest path, return it
        if target in self.known_dists[source]:
            return self.known_dists[source][target]

        # set the weight function and path dictionary
        weight = nx.algorithms.shortest_paths.weighted._weight_function(G, "length")
        paths = {source: [source]}

        # run Dijkstra's algorithm to compute shortest paths and distances from source to target
        dist = nx.algorithms.shortest_paths.weighted._dijkstra(G, source, weight, paths=paths, target=target)

        # iterate over all paths found, starting with longest
        for v, path in reversed(paths.items()):
            # calculate shortest path distance to last node in path if not already computed
            if v not in dist:
                dist[v] = sum(weight(path[i], path[i + 1], G[path[i]][path[i + 1]]) for i in range(len(path) - 1))

            # iterate over all nodes in path
            for idx, u in enumerate(path):
                # calculate shortest path distance to predecessor if not already computed
                if u not in dist:
                    dist[u] = path[idx - 1] + weight(path[idx - 1], u, G[path[idx - 1]][u])

                # sort u and v to avoid duplicate calculations
                u, v = sorted([u, v])

                # if u-v distance known, also known for all remaining nodes in path
                if v in self.known_dists[u]:
                    break

                # store shortest path distance between u and v
                self.known_dists[u][v] = dist[v] - dist[u]
        # end for

        # if target is reachable from source, return shortest path distance
        if target in self.known_dists[source]:
            return self.known_dists[source][target]

        # otherwise, set shortest path distance to None for all u-target pairs
        for u in dist.keys():
            if u < target:
                self.known_dists[u][target] = None
            else:
                self.known_dists[target][u] = None

        # return shortest path distance (which is None in this case)
        return self.known_dists[source][target]

    @staticmethod
    def insert_gap_between(u: str, v: str, trellis: nx.DiGraph, gap: int):
        """Insert a gap node between the layer containing u and the layer containing v in the trellis.

        Args:
            u (str): The tail node name.
            v (str): The head node name.
            trellis (nx.DiGraph): The trellis graph.
            gap (int): The number of gaps inserted so far.
        """
        # if u already a gap, add edges from u to all v's successors
        if u.startswith("gap") or u == "start":
            for w_name in trellis.successors(v):
                trellis.add_edge(u, w_name)
            return

        # otherwise, create new gap node
        trellis.add_node(f"gap_{gap}", candidate=Candidate("gap", None, None, None, None))

        # add edge from gap node to all nodes at same level as v
        for v in trellis.successors(u):
            trellis.add_edge(f"gap_{gap}", v)

        # add edge from all nodes at same level as u to gap node
        level_prefix = u.split("_")[0] + "_"
        for u in (n for n in trellis if n.startswith(level_prefix)):
            trellis.add_edge(u, f"gap_{gap}")
