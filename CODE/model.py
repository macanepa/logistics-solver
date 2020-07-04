import pyscipopt

from mcutils import menu_manager as mc


class Model:
    model = pyscipopt.Model("Model_Team_8")


def build_model(data, parameters):
    Model.model = pyscipopt.Model("Model_Team_8")
    model = Model.model

    # Aux
    big_m = 9999999
    pa = parameters

    # Variable Declarations
    x_srpic = {}
    p_srpic = {}

    mc.mcprint(text="Constructing Variable X & P")
    for supplier in data['suppliers']:
        for reception in data['receptions']:
            for plant in data['plants']:
                for item in data['items']:
                    for corridor in parameters['COR']:
                        variable_x_name = "X[{}][{}][{}][{}][{}]".format(
                            supplier, reception, item, plant, corridor
                        )
                        variable_p_name = "P[{}][{}][{}][{}][{}]".format(
                            supplier, reception, item, plant, corridor
                        )
                        if (supplier, reception) in pa['LDsd'].keys() \
                                and (supplier, item) in pa['CSsp'].keys():
                            x_srpic[supplier, reception, plant, item, corridor] = model.addVar(lb=0, ub=None,
                                                                                               name=variable_x_name,
                                                                                               vtype="INTEGER")
                            p_srpic[supplier, reception, plant, item, corridor] = model.addVar(lb=0, ub=None,
                                                                                               name=variable_p_name,
                                                                                               vtype="INTEGER")

    mc.mcprint(text="Constructing Objective Function")
    objective_function = model.addVar(name="objective function", lb=None)
    model.addCons(objective_function == (
            pyscipopt.quicksum(
                (pa['Tsd'][s, r] * pa['PLra'][r, p] + pa['CDdj'][r, c] + pa['LDsd'][s, r]) * x_srpic[s, r, p, i, c] +
                pa['CSsp'][s, i] * p_srpic[s, r, p, i, c]
                for s in data['suppliers']
                for r in data['receptions']
                for p in data['plants']
                for i in data['items']
                for c in parameters['COR'] if (s, r, p, i, c) in x_srpic.keys())
            + pyscipopt.quicksum((pa['Kdaj'][r, p, c] + pa['CDaj'][p, c]) * x_srpic[s, r, p, i, c]
                                 for s in data['suppliers']
                                 for r in data['receptions']
                                 for p in data['plants']
                                 for i in data['items']
                                 for c in parameters['COR'] if (s, r, p, i, c) in p_srpic.keys()
                                 )))
    model.setObjective(objective_function, "minimize")

    # Constraint: Demand
    mc.mcprint(text="Cons: Demand")
    for p in data['plants']:
        for i in data['items']:
            if (p, i) in parameters['Map'].keys():
                # mc.mcprint(text=parameters['Map'][p,i], color=mc.Color.RED)
                model.addCons(pyscipopt.quicksum(
                    p_srpic[s, r, p, i, c] for s in data['suppliers'] for r in data['receptions'] for c in
                    parameters['COR'] if (s, r, p, i, c) in p_srpic.keys())
                              == (parameters['Map'][p, i]))
            else:
                model.addCons(pyscipopt.quicksum(
                    p_srpic[s, r, p, i, c] for s in data['suppliers'] for r in data['receptions'] for c in
                    parameters['COR'] if (s, r, p, i, c) in p_srpic.keys())
                              == 0)

    # Constraint: Divide Items in Containers
    mc.mcprint(text="Cons: Distribute P in X")
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    for c in parameters['COR']:
                        if (s, r, p, i, c) in p_srpic.keys():
                            model.addCons(p_srpic[s, r, p, i, c] <= x_srpic[s, r, p, i, c] * parameters['Wp'][i])

    # Constraint: Max Container from R -> P (automatic)
    mc.mcprint(text="Cons: Max Container from R -> P (automatic)")
    c = "Automatic"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(x_srpic[s, r, p, i, c] for i in data['items'] for s in data['suppliers'] if
                                             (s, r, p, i, c) in x_srpic.keys()) <= parameters['RCAd'][r])

    # Constraint: Cons: Max Container from R -> P (manual)
    mc.mcprint(text="Cons: Max Container from R -> P (manual)")
    c = "Manual"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(x_srpic[s, r, p, i, c] for i in data['items'] for s in data['suppliers'] if
                                             (s, r, p, i, c) in x_srpic.keys()) <= parameters['RCMd'][r])

    # Constraint: Max Weight from R -> P (automatic)
    mc.mcprint(text="Cons: Max Weight from R -> P (automatic)")
    c = "Automatic"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(
                p_srpic[s, r, p, i, c] * parameters['Fp'][i] for s in data['suppliers'] for i in data['items'] if
                (s, r, p, i, c) in p_srpic.keys())
                          <= parameters['RWAd'][r])

    # Constraint: Max Items from R-> P (manual)
    mc.mcprint(text="Cons: Max Items from R -> P (manual)")
    c = "Manual"
    for r in data['receptions']:
        model.addCons(pyscipopt.quicksum(
            p_srpic[s, r, p, i, c] for s in data['suppliers'] for p in data['plants'] for i in data['items'] if
            (s, r, p, i, c) in p_srpic.keys())
                      <= parameters['RIMd'][r])

    # Constraint: Check if Item can go through corridor (automatic)
    mc.mcprint(text="Cons: Check if Item can go through corridor (automatic)")
    c = "Automatic"
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    if (s, r, p, i, c) in x_srpic.keys():
                        model.addCons(x_srpic[s, r, p, i, c] <= big_m * pa['Ii'][i])

    # Constraint: Don't surpass Supplier Stock
    mc.mcprint(text="Cons: Don't surpass Supplier Stock")
    for s in data['suppliers']:
        model.addCons(pyscipopt.quicksum(
            p_srpic[s, r, p, i, c] for r in data['receptions'] for p in data['plants'] for i in data['items'] for c in
            parameters['COR'] if (s, r, p, i, c) in p_srpic.keys())
                      <= parameters['Ss'][s])

    # Constraint: Manual Corridor can only send to closest plant
    mc.mcprint(text="Cons: Manual Corridor can only send to closest plant")
    c = "Manual"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(x_srpic[s, r, p, i, c] for i in data['items'] for s in data['suppliers'] if
                                             (s, r, p, i, c) in x_srpic.keys()) <= parameters['Eda'][(r, p)] * big_m)


def display_optimal_information():
    model = Model.model
    mc.mcprint(text=model.getStatus(), color=mc.Color.YELLOW)
    if model.getStatus() != "infeasible":
        for var in model.getVars():
            value = int(model.getVal(var))
            print("{}:\t{}".format(value, var)) if value != 0 else None
        if model.getStatus() == "optimal":
            mc.mcprint(text="Found the optimal solution successfully", color=mc.Color.GREEN)
    else:
        mc.mcprint(text="The instance is INFEASIBLE", color=mc.Color.RED)


def reset_model():
    del Model.model
    Model.model = None
