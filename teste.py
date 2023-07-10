import numpy as np
from pymoo.factory import get_problem
from pymoo.visualization.scatter import Scatter
from pymoo.factory import get_performance_indicator
from pymoo.factory import get_performance_indicator

# The pareto front of a scaled zdt1 problem
pf = get_problem("zdt1").pareto_front()

# The result found by an algorithm
a = pf[::10] * 1.1

igd = get_performance_indicator("igd", pf)
valor1 = igd.do(a)
print("IGD", valor1)

hv = get_performance_indicator("hv", ref_point=np.array([1.2, 1.2]))
valor2 = hv.do(a)
print("hv", valor2)
