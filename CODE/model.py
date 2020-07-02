import pyscipopt
from mcutils import menu_manager as mc

class Model:
    # model = None
    model = pyscipopt.Model("Model_Team_8")

def build_model(data, parameters):
    Model.model = pyscipopt.Model("Model_Team_8")
    model = Model.model
    # Aux
    MM = 9999999
    pa = parameters

    # Variable Declarations
    Xsrpic = {}
    # Yrpic = {}
    Psrpic = {}

    mc.mcprint(text="Constructing Variable X")
    # Construct Variable X
    for supplier in data['suppliers']:
        for reception in data['receptions']:
            for plant in data['plants']:
                for item in data['items']:
                    for corridor in parameters['COR']:
                        variable_name = "X[{}][{}][{}][{}][{}]".format(
                            supplier, reception, item, plant, corridor
                        )
                        if (supplier,reception) in pa['LDsd'].keys():
                            Xsrpic[supplier, reception, plant, item, corridor] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")

    # TODO: Only construct variable that can exists (i.e, remove corridor where )
    # Construct Variable Y
    # for reception in data['receptions']:
    #     for plant in data['plants']:
    #         for item in data['items']:
    #             for corridor in parameters['COR']:
    #                 variable_name = "Y[{}][{}][{}][{}]".format(
    #                     reception, plant, item, corridor
    #                 )
                    # Yrpic[reception, plant, item, corridor] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")

    mc.mcprint(text="Constructing Variable P")
    # Construct Variable P
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    for c in parameters['COR']:
                        variable_name = "P[{}][{}][{}][{}][{}]".format(
                            s, r, p, i, c
                        )
                        if (s, r) in pa['LDsd'].keys():
                            Psrpic[s,r,p,i,c] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")


    # pprint(model.getVars())


    objective_function = model.addVar(name="objective function", lb=None)
    # model.addCons(objective_function == pyscipopt.quicksum(Xsrpi[supplier, reception, plant, item]*3 for supplier in data['suppliers'] for reception in data['receptions'] for plant in data['plants'] for item in data['items'] ))
    # model.addCons(objective_function == pyscipopt.quicksum(Psrpi[s,r,p,i] + Xsrpi[s,r,p,i] + Yrpic[r,p,i,c] for s in data['suppliers'] for r in data['receptions'] for p in data['plants'] for i in data['items'] for c in parameters['COR'] ))

    mc.mcprint(text="Constructing Objective Function")
    # TODO: This is the real objective function. Is not complete.
    model.addCons(objective_function == (
                  pyscipopt.quicksum((pa['Tsd'][s,r]*pa['PLra'][r,p] + pa['CDdj'][r,c]+ pa['LDsd'][s,r])*Xsrpic[s,r,p,i,c] + pa['CSsp'][s,i]*Psrpic[s,r,p,i,c]\
                                     #for s,r,p,i,c


                                     for s in data['suppliers']\
                                     for r in data['receptions']\
                                     for p in data['plants']\
                                     for i in data['items']\
                                     for c in parameters['COR'] if (s,r) in pa['LDsd'].keys() and (s,i) in pa['CSsp'].keys() and (s,r,p,i,c) in Xsrpic.keys() and (s,r,p,i,c) in Psrpic.keys())\
                  + pyscipopt.quicksum((pa['Kdaj'][r,p,c] + pa['CDaj'][p,c]) * Xsrpic[s,r,p,i,c]\
                  #                    for r,p,i,c
                                     for s in data['suppliers']
                                     for r in data['receptions']\
                                     for p in data['plants']\
                                     for i in data['items']\
                                     for c in parameters['COR']  if (s,r,p,i,c) in Psrpic.keys()\
                                       )))

    model.setObjective(objective_function, "minimize")

    # Example constraint
    # model.addCons(pyscipopt.quicksum(Xsrpi[supplier, reception, plant, item] for supplier in data['suppliers'] for reception in data['receptions'] for plant in data['plants'] for item in data['items']) <= 3.2)


    mc.mcprint(text="Cons: Demand")
    # Restriccion de demanda
    for p in data['plants']:
        for i in data['items']:
            if (p,i) in parameters['Map'].keys():
                # mc.mcprint(text=parameters['Map'][p,i], color=mc.Color.RED)
                model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for s in data['suppliers'] for r in data['receptions'] for c in parameters['COR'] if (s,r,p,i,c) in Psrpic.keys())
                              == (parameters['Map'][p,i]))
            else:
                model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for s in data['suppliers'] for r in data['receptions'] for c in parameters['COR'] if (s,r,p,i,c) in Psrpic.keys())
                              == 1)

    mc.mcprint(text="Cons: Distribute P in X")
    # Repartir los productos en containers
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    for c in parameters['COR']:
                        if (s, r, p, i, c) in Psrpic.keys():
                            model.addCons(Psrpic[s,r,p,i,c] <= Xsrpic[s,r,p,i,c] * parameters['Wp'][i])


    # Flujo todo lo que llega a reception, debe mandarse a un assembly
    # for r in data['receptions']:
    #     for i in data['items']:
    #         model.addCons(pyscipopt.quicksum(Xsrpi[s,r,p,i] for s in data['suppliers'] for p in data['plants'])\
    #                       == pyscipopt.quicksum(Yrpic[r,p,i,c] for c in parameters['COR'] for p in data['plants']))

    mc.mcprint(text="Cons: Max Container from R -> P (automatic)")
    # Flujo limite de cantidad de containers transportados desde reception r con corridor automatico
    c = "Automatic"
    for r in data['receptions']:
        for p in data['plants']:
            if (s, r, p, i, c) in Xsrpic.keys():
                model.addCons(pyscipopt.quicksum(Xsrpic[s,r,p,i,c] for i in data['items'] for s in data['suppliers']) <= parameters['RCAd'][r] )


    mc.mcprint(text="Cons: Max Container from R -> P (manual)")
    # Flujo limite de cantidad de containers transportados desde reception r con corridor manual
    c = "Manual"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(Xsrpic[s,r,p,i,c] for i in data['items'] for s in data['suppliers'] if (s,r,p,i,c) in Xsrpic.keys()) <= parameters['RCMd'][r])

    mc.mcprint(text="Cons: Max Weight from R -> P (automatic)")
    # Peso limite de corridor automatico
    c = "Automatic"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] * parameters['Fp'][i] for s in data['suppliers'] for i in data['items'] if (s,r,p,i,c) in Psrpic.keys())
                  <= parameters['RWAd'][r])

    mc.mcprint(text="Cons: Max Items from R -> P (manual)")
    # Cantidad de Items limite de corridor manual
    c = "Manual"
    for r in data['receptions']:
        model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for s in data['suppliers'] for p in data['plants'] for i in data['items'] if (s,r,p,i,c) in Psrpic.keys())
                      <= parameters['RIMd'][r])

    mc.mcprint(text="Cons: Check if Item can go through corridor (automatic)")
    c = "Automatic"
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    if (s, r, p, i, c) in Xsrpic.keys():
                        model.addCons(Xsrpic[s,r,p,i,c] <= MM*pa['Ii'][i])

    mc.mcprint(text="Cons: Supplier Stock")
    # stock de supplier
    for s in data['suppliers']:
        model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for r in data['receptions'] for p in data['plants'] for i in data['items'] for c in parameters['COR']  if (s,r,p,i,c) in Psrpic.keys())
                      <= parameters['Ss'][s])


    mc.mcprint(text="Cons: Manual Corridor only send to closest plant")
    # Permitir que usando corridor manual, solo se pueda mandar a la planta mas cercana
    c = "Manual"
    for r in data['receptions']:
        for p in data['plants']:
                model.addCons(pyscipopt.quicksum(Xsrpic[s,r,p,i,c] for i in data['items'] for s in data['suppliers'] if (s,r,p,i,c) in Xsrpic.keys()) <= parameters['Eda'][(r,p)]*MM )

    # TODO: automatic solo acepta ciertos items (este valor se encuentra en items)

    for x in Xsrpic:
        print(x)
    for x in Psrpic:
        print(x)
def display_optimal_information():
    model = Model.model
    if model.getStatus() == "optimal":
        for var in model.getVars():
            value = int(model.getVal(var))
            print("{}:\t{}".format(value, var)) if value != 0 else None
        mc.mcprint(text="Found the optimal solution successfully", color=mc.Color.GREEN)
    else:
        mc.mcprint(text="The instance is INFEASIBLE", color=mc.Color.RED)

def reset_model():
    del Model.model
    Model.model = None

# def print_model_info():
# model = pyscipopt.Model("Model_Team_8")
# x = model.addVar("x")model.getVal(var)
# y = model.addVar("y", vtype="INTEGER")
# model.setObjective(x + y)
# model.addCons(2 * x - y * y >= 0)
