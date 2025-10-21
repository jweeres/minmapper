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

def get_cuts(relaxation_sol):

  new_solution = relaxation_sol

  # Create solution graph
  G = nx.DiGraph()

  for edge in edges:
      i,j = edge

      if relaxation_sol[edge]>0.05:
          G.add_edge(i,j, visited=relaxation_sol[edge])

  epsilon_lst = [0, 0.25, 0.5]

  for epsilon in epsilon_lst:
    H  = G.copy()

    # Remove all edges from H where visited < 1-epsilon
    for edge in G.edges:
      if H.edges[edge]['visited'] < 1-epsilon:
          i,j = edge
          H.remove_edge(i,j)

    constraints_to_add=[]  

    comp_lst = list(nx.strongly_connected_components(H))
    in_edges=[]
    comp_edges=[]

    for component in comp_lst:
        if start_node_no not in component:

          in_edges = [(u,v) for u,v in H.edges if u not in component and v in component]
          comp_edges = [(u,v) for u,v in H.edges if u in component and v in component]

          # Checking that there's at least one edge in each list
          if in_edges !=[] and comp_edges!=[]:
            
            for comp_edge in comp_edges:
              
              in_edge_visits = sum([H.edges[in_edge]['visited'] for in_edge in in_edges])

              if in_edge_visits < H.edges[comp_edge]['visited']:
                  k,l = comp_edge

                  # Add constraint to list
                  constraints_to_add.append((x[i,j] >= y[k,l] for i,j in edge for edge in in_edges))
              
    if len(constraints_to_add)>0:
      break

  # If we didn't previously add any constraints
  if constraints_to_add==[]:
  
    for u,v in G.edges:

      H  = G.copy()

      H.add_node('w')
      H.add_edge(u,'w')
      H.add_edge('w',v)

      H.edges[(u,'w')]['visited']=G.edges[(u,v)]['visited']
      H.edges[('w',v)]['visited']=float('inf')
      H.remove_edge(u,v)

      cut_val, partition = nx.minimum_cut(H, start_node_no, 'w', capacity="visited")

      if cut_val < G.edges[(u,v)]['visited']:
        i_set, j_set = partition
        cut_set = set()

        for i, i_successors in ((i, G[i]) for i in i_set):
          cut_set.update((i,j) for j in i_successors if j in j_set)
        
        j_set.add(v)
        
        for comp_edge in nx.induced_subgraph(G, j_set).edges:
          k,l = comp_edge
          constraints_to_add.append((x[i,j] >= y[k,l] for i,j in edge for edge in cut_set))

  return constraints_to_add

def subtourelim(model, where):
  if where == GRB.Callback.MIPSOL:

    # Get results
    obj=model.cbGet(GRB.Callback.MIPSOL_OBJBST)
    bound=model.cbGet(GRB.Callback.MIPSOL_OBJBND)
    time=model.cbGet(GRB.Callback.RUNTIME)
    
    model._data.append((time, obj, bound))

    solution_x = model.cbGetSolution(model._x)
    solution_y = model.cbGetSolution(model._y)

  ## Subtour elimination
  # Identify visited nodes
    visited_edges = [edge for edge in model._edges if solution_x[edge]>0.05]
    visited_nodes = set()
    for edge in visited_edges:
      i,j = edge
      visited_nodes.update({i,j})

    # Define graph of subtours
    S = nx.Graph()
    for i in visited_nodes:
        for j in visited_nodes:
          if (i,j) in model._edges:
              if i!=j and solution_x[(i,j)] > 0.05:
                  S.add_edge(i,j)

    # Find connected components (subtours)
    components = list(nx.connected_components(S))

    # Add subtour elimination constraints for each disconnected component
    for subtour in components:
      if model._depot in subtour:
        continue

      expr_arc = gp.quicksum(model._x[i,j] for i in subtour for j in subtour if i!=j and (i,j) in model._edges)
      model.cbLazy((expr_arc <= len(subtour) - 1))

  if where ==  GRB.Callback.MIPNODE and GRB.Callback.MIPNODE_STATUS ==  GRB.OPTIMAL:
    relaxation_sol = model.cbGetNodeRel(model._x)
    connectivity_cuts = get_cuts(relaxation_sol)

    for cut in connectivity_cuts:
      model.cbCut(cut)


