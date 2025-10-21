import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import matplotlib.pyplot as plt

import generate_instances



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
# g_edge_lst = [
#             (1,2),
#             (1,7),
#             (2,3),
#             (3,2),
#             (3,4),
#             (4,5),
#             (4,8),
#             (5,9),
#             (6,1),
#             (6,5),
#             (7,6),
#             (7,8),
#             (7,9), 
#             (8,7),
#             (8,2),
#             (8,3),
#             (9,7)
#             ]

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
# R = nx.DiGraph(H)

# for edge in R.edges:
#     R.edges[edge]['visited']=1

# 2. No Roads have been ran, R is empty
# R = nx.DiGraph(H)
# for edge in R.edges:
#     R.edges[edge]['visited']=0

# 3. Only H/G ran, R = H/G
# R = nx.DiGraph(H)
# for edge in R.edges:
#    if edge in G.edges:
#       R.edges[edge]["visited"]=0
#    else:
#       R.edges[edge]["visited"]=1

# 4. Only G ran, R = G
R = nx.DiGraph(H)

for edge in R.edges:
    if edge in G:
        R.edges[edge]['visited']=1
    else:
        R.edges[edge]['visited']=0


edges, lengths = gp.multidict({edge:H.edges[edge]['length'] for edge in H.edges })
nodes = [i for i in range(1, n_nodes+1)]
profit = {edge: (50 if edge in G.edges and R.edges[edge]['visited']==0 else 0) for edge in H.edges}
penalty = {edge: (30 if edge in R.edges else 0) for edge in H.edges}

def subtourelim(model, where):
    if where == GRB.Callback.MIPSOL:

      solution_x = model.cbGetSolution(model._x)
      solution_y = model.cbGetSolution(model._y)

    ## Subtour elimination
    # Identify visited nodes
      visited_edges = [edge for edge in model._edges if solution_y[edge]>0.05]
      visited_nodes = set()
      for edge in visited_edges:
        i,j = edge
        visited_nodes.update({i,j})

      # Define graph of subtours
      S = nx.Graph()
      for i in visited_nodes:
         for j in visited_nodes:
            if (i,j) in edges:
                if i!=j and solution_y[(i,j)] > 0.05:
                    S.add_edge(i,j)

      # Find connected components (subtours)
      components = list(nx.connected_components(S))

      # Add subtour elimination constraints for each disconnected component
      for subtour in components:
        if model._depot in subtour:
          continue

        expr_arc = gp.quicksum(model._y[i,j] for i in subtour for j in subtour if i!=j and (i,j) in model._edges)
        model.cbLazy((expr_arc <= len(subtour) - 1))


def solve_model(nodes, edges, depot, big_M, total_length):
    # Define model
    m = gp.Model("mp")

    x = m.addVars(edges, name="traversed", vtype=GRB.INTEGER) # number of times arc (i,j) is traversed
    y = m.addVars(edges, name="run", vtype=GRB.BINARY) # arc (i,j) is chosen to be ran, {0,1}
    z = m.addVars({(i,j) for i in nodes for j in nodes if i<j}, name='profitable_route', vtype=GRB.BINARY)

    ## Constraints

    # Symmetry Constraint
    symm = m.addConstrs((x.sum(i,'*') == x.sum('*', i) for i in node_dict), name = 'symmetry')

    # Connectivity Constraint (bi-conditional)
    conn1_const = m.addConstrs((x[i,j] >= y[i,j] for i in nodes for j in nodes if i!=j and j in node_dict[i]))
    conn2_const = m.addConstrs((y[i,j]*big_M >= x[i,j] for i in nodes for j in nodes if i!=j and j in node_dict[i]))

    # Total Length Constraint
    total_length_const = m.addConstr((x.prod(lengths)<=total_length), name = 'total_length')

    # Start at start node
    start_node = m.addConstrs((y.sum(1, j)>=1 for j in node_dict[1]), name='start_node')

    # Set only one route as profitable

    profit_1 = m.addConstrs((z[i,j] >= y[i,j] for i in nodes for j in nodes if i<=j and (i,j) in edges))
    profit_2 = m.addConstrs((z[i,j] >= y[j,i] for i in nodes for j in nodes if i<=j and (i,j) in edges))
    profit_3 = m.addConstrs((y[i,j] + y[j,i] >= z[i,j] for i in nodes for j in nodes if i<=j and (i,j) in edges))

    m.setObjective(z.prod(profit)-x.prod(penalty), GRB.MAXIMIZE)

    # # Solve problem
    m.write('optimal_run.lp')
    # m.optimize()

    # Set-up lazy constraints and call variables
    m.Params.LazyConstraints =1
    m._x = x
    m._y = y
    m._edges = edges
    m._N = n_nodes
    m._depot = depot
    m.optimize(subtourelim)

    for v in m.getVars():
        if v.x > 1e-6:
            print(v.varName, v.x)

    print('Total profit: ', m.objVal)

    # Draw final graph
    F = nx.DiGraph()

    for i in nodes:
        for j in nodes:
            if (i,j) in edges:
                if x[(i,j)].x >= 0.05:
                    F.add_edge(i,j)

    pos = nx.spring_layout(F)
    plt.figure()
    nx.draw(F, pos, with_labels=True, node_color='lightblue', edge_color='gray', arrows=True)

    plt.title("Optimal Run")
    plt.show()

    return m

depot = 1
big_M = 10
total_length = 500

m = solve_model(nodes, edges, depot, big_M, total_length)
