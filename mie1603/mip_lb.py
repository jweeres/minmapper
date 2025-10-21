import math
import pickle
import time
from collections import defaultdict

import gurobipy as gp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from gurobipy import GRB

import generate_instances


def get_lower_bound(relaxation_sol, edges, int_tol):
    new_solution = relaxation_sol

    # Create solution graph
    G = nx.DiGraph()

    for edge in edges:
        i, j = edge
        G.add_edge(i, j, visited=relaxation_sol["x"][edge])

    H = G.copy()

    # Remove all edges from H where visited is an integer number, otherwise retain only fractional part of visited
    for i, j in G.edges:
        if abs(H[i][j]["visited"] - math.floor(H[i][j]["visited"] + 0.5)) <= int_tol:
            H.remove_edge(i, j)
        else:
            H[i][j]["visited"] = H[i][j]["visited"] % 1

    # Set demand equal to excess visited at node
    for node in H.nodes:
        in_edges = H.in_edges(node)
        out_edges = H.out_edges(node)

        H.nodes[node]["demand"] = sum(
            H.edges[edge]["visited"] for edge in out_edges
        ) - sum(H.edges[edge]["visited"] for edge in in_edges)

    # with open('G_values.csv', "w") as f:
    #     for edge in G.edges:
    #         f.write(f"{edge},{G.edges[edge]['visited']}\n")

    # Set of nodes where demand != 0
    demand_nodes = {
        node: H.nodes[node]["demand"]
        for node in H
        if abs(H.nodes[node]["demand"] - math.floor(H.nodes[node]["demand"] + 0.5))
        > int_tol
    }

    if len(demand_nodes) == 0:
        # set x = int(x)
        new_solution["x"] = {
            edge: int(relaxation_sol["x"][edge]) for edge in relaxation_sol["x"]
        }
    elif len(demand_nodes) < 10:
        # calculate min cost flow and set x from that
        nx.set_node_attributes(G, 0, "demand")
        nx.set_node_attributes(G, demand_nodes, "demand")
        print(sum(demand_nodes.values()))
        flow = nx.min_cost_flow(G, weight="visited")
        for u, v in G.edges:
            if u in flow and v in flow[u]:
                new_solution["x"][(u, v)] = flow[u][v]
            else:
                new_solution["x"][(u, v)] = 0
    else:  # probably not feasible, so return
        return

    # set y and z based on x
    new_solution["y"] = {
        edge: 1 if new_solution["x"][edge] > 0 else 0 for edge in relaxation_sol["y"]
    }
    new_solution["z"] = {
        (i, j): 1
        if new_solution["y"][(i, j)] == 1 or new_solution["y"][(j, i)] == 1
        else 0
        for i, j in relaxation_sol["z"]
    }

    return new_solution


