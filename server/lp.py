import pulp

problem = pulp.LpProblem('', pulp.const.LpMinimize)

u1 = pulp.LpVariable('u1', lowBound=0)
u2 = pulp.LpVariable('u2', lowBound=0)
u3 = pulp.LpVariable('u3', lowBound=0)
u4 = pulp.LpVariable('u4', lowBound=0)
v1 = pulp.LpVariable('v1', lowBound=0)
v2 = pulp.LpVariable('v2', lowBound=0)
v3 = pulp.LpVariable('v3', lowBound=0)
v4 = pulp.LpVariable('v4', lowBound=0)
l12 = pulp.LpVariable('l12', lowBound=0)
l13 = pulp.LpVariable('l13', lowBound=0)
l14 = pulp.LpVariable('l14', lowBound=0)
l23 = pulp.LpVariable('l23', lowBound=0)
l24 = pulp.LpVariable('l24', lowBound=0)
l34 = pulp.LpVariable('l34', lowBound=0)
b1 = pulp.LpVariable('b1', lowBound=0)
g1 = pulp.LpVariable('g1', lowBound=0)
b2 = pulp.LpVariable('b2', lowBound=0)
g2 = pulp.LpVariable('g2', lowBound=0)

problem += 0.3*u1 + 0.3*u2 + 0.3*u3 + 0.3*u4 + 0.3*v1 + 0.3*v2 + 0.3*v3 + 0.3*v4 \
    + 0.7*l12 + 0.7*l13 + 0.7*l14 + 0.7*l23 + 0.7*l24 + 0.7*l34 \
    + 0.000001*b1 + 0.000001*g1 + 0.000001*b2 + 0.000001*g2, 'Function'

problem += 6*b1 - 6*g1 + 2*b2 - 2*g2 + l12 >= 0
problem += 3*b1 - 3*g1 - 4*b2 + 4*g2 + l13 >= 0
problem += -2*b1 + 2*g1 + b2 - g2 + l14 >= 0
problem += -3*b1 + 3*g1 - 6*b2 + 6*g2 + l23 >= 0
problem += 4*b1 - 4*g1 + 3*b2 - 3*g2 + l24 >= 0
problem += b1 - g1 - 3*b2 + 3*g2 + l34 >= 0

problem += b1 - g1 + 6*b2 - 6*g2 + u1 - v1 == 5
problem += 7*b1 - 7*g1 + 8*b2 - 8*g2 + u2 - v2 == 7
problem += 4*b1 - 4*g1 + 2*b2 - 2*g2 + u3 - v3 == 9
problem += 3*b1 - 3*g1 + 5*b2 - 5*g2 + u4 - v4 == 3

problem.solve()
for variable in problem.variables():
    print(variable.name, "=", variable.varValue)
print(abs(pulp.value(problem.objective)))

# Результаты решения (совпали с ожидаемыми):
# b1 = 0.64285714
# b2 = 0.21428571
# g1 = 0.0
# g2 = 0.0
# l12 = 0.0
# l13 = 0.0
# l14 = 1.0714286
# l23 = 3.2142857
# l24 = 0.0
# l34 = 0.0
# u1 = 3.0714286
# u2 = 0.78571429
# u3 = 6.0
# u4 = 0.0
# v1 = 0.0
# v2 = 0.0
# v3 = 0.0
# v4 = 0.0
# 5.95714373414285