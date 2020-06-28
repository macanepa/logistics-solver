import pyscipopt
from pprint import pprint

global model
model = pyscipopt.Model("Model_Team_8")

def build_model(data, parameters):
    # Variable Declarations
    Xsdap = {}
    Ydapj = {}

    # Construct Variable X
    for supplier in data['suppliers']:
        # print(supplier)
        for reception in data['receptions']:
            # print("\t", reception)
            for plant in data['plants']:
                # print("\t\t", plant)
                for item in data['items']:
                    # print("\t\t\t", item)
                    variable_name = "X[{}][{}][{}][{}]".format(
                        supplier, reception, item, plant
                    )
                    Xsdap[supplier, reception, plant, item] = model.addVar(lb=0, ub=None, name=variable_name, vtype="INTEGER")

    # TODO: Only construct variable that can exists (i.e, remove corridor where )
    # Construct Variable Y
    for reception in data['receptions']:
        # print(reception)
        for plant in data['plants']:
            # print("\t", plant)
            for item in data['items']:
                # print("\t\t", item)
                for corridor in data['corridor']:
                    # print("\t\t\t", corridor)
                    variable_name = "Cont. transported from DC:{} to assembly:{} with corridor:{} of item:{}".format(
                        reception, plant, corridor, item
                    )
                    # Ydapj[reception, plant, item, corridor] = model.addVar(lb=0, ub=None, name=variable_name)
    # pprint(model.getVars())
    funcion_objetivo = model.addVar(name="funcion objetivo", lb=None)
    model.addCons(funcion_objetivo == pyscipopt.quicksum(Xsdap[supplier, reception, plant, item]*3 for supplier in data['suppliers'] for reception in data['receptions'] for plant in data['plants'] for item in data['items'] ))
    model.addCons(pyscipopt.quicksum(Xsdap[supplier, reception, plant, item] for supplier in data['suppliers'] for reception in data['receptions'] for plant in data['plants'] for item in data['items']) <= 3.2)
    model.setObjective(funcion_objetivo, "maximize")


def display_optimal_information():
    for var in model.getVars():
        print("Var:", var, model.getVal(var))


# def print_model_info():
# model = pyscipopt.Model("Model_Team_8")
# x = model.addVar("x")
# y = model.addVar("y", vtype="INTEGER")
# model.setObjective(x + y)
# model.addCons(2 * x - y * y >= 0)