def callback(model, where):

    if where == GRB.Callback.MIPNODE:

      time=model.cbGet(GRB.Callback.RUNTIME)
      obj=model.cbGet(GRB.Callback.MIPNODE_OBJBST)
      bound=model.cbGet(GRB.Callback.MIPNODE_OBJBND)
      node_count=model.cbGet(GRB.Callback.MIPNODE_NODCNT)
      
      model._data.append((time, obj, bound, node_count))

    if where == GRB.Callback.MIPSOL:
        # Get results
        # obj = model.cbGet(GRB.Callback.MIPSOL_OBJBST)
        # bound = model.cbGet(GRB.Callback.MIPSOL_OBJBND)
        # time = model.cbGet(GRB.Callback.RUNTIME)

        # model._data.append((time, obj, bound))

        solution_x = model.cbGetSolution(model._x)
        solution_y = model.cbGetSolution(model._y)

        ## Subtour elimination
        # Identify visited nodes
        visited_edges = [edge for edge in model._edges if solution_x[edge] > 0.05]
        visited_nodes = set()
        for edge in visited_edges:
            i, j = edge
            visited_nodes.update({i, j})

        # Define graph of subtours
        S = nx.Graph()
        for i in visited_nodes:
            for j in visited_nodes:
                if (i, j) in model._edges:
                    if i != j and solution_x[(i, j)] > 0.05:
                        S.add_edge(i, j)

        # Find connected components (subtours)
        components = list(nx.connected_components(S))

        # Add subtour elimination constraints for each disconnected component
        for subtour in components:
            if model._depot in subtour:
                continue

            expr_arc = gp.quicksum(
                model._x[i, j]
                for i in subtour
                for j in subtour
                if i != j and (i, j) in model._edges
            )
            model.cbLazy((expr_arc <= len(subtour) - 1))

    if (
        where == GRB.Callback.MIPNODE
        and model.cbGet(GRB.Callback.MIPNODE_STATUS) == GRB.OPTIMAL
    ):

        node_count = model.cbGet(GRB.Callback.MIPNODE_NODCNT)

        if (
            node_count <= 10
            or (node_count <= 50 and node_count % 2 == 0)
            or node_count % 10 == 0
        ):
            # relaxation_sol = model.cbGetNodeRel(model._x)
            relaxation_sol = {
                "x": {
                    edge: model.cbGetNodeRel(model._x[edge]) for edge in model._edges
                },
                "y": {
                    edge: model.cbGetNodeRel(model._y[edge]) for edge in model._edges
                },
                "z": {
                    (i, j): model.cbGetNodeRel(model._z[(i, j)])
                    for i, j in model._edges
                    if i < j
                },
            }
            new_solution = get_lower_bound(
                relaxation_sol, model._edges, model.Params.IntFeasTol
            )
            if new_solution is None:
                return
            new_sol_arr = np.zeros(len(model.getVars()))
            for edge, val in new_solution["x"].items():
                new_sol_arr[model._x[edge].index] = val
            for edge, val in new_solution["y"].items():
                new_sol_arr[model._y[edge].index] = val
            for edge, val in new_solution["z"].items():
                new_sol_arr[model._z[edge].index] = val
            lb_constr = model.getConstrByName("total_length_lb")
            new_sol_arr[model._v.index] = lb_constr.rhs - sum(
                new_sol_arr[model.getRow(lb_constr).getVar(idx).index]
                * model.getRow(lb_constr).getCoeff(idx)
                for idx in range(model.getRow(lb_constr).size())
            )

            # Check if new solution is feasible, return if not
            # for constr in model.getConstrs():
            #     lhs = sum(
            #         new_sol_arr[model.getRow(constr).getVar(idx).index]
            #         * model.getRow(constr).getCoeff(idx)
            #         for idx in range(model.getRow(constr).size())
            #     )
            #     rhs = constr.RHS
            #     if constr.Sense == GRB.LESS_EQUAL and lhs > rhs:
            #         return
            #     if constr.Sense == GRB.GREATER_EQUAL and lhs < rhs:
            #         return
            #     if constr.Sense == GRB.EQUAL and abs(rhs-lhs) > model.Params.FeasibilityTol:
            #         return

            # with open("relaxation_sol.csv", "w") as f:
            #     for edge, value in relaxation_sol.items():
            #         f.write(f"{edge},{value}\n")
            # with open("new_sol.csv", "w") as f:
            #     for edge, value in new_solution.items():
            #         f.write(f"{edge},{value}\n")

            # Objective value of current solution
            current_obj_val = model.cbGet(GRB.Callback.MIPNODE_OBJBST)

            objective = model.getObjective()
            obj_val = sum(
                new_sol_arr[objective.getVar(idx).index] * objective.getCoeff(idx)
                for idx in range(objective.size())
            )  # Calculcate objective value for new solution

            # If your feasible solution is better than gurobi's, replace the solution
            if obj_val > current_obj_val:
                model.cbSetSolution(model.getVars(), new_sol_arr)
            # Evaluating objective value at new solution
            # new_sol_obj = 0

            # # # This is currently wrong
            # # # Get the variables and their coefficients from the objective
            # # vars_in_obj = objective.getVars()   # Variables involved in the objective
            # # coefs_in_obj = objective.getCoeffs()  # Coefficients of those variables

            # # # Calculate the objective value at the new solution
            # # for var, coef in zip(vars_in_obj, coefs_in_obj):
            # #     var_name = var.getVarName()  # Get the name of the variable
            # #     if var_name in new_solution:  # Ensure the solution contains this variable
            # #         new_sol_obj += new_solution[var_name] * coef

            # for i, j in objective.getVarCoeff():
            #     new_solution += new_solution[i] * j

            # if new_sol_obj > current_obj_val:
            #     model.cbSetSolution(model._x, new_solution)


