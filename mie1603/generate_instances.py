import networkx as nx

# H: Runnable paths
# G: City Strides Graph, G \subset H
# R: H with number of passes

n_nodes = 9
nodes = [i for i in range(1, n_nodes+1)]

# h_edge_lst = [(i,j) for i in nodes_lst for j in nodes_lst if j!=i] # all connected

# (node i, node j)
h_edge_lst = [
            (1,2),
            (1,6),
            (1,7),
            (2,3),
            (2,7),
            (2,8),
            (3,4),
            (3,8),
            (4,5),
            (4,8),
            (5,6),
            (5,9),
            (6,7),
            (7,8),
            (7,9),
            (8,9)
            ]

h_edge_lst = h_edge_lst + [tuple(reversed(edge)) for edge in h_edge_lst] # adding reversed direction of edges

# Dictionary of connected nodes
node_dict = {i:{j for _, j in h_edge_lst if _ == i } for i in nodes}

# Random
g_edge_lst = [
            (1,2),
            (1,7),
            (2,3),
            (3,2),
            (3,4),
            (4,5),
            (4,8),
            (5,9),
            (6,1),
            (6,5),
            (7,6),
            (7,8),
            (7,9), 
            (8,7),
            (8,2),
            (8,3),
            (9,7)
            ]

# Force subtours
g_edge_lst = [
            (1,2),
            (1,6),
            (2,1),
            (2,3),
            (3,2),
            (3,4),
            (4,3),
            (4,5),
            (5,4),
            (5,6),
            (6,5),
            (6,1),
            (7,8),
            (7,9),
            (8,7),
            (8,9),
            (9,7),
            (9,8)
            ]

# Define H (runnable paths)
H = nx.DiGraph()
H.add_nodes_from(nodes)
H.add_edges_from(h_edge_lst)
for edge in H.edges:
    H.edges[edge]['length']=5


# list(H.edges(data=True))
# H.edges[1,2]['distance']

# Define G (citystrides)
G = nx.DiGraph()
G.add_nodes_from(nodes)
G.add_edges_from(g_edge_lst)

# 1. All roads have been ran, R = H
R = nx.DiGraph(H)

# Add passes
for edge in R.edges:
    R.edges[edge]['visited']=1

# 2. No Roads have been ran, R is empty
R = nx.DiGraph(H)
for edge in R.edges:
    R.edges[edge]['visited']=0

# 3. Only H/G ran, R = H/G
R = nx.DiGraph(H)
for edge in R.edges:
   if edge in G.edges:
      R.edges[edge]["visited"]=0
   else:
      R.edges[edge]["visited"]=1

# 4. Only G ran, R = G
R = nx.DiGraph(H)

for edge in R.edges:
    if edge in G:
        R.edges[edge]['visited']=1

'''
# Incorporate nodes from one graph into another
H = nx.path_graph(10)
G.add_nodes_from(H)

list(G.nodes) # List all nodes
list(G.edges) # List all edges
list(G.adj[2]) # List adjacent nodes
G.degree[2] # number of edges incident to 1
'''
