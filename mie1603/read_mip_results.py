import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox
from collections import defaultdict

import generate_instances
import pickle
import pandas as pd
import time

# Read instance graph
C  = pd.read_pickle('instance-jess-min.pkl')
C = nx.DiGraph(C)
edges, lengths = gp.multidict({edge:C.edges[edge]['length'] for edge in C.edges })

len(list(ox.truncate.largest_component(C)))


# Read final graph 
S = pd.read_pickle("sol_graph_instance-jess-min_6000_min_length.pkl")
S = pd.read_pickle("sol_graph_instance-jess-min_15000_test.pkl")

S.edges(data=True)

# Plot graph
pos = nx.spring_layout(S)
plt.figure()
nx.draw(S, pos, with_labels=True, node_color='lightblue', edge_color='gray', arrows=True)
plt.title("Optimal Run")
plt.show()

S = pd.read_pickle("sol_graph_instance-jess-min_5000_min_length.pkl")
# Get total distance
run_length = 0
for edge in S.edges:
    run_length += lengths[edge]*S.edges[edge]['visited']
    # print(edge, lengths[edge])
    # print(edge, S.edges[edge]['visited'])

print(run_length)


# Start node
path = [6813225352]

# Append the first successor from each node into the path list


for i in range(len(list(S))):
    path.append(next(C.successors(path[-1])))

# Path list is the route we're plotting
fig, ax = ox.plot.plot_graph_route(C, route=path)
plt.show()


C  = pd.read_pickle('instance-jess-min.pkl')
# C = nx.DiGraph(C)
# edges, lengths = gp.multidict({edge:C.edges[edge]['length'] for edge in C.edges })

profit = {edge: C.edges[edge]['profit'] for edge in C.edges if C.edges[edge]['profit'] > 0}

C = nx.Graph(C)
components = list(nx.connected_components(C))
for i in components:
    print(len(i))

from collections import deque

with open("sol_graph_instance-jess-min_5000_min_length.pkl", "rb") as file:
    sol = pickle.load(file)

with open("instance-jess-min.pkl", "rb") as file:
    G = pickle.load(file)

from collections import deque



run_length = 0
for edge in S.edges:
    run_length += lengths[edge]*S.edges[edge]['visited']
    # print(edge, lengths[edge])
    print(edge, S.edges[edge]['visited'])

print(run_length)

for edge in S.edges:
    print(edge, )