def solve_MIP(C, total_length, start_node_no, time_limit):
    C = nx.DiGraph(C)

    # Get visited, profit, and penalty
    visited = {edge: C.edges[edge]["visited"] for edge in C.edges}
    profit = {edge: C.edges[edge]["profit"] for edge in C.edges}
    penalty = {edge: C.edges[edge]["penalty"] for edge in C.edges}
    violation_penalty = max(visited.values())

    edges, lengths = gp.multidict({edge: C.edges[edge]["length"] for edge in C.edges})
    nodes = C.nodes
    # node_dict = {i:{j for _, j in edges if _ == i } for i in nodes} # Dictionary of connected nodes, old really slow

    node_dict = defaultdict(set)
    for i, j in edges:
        node_dict[i].add(j)

    # Build model

    m = gp.Model("mp")
    print("building model...")

    # Variables
    print("adding variables...")
    x = m.addVars(
        edges, name="traversed", vtype=GRB.INTEGER
    )  # number of times arc (i,j) is traversed
    y = m.addVars(
        edges, name="run", vtype=GRB.BINARY
    )  # arc (i,j) is chosen to be ran, {0,1}

    z = m.addVars(
        {(i, j) for i, j in edges if i < j}, name="profitable_route", vtype=GRB.BINARY
    )
    v = m.addVar(lb=0, ub=time_limit, name="violation", vtype=GRB.CONTINUOUS)

    ## Constraints
    print("adding constraints...")

    # Symmetry Constraint
    symm = m.addConstrs(
        (x.sum(i, "*") == x.sum("*", i) for i in node_dict), name="symmetry"
    )

    # Connectivity Constraint (bi-conditional)
    conn1_const = m.addConstrs(
        (
            x[i, j] >= y[i, j]
            for i in nodes
            for j in nodes
            if i != j and j in node_dict[i]
        )
    )
    conn2_const = m.addConstrs(
        (
            y[i, j] * 2 >= x[i, j]
            for i in nodes
            for j in nodes
            if i != j and j in node_dict[i]
        )
    )

    # Total Length Constraint
    max_length_const = m.addConstr(
        (x.prod(lengths) <= total_length), name="total_length_ub"
    )
    # min_length_const = m.addConstr(
    #     (x.prod(lengths) >= total_length * 0.8), name="total_length_lb"
    # )
    min_length_const = m.addConstr(
        (x.prod(lengths) + v == total_length), name="total_length_lb"
    )

    # Start at start node
    start_node = m.addConstrs(
        (y.sum(start_node_no, j) >= 1 for j in node_dict[start_node_no]),
        name="start_node",
    )  ## this crashes the model, makes it infeasible

    # Set only one route as profitable

    profit_1 = m.addConstrs(
        (z[i, j] >= y[i, j] for i in nodes for j in nodes if i <= j and (i, j) in edges)
    )
    profit_2 = m.addConstrs(
        (z[i, j] >= y[j, i] for i in nodes for j in nodes if i <= j and (i, j) in edges)
    )
    profit_3 = m.addConstrs(
        (
            y[i, j] + y[j, i] >= z[i, j]
            for i in nodes
            for j in nodes
            if i <= j and (i, j) in edges
        )
    )

    print("add objective function...")
    m.setObjective(
        z.prod(profit) - y.prod(penalty) - x.prod(visited) - v * violation_penalty,
        GRB.MAXIMIZE,
    )

    # Set-up lazy constraints and call variables
    m.Params.LazyConstraints = 1
    m._x = x
    m._y = y
    m._z = z
    m._v = v
    m._edges = edges
    m._nodes = nodes
    m._data = []
    m._depot = start_node_no
    m.setParam("TimeLimit", time_limit)
    m.setParam('LogtoConsole', 0)
    m.setParam('LogFile', f'better_lb_{instance}_{total_length}.log')

    print("start solving model...")
    m.optimize(callback)

    # m.write('instance-jess.lp')
    # m.optimize()

    # for v in m.getVars():
    #     if v.x > 1e-6:
    #         print(v.varName, v.x)

    # print("Total profit: ", m.objVal)


    ## Recording solution data
    # Add last solution data
    node_count=m.NodeCount
    obj=m.ObjVal
    bound=m.ObjBound
    time=m.Runtime
    m._data.append((time, obj, bound, node_count))

    # Record results
    with open(log_filename + '.csv', "w") as f:
        for sol_data in m._data:
            time, obj, bound, node_count = sol_data

            f.write("{}, {}, {}, {}\n".format(time, obj, bound, node_count))

    # If model found a feasible solution in the time limit
    if m.solCount > 0:

        # Draw final graph
        F = nx.DiGraph()

        for i in nodes:
            for j in nodes:
                if (i, j) in edges:
                    if x[(i, j)].X >= 0.05:
                        F.add_edge(i, j, visited=float(x[(i, j)].X))

        # Find total distance
        run_length = 0
        for edge in F.edges:
            run_length += lengths[edge] * F.edges[edge]["visited"]

        print("Total length : " + str(run_length))

        print("Time to solve :" + str(m.Runtime))

        pos = nx.spring_layout(F)
        plt.figure()
        nx.draw(
            F, pos, with_labels=True, node_color="lightblue", edge_color="gray", arrows=True
        )
        plt.title("Optimal Run")
        # plt.show()

        # Create final graph solution
        print("saving graphs to file", end=" ", flush=True)

        log_filepath = "final_test/"
        with open(
            log_filepath+
            "sol_graph_"
            + instance
            + "_"
            + str(total_length)
            + str("_test_better_lb")
            + ".pkl",
            "wb",
        ) as file:
            pickle.dump(F, file, pickle.HIGHEST_PROTOCOL)

    print("complete!")


# Parameters
total_length_lst = [5000, 10000, 15000]
instance_lst = ["instance-jin"]
# ["instance-jess-min","instance-jess"]#, "instance-jess"]#, "instance-jin.pkl"]

start_node_no = 6813225352  # Start node for instance-jess-min
# start_node_no = 1004361926 # New start node for instance-jess

time_limit = 1800#3600

for instance in instance_lst:
    for total_length in total_length_lst:

        if 'jess' in instance:
            start_node_no = 6813225352
        
        if 'jin' in instance:
            start_node_no = 394502562

        log_filepath = "final_test/"
        log_filename = (
            log_filepath + instance + "_" + str(total_length) + str("_test_better_lb")
        )

        print("reading instance file...")

        C = pd.read_pickle(instance + ".pkl")

        C = ox.truncate.truncate_graph_dist(C, start_node_no, total_length)

        # Run experiments
        print("running experiment with " + str(total_length) + " total_length")
        solve_MIP(C, total_length, start_node_no, time_limit)
