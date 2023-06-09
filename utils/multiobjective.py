from collections import defaultdict 
from collections.abc import Iterable
import random

import numpy as np

from utils.misc import array_to_float


# Code adapted from:
# https://medium.com/@rossleecooloh/optimization-algorithm-nsga-ii-and-python-package-deap-fca0be6b2ffc

def dominates(obj1, obj2, sign=None):
    """Return true if each objective of *self* is not strictly worse than
            the corresponding objective of *other* and at least one objective is
            strictly better.
        **no need to care about the equal cases
        (Cuz equal cases mean they are non-dominators)
    :param obj1: a list of multiple objective values
    :type obj1: numpy.ndarray
    :param obj2: a list of multiple objective values
    :type obj2: numpy.ndarray
    :param sign: target types. positive means maximize and otherwise minimize.
    :type sign: list
    """

    num_objectives = len(obj1)

    if sign is None:
        sign = [1] * num_objectives
    elif not isinstance(sign, Iterable):
        sign = [sign] * num_objectives

    indicator = False
    for a, b, sign in zip(obj1, obj2, sign):
        if a * sign > b * sign:
            indicator = True
        # if one of the objectives is dominated, then return False
        elif a * sign < b * sign:
            return False
    return indicator


def sort_nondominated(fitness, k=None, first_front_only=False, include_repetition=True, sign=None):
    """Sort the first *k* *individuals* into different nondomination levels
        using the "Fast Nondominated Sorting Approach" proposed by Deb et al.,
        see [Deb2002]_. This algorithm has a time complexity of :math:`O(MN^2)`,
        where :math:`M` is the number of objectives and :math:`N` the number of
        individuals.
        :param individuals: A list of individuals to select from.
        :param k: The number of individuals to select.
        :param first_front_only: If :obj:`True` sort only the first front and
                                    exit.
        :param sign: indicate the objectives are maximized or minimized
        :returns: A list of Pareto fronts (lists), the first list includes
                    nondominated individuals.
        .. [Deb2002] Deb, Pratab, Agarwal, and Meyarivan, "A fast elitist
            non-dominated sorting genetic algorithm for multi-objective
            optimization: NSGA-II", 2002.
    """
    if k is None:
        k = len(fitness)

    # Use objectives as keys to make python dictionary
    map_fit_ind = defaultdict(list)
    for i, f_value in enumerate(fitness):  # fitness = [(1, 2), (2, 2), (3, 1), (1, 4), (1, 1)...]
        map_fit_ind[tuple(f_value)].append(i)
    fits = list(map_fit_ind.keys())  # fitness values

    current_front = []
    next_front = []
    dominating_fits = defaultdict(int)  # n (The number of people dominate you)
    dominated_fits = defaultdict(list)  # Sp (The people you dominate)

    # Rank first Pareto front
    # *fits* is a iterable list of chromosomes. Each has multiple objectives.
    for i, fit_i in enumerate(fits):
        for fit_j in fits[i + 1:]:
            # Eventhougn equals or empty list, n & Sp won't be affected
            if dominates(fit_i, fit_j, sign):
                dominating_fits[fit_j] += 1
                dominated_fits[fit_i].append(fit_j)
            elif dominates(fit_j, fit_i, sign):
                dominating_fits[fit_i] += 1
                dominated_fits[fit_j].append(fit_i)
        if dominating_fits[fit_i] == 0:
            current_front.append(fit_i)

    fronts = [[]]  # The first front
    for fit in current_front:
        if include_repetition:
            fronts[-1].extend(map_fit_ind[fit])
        else:
            fronts[-1].append(map_fit_ind[fit][0])
    pareto_sorted = len(fronts[-1])

    # Rank the next front until all individuals are sorted or
    # the given number of individual are sorted.
    # If Sn=0 then the set of objectives belongs to the next front
    if not first_front_only:  # first front only
        N = min(len(fitness), k)
        while pareto_sorted < N:
            fronts.append([])
            for fit_p in current_front:
                # Iterate Sn in current fronts
                for fit_d in dominated_fits[fit_p]:
                    dominating_fits[fit_d] -= 1  # Next front -> Sn - 1
                    if dominating_fits[fit_d] == 0:  # Sn=0 -> next front
                        next_front.append(fit_d)
                         # Count and append chromosomes with same objectives
                        pareto_sorted += len(map_fit_ind[fit_d])

                        if include_repetition:
                            fronts[-1].extend(map_fit_ind[fit_d])
                        else:
                            fronts[-1].append(map_fit_ind[fit_d][0])
            current_front = next_front
            next_front = []

    return fronts


def crowding_dist(fitness=None):
    """
    :param fitness: A list of fitness values
    :return: A list of crowding distances of chrmosomes

    The crowding-distance computation requires sorting the population according to each objective function value
    in ascending order of magnitude. Thereafter, for each objective function, the boundary solutions (solutions with smallest and largest function values)
    are assigned an infinite distance value. All other intermediate solutions are assigned a distance value equal to
    the absolute normalized difference in the function values of two adjacent solutions.
    """

    # initialize list: [0.0, 0.0, 0.0, ...]
    distances = [0.0] * len(fitness)
    crowd = [(f_value, i) for i, f_value in enumerate(fitness)]  # create keys for fitness values

    n_obj = len(fitness[0])

    for i in range(n_obj):  # calculate for each objective
        crowd.sort(key=lambda element: element[0][i])
        # After sorting,  boundary solutions are assigned Inf
        # crowd: [([obj_1, obj_2, ...], i_0), ([obj_1, obj_2, ...], i_1), ...]
        distances[crowd[0][1]] = float("inf")
        distances[crowd[-1][1]] = float("inf")
        if crowd[-1][0][i] == crowd[0][0][i]:  # If objective values are same, skip this loop
            continue
        # normalization (max - min) as Denominator
        norm = float(crowd[-1][0][i] - crowd[0][0][i])
        # crowd: [([obj_1, obj_2, ...], i_0), ([obj_1, obj_2, ...], i_1), ...]
        # calculate each individual's Crowding Distance of i th objective
        # technique: shift the list and zip
        for prev, cur, next in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            distances[cur[1]] += (next[0][i] - prev[0][i]) / norm  # sum up the distance of ith individual along each of the objectives

    return distances


def nsga_ii_tourn(fit0, fit1, crowd_dist0, crowd_dist1):
    if dominates(fit0, fit1):
        return 0
    elif dominates(fit0, fit1):
        return 1

    if crowd_dist0 < crowd_dist1:
        return 0
    elif crowd_dist1 < crowd_dist0:
        return 1

    if random.random() <= 0.5:
        return 0
    return 1


def fitness_sch(individual, instance, student, timer, print_results=False, data=None, **kwargs):
    value = array_to_float(individual, 10)

    f1 = value ** 2
    f2 = (value - 2) ** 2

    objective = (f1, f2)

    if data is not None:
        data.append(objective)

    if print_results:
        print("Individuo:")
        print(individual)
        print("Objetivos: [{}, {}]".format(f1, f2))

    return objective
