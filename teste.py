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
print("IGD", igd.do(a))

hv = get_performance_indicator("hv", ref_point=np.array([1.2, 1.2]))
print("hv", hv.do(a))