def solve_MIP(C, total_length, start_node_no, time_limit):

  C = nx.DiGraph(C)

  # Get visited, profit, and penalty
  visited = {edge: C.edges[edge]['visited'] for edge in C.edges}
  profit = {edge: C.edges[edge]['profit'] for edge in C.edges}
  penalty = {edge: C.edges[edge]['penalty'] for edge in C.edges}

  edges, lengths = gp.multidict({edge:C.edges[edge]['length'] for edge in C.edges })
  nodes = C.nodes
  # node_dict = {i:{j for _, j in edges if _ == i } for i in nodes} # Dictionary of connected nodes, old really slow

  node_dict = defaultdict(set)
  for i,j in edges:
    node_dict[i].add(j)

  # Build model

  m = gp.Model("mp")
  print('building model...')

  # Variables
  print('adding variables...')
  x = m.addVars(edges, name="traversed", vtype=GRB.INTEGER) # number of times arc (i,j) is traversed
  y = m.addVars(edges, name="run", vtype=GRB.BINARY) # arc (i,j) is chosen to be ran, {0,1}

  z = m.addVars({(i,j) for i,j in edges if i< j}, name = 'profitable_route', vtype=GRB.BINARY)

  ## Constraints
  print('adding constraints...')

  # Symmetry Constraint
  symm = m.addConstrs((x.sum(i,'*') == x.sum('*', i) for i in node_dict), name = 'symmetry')

  # Connectivity Constraint (bi-conditional)
  conn1_const = m.addConstrs((x[i,j] >= y[i,j] for i in nodes for j in nodes if i!=j and j in node_dict[i]))
  conn2_const = m.addConstrs((y[i,j]*2 >= x[i,j] for i in nodes for j in nodes if i!=j and j in node_dict[i]))

  # Total Length Constraint
  max_length_const = m.addConstr((x.prod(lengths)<=total_length), name = 'total_length')
  min_length_const = m.addConstr((x.prod(lengths)>=total_length*0.8), name = 'total_length')


  # Start at start node
  start_node = m.addConstrs((y.sum(start_node_no, j)>=1 for j in node_dict[start_node_no]), name='start_node') ## this crashes the model, makes it infeasible

  # Set only one route as profitable

  profit_1 = m.addConstrs((z[i,j] >= y[i,j] for i in nodes for j in nodes if i<=j and (i,j) in edges))
  profit_2 = m.addConstrs((z[i,j] >= y[j,i] for i in nodes for j in nodes if i<=j and (i,j) in edges))
  profit_3 = m.addConstrs((y[i,j] + y[j,i] >= z[i,j] for i in nodes for j in nodes if i<=j and (i,j) in edges))

  print('add objective function...')
  m.setObjective(z.prod(profit)-z.prod(penalty)-x.prod(visited), GRB.MAXIMIZE)

  # Set-up lazy constraints and call variables
  m.Params.LazyConstraints = 1
  m._x = x
  m._y = y
  m._z = z
  m._edges = edges
  m._N = nodes
  m._data = []
  m._depot = start_node_no
  m.setParam('TimeLimit', time_limit)


  print('start solving model...')
  m.optimize(subtourelim)

  # m.write('instance-jess.lp')
  # m.optimize()

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
              F.add_edge(i,j, visited=float(x[(i,j)].x))

  # Find total distance
  run_length = 0
  for edge in F.edges:
      run_length += lengths[edge]*F.edges[edge]['visited']
      # print(edge, lengths[edge])
      # print(edge, S.edges[edge]['visited'])

  print('Total length : ' + str(run_length))

  pos = nx.spring_layout(F)
  plt.figure()
  nx.draw(F, pos, with_labels=True, node_color='lightblue', edge_color='gray', arrows=True)
  plt.title("Optimal Run")
  # plt.show()

  # Add last solution data
  obj=m.ObjVal
  bound=m.ObjBound
  time=m.Runtime
  m._data.append((time, obj, bound))

  # # Record results
  # with open(log_filename + '.csv', "w") as f:
  #   for sol_data in m._data:
  #     time, obj, bound = sol_data

  #     f.write("{}, {}, {}\n".format(time, obj, bound))

  # Create final graph solution
  print("saving graphs to file", end=" ", flush=True)

  # with open('sol_graph_'+instance + '_' + str(total_length)+'.pkl', "wb") as file:    #+ str('_removed') 
  #     pickle.dump(F, file, pickle.HIGHEST_PROTOCOL)

  print("complete!")


# Parameters
total_length_lst =[5000]#[1000, 5000, 8000, 10000, 15000]
instance_lst = ["instance-jess"]#["instance-jess-min-removed","instance-jess-removed"]##["instance-jess-min"]#, "instance-jess"]#, "instance-jin.pkl"]

start_node_no = 6813225352 # Start node for instance-jess-min
# start_node_no = 1004361926 # New start node for instance-jess

time_limit=100#3600

for instance in instance_lst:
  for total_length in total_length_lst:

    log_filepath = "C://Users//Jin//Github//MIE1603-Project//experiment_jess_3600//"
    log_filename = log_filepath + instance + '_' + str(total_length) #+ str('_removed')

    print("reading instance file...")

    C  = pd.read_pickle(instance +'.pkl')

    C = ox.truncate.truncate_graph_dist(C,start_node_no,total_length)

    # Run experiments
    print('running experiment with ' + str(total_length) + ' total_length')
    solve_MIP(C, total_length, start_node_no, time_limit)


# C = pd.read_pickle('instance-jess.pkl')
# start_node_no = 6571986444
# C = ox.truncate.truncate_graph_dist(C,start_node_no,500)

# C = nx.Graph(C)
# nx.connected_components(C)

#######################################################################################



