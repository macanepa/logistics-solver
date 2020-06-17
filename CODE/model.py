import pyscipopt


model = pyscipopt.Model("Model_Team_8")
x = model.addVar("x")
y = model.addVar("y", vtype="INTEGER")
model.setObjective(x + y)
model.addCons(2 * x - y * y >= 0)
