import pyscipopt
from pprint import pprint
from mcutils import menu_manager as mc

class Model:
    # model = None
    model = pyscipopt.Model("Model_Team_8")

def build_model(data, parameters):
    Model.model = pyscipopt.Model("Model_Team_8")
    model = Model.model
    # Aux
    MM = 9999999

    # Variable Declarations
    Xsrpic = {}
    # Yrpic = {}
    Psrpic = {}

    # Construct Variable X
    for supplier in data['suppliers']:
        for reception in data['receptions']:
            for plant in data['plants']:
                for item in data['items']:
                    for corridor in parameters['COR']:
                        variable_name = "X[{}][{}][{}][{}][{}]".format(
                            supplier, reception, item, plant, corridor
                        )
                        Xsrpic[supplier, reception, plant, item, corridor] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")

    # TODO: Only construct variable that can exists (i.e, remove corridor where )
    # Construct Variable Y
    for reception in data['receptions']:
        for plant in data['plants']:
            for item in data['items']:
                for corridor in parameters['COR']:
                    variable_name = "Y[{}][{}][{}][{}]".format(
                        reception, plant, item, corridor
                    )
                    # Yrpic[reception, plant, item, corridor] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")

    # Construct Variable P
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    for c in parameters['COR']:
                        variable_name = "P[{}][{}][{}][{}][{}]".format(
                            s, r, p, i, c
                        )
                        Psrpic[s,r,p,i, c] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")


    # pprint(model.getVars())


    objective_function = model.addVar(name="objective function", lb=None)
    # model.addCons(objective_function == pyscipopt.quicksum(Xsrpi[supplier, reception, plant, item]*3 for supplier in data['suppliers'] for reception in data['receptions'] for plant in data['plants'] for item in data['items'] ))
    # model.addCons(objective_function == pyscipopt.quicksum(Psrpi[s,r,p,i] + Xsrpi[s,r,p,i] + Yrpic[r,p,i,c] for s in data['suppliers'] for r in data['receptions'] for p in data['plants'] for i in data['items'] for c in parameters['COR'] ))
    pa = parameters

    # TODO: This is the real objective function. Is not complete.
    model.addCons(objective_function == (
                  pyscipopt.quicksum((pa['Tsd'][s,r]*pa['PLra'][r,p] + pa['CDdj'][r,c]+ pa['LDsd'][s,r])*Xsrpic[s,r,p,i,c] + pa['CSsp'][s,i]*Psrpic[s,r,p,i,c]\
                                     #for s,r,p,i,c


                                     for s in data['suppliers']\
                                     for r in data['receptions']\
                                     for p in data['plants']\
                                     for i in data['items']\
                                     for c in parameters['COR'] if (s,r) in pa['LDsd'].keys())\
                  + pyscipopt.quicksum((pa['Kdaj'][r,p,c] + pa['CDaj'][p,c]) * Xsrpic[s,r,p,i,c]\
                  #                    for r,p,i,c
                                     for s in data['suppliers']
                                     for r in data['receptions']\
                                     for p in data['plants']\
                                     for i in data['items']\
                                     for c in parameters['COR']\
                                       )))

    model.setObjective(objective_function, "minimize")

    # Example constraint
    # model.addCons(pyscipopt.quicksum(Xsrpi[supplier, reception, plant, item] for supplier in data['suppliers'] for reception in data['receptions'] for plant in data['plants'] for item in data['items']) <= 3.2)


    # Restriccion de demanda
    for p in data['plants']:
        for i in data['items']:
            model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for s in data['suppliers'] for r in data['receptions'] for c in parameters['COR'])
                          == (parameters['Map'][p,i] if (p,i) in parameters['Map'].keys() else 0))

    # Repartir los productos en containers
    for s in data['suppliers']:
        for r in data['receptions']:
            for p in data['plants']:
                for i in data['items']:
                    for c in parameters['COR']:
                        model.addCons(Psrpic[s,r,p,i,c] <= Xsrpic[s,r,p,i,c] * parameters['Wp'][i])


    # Flujo todo lo que llega a reception, debe mandarse a un assembly
    # for r in data['receptions']:
    #     for i in data['items']:
    #         model.addCons(pyscipopt.quicksum(Xsrpi[s,r,p,i] for s in data['suppliers'] for p in data['plants'])\
    #                       == pyscipopt.quicksum(Yrpic[r,p,i,c] for c in parameters['COR'] for p in data['plants']))

    # Flujo limite de cantidad de containers transportados desde reception r con corridor automatico
    c = "Automatic"
    for r in data['receptions']:
        for p in data['plants']:
                model.addCons(pyscipopt.quicksum(Xsrpic[s,r,p,i,c] for i in data['items'] for s in data['suppliers']) <= parameters['RCAd'][r] )


    # Flujo limite de cantidad de containers transportados desde reception r con corridor manual
    c = "Manual"
    for r in data['receptions']:
        for p in data['plants']:
                model.addCons(pyscipopt.quicksum(Xsrpic[s,r,p,i,c] for i in data['items'] for s in data['suppliers']) <= parameters['RCMd'][r])

    # Peso limite de corridor automatico
    c = "Automatic"
    for r in data['receptions']:
        for p in data['plants']:
            model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] * parameters['Fp'][i] for s in data['suppliers'] for i in data['items'])
                          <= parameters['RWAd'][r])

    # Cantidad de Items limite de corridor manual
    c = "Manual"
    for  r in data['receptions']:
        model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for s in data['suppliers'] for p in data['plants'] for i in data['items'])
                      <= parameters['RIMd'][r])


    # stock de supplier
    for s in data['suppliers']:
        model.addCons(pyscipopt.quicksum(Psrpic[s,r,p,i,c] for r in data['receptions'] for p in data['plants'] for i in data['items'] for c in parameters['COR'])
                      <= parameters['Ss'][s])


    # Permitir que usando corridor manual, solo se pueda mandar a la planta mas cercana
    c = "Manual"
    for r in data['receptions']:
        for p in data['plants']:
                model.addCons(pyscipopt.quicksum(Xsrpic[s,r,p,i,c] for i in data['items'] for s in data['suppliers'] ) <= parameters['Eda'][(r,p)]*MM)


def display_optimal_information():
    model = Model.model
    for var in model.getVars():
        value = int(model.getVal(var))
        print("{}:\t{}".format(value, var)) if value != 0 else None

def reset_model():
    del Model.model
    Model.model = None

# def print_model_info():
# model = pyscipopt.Model("Model_Team_8")
# x = model.addVar("x")model.getVal(var)
# y = model.addVar("y", vtype="INTEGER")
# model.setObjective(x + y)
# model.addCons(2 * x - y * y >= 0)
