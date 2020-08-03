#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import statistics
import numbers

from ortools.linear_solver import pywraplp


class RepSchemeGenerator:
    def __init__(self, reps_slack: int = 3, max_diff: int = 1, max_unique: int = 3):
        """Initialize the generator by supplying hard constraints.

        Parameters
        ----------
        reps_slack : int, optional
            Maximum deviation from the repetition goal.
        max_diff : int, optional
            Maximum difference between two consecutive sets.
        max_unique : int, optional
            Maximum unique sets in the solution.
            
        Examples
        --------
        >>> generator = RepSchemeGenerator(reps_slack=0, max_diff=2)
        >>> for result in generator.generate(sets=[2, 3, 4], reps_goal=6):
        ...     print(result)
        (2, 2, 2)
        (2, 4)
        (3, 3)
        >>> generator = RepSchemeGenerator(reps_slack=1, max_diff=2)
        >>> for result in generator.generate(sets=[2, 3, 4], reps_goal=6):
        ...     print(result)
        (2, 2, 2)
        (2, 2, 3)
        (2, 3)
        (2, 4)
        (3, 3)
        (3, 4)
        >>> generator = RepSchemeGenerator(reps_slack=0, max_diff=1, max_unique=1)
        >>> for result in generator.generate(sets=[2, 3, 4], reps_goal=8):
        ...     print(result)
        (2, 2, 2, 2)
        (4, 4)

        """
        assert isinstance(reps_slack, numbers.Integral)
        assert reps_slack >= 0
        assert isinstance(max_diff, numbers.Integral)
        assert max_diff >= 0
        assert isinstance(max_unique, numbers.Integral)
        assert max_unique >= 1

        self.reps_slack = reps_slack
        self.max_diff = max_diff
        self.max_unique = max_unique

    def generate(self, sets: list, reps_goal: int):
        """
        Generate repetition schemes.

        Parameters
        ----------
        sets : list
            A list of allowed repetitions. Unique and sorted.
        reps_goal : int
            The repetition goal.

        Yields
        ------
        Tuples with repetition schemes.

        """
        assert isinstance(reps_goal, numbers.Integral)
        assert reps_goal >= 0
        assert all(s > 0 for s in sets)

        # Store parameters in instance to avoid passing to _generate_sets()
        self.sets = list(sorted(set(sets)))
        self.reps_goal = reps_goal

        # Generate sets and yield them out
        for scheme in self._generate_sets(stack=[]):
            # Prune solutions with too many unique repetitions
            if len(set(scheme)) <= self.max_unique:
                yield scheme

    def _generate_sets(self, i: int = 0, stack=None):
        """Only to be called internally."""
        assert stack is not None, "'stack' should be set to [] by caller."
        assert i >= 0
        assert isinstance(i, numbers.Integral)

        # Yield the result if it's within the allowed range
        if stack and (abs(sum(stack) - self.reps_goal) <= self.reps_slack):
            yield tuple(stack)

        # Stop the recursion if the sum is too high. This prunes the search.
        if sum(stack) > self.reps_goal + self.reps_slack:
            return

        for j in range(i, len(self.sets)):
            if not stack:
                yield from self._generate_sets(i=j, stack=stack + [self.sets[j]])
            else:
                # Prune solutions with too large differences
                # This avoids jumps like e.g. [8, 8, 3, 3]
                if self.sets[j] - stack[-1] <= self.max_diff:
                    yield from self._generate_sets(i=j, stack=stack + [self.sets[j]])


class RepSchemeOptimizer:
    def __init__(self, generator=None):
        """Initialize the optimizer.

        Parameters
        ----------
        generator : callable, optional
            A rep scheme generator with a 'generate' method with signature
            generate(self, sets: list, reps_goal: int). 
            The default when `None` is the RepSchemeGenerator.

        """
        if generator is None:
            self.generator = RepSchemeGenerator()
        else:
            self.generator = generator

        self._cache = dict()

    def _optimize(self, sets: tuple, intensities: tuple, reps_goal: int, intensity_goal: float):
        """Core optimization. Moved to its own method for caching."""

        # Convert data to lists (tuples are used for caching)
        sets = list(sets)
        intensities = list(intensities)

        # Create a mapping
        reps_to_intensity_dict = {r_j: i_j for (r_j, i_j) in zip(sets, intensities)}

        def reps_to_intensity(reps):
            """Map repetitions to intensity, e.g. 8 -> 70."""
            return reps_to_intensity_dict[reps]

        schemes = self.generator.generate(sets=sets, reps_goal=reps_goal)

        def loss(scheme: list):
            """Loss function - smaller is better. Uses 2-norm."""
            reps = sum(scheme)
            intensities = map(reps_to_intensity, scheme)
            intensity = sum(r * i for r, i in zip(scheme, intensities)) / reps
            # No weighting is used here since the units are about the same
            return (reps - reps_goal) ** 2 + (intensity - intensity_goal) ** 2

        # Optimization here is simply going through every feasible solution
        # and choosing the best one. The feasible solution search space is so
        # small that this is fast and efficient, provided that the generator
        # is efficient.
        return list(reversed(min(schemes, key=loss)))

    def __call__(self, sets: tuple, intensities: tuple, reps_goal: int, intensity_goal: float):
        """Use the generator to generate feasible solutions, then optimize."""
        assert isinstance(sets, tuple)
        assert isinstance(intensities, tuple)
        assert reps_goal > 0
        assert intensity_goal > 1
        assert all(i_j > 1 for i_j in intensities)
        assert list(sets) == sorted(sets)

        # Pack the arguments into a tuple for caching
        args = (sets, intensities, reps_goal, intensity_goal)

        # Try to hit the cache. If it fails: compute, store and return.
        try:
            return self._cache[args]
        except KeyError:
            self._cache[args] = self._optimize(*args)
            return self._cache[args]


@functools.lru_cache(maxsize=1024, typed=False)
def optimize_sets(reps, intensities, reps_goal, intensities_goal):
    r"""Get the optimal number of sets.
    
    Introduction
    ------------
    
    This function uses a MIP model to optimize the number of sets in an exercise in a
    strength training program. Novices usually train with SETS x REPS, for instance
    3 x 12 - three sets of twelwe repetitions for some exercise. This is boring and does
    not allow for long-term planning.
    
    Consider a set of avaiable repetitions, {r_j}, and a set of corresponding
    intensities {i_j}. A realistic table might look like:
        
        reps          8     7      6      5      4      3
        intensities   0.7   0.74   0.78   0.82   0.86   0.90
        
    This means that this athlete can perform 6 repetitions at 78% of his/her maximum.
    From these sets we would like to draw reps and intensities to create programs, e.g.,
    
        8 x 0.7   -   6 x 0.78   -   6 x 0.78   -   5 x 0.82
        
    This corresponds to 25 repetitions and a (weighted) average intensity of
    (8 * 0.7 + 6 * 0.78 + 6 * 0.78 + 5 * 0.82) / 25 = 0.7624
    
    Mathematical model
    ------------------
    Let x_j be the number of sets performed with r_j repetitions, and a assume we have
    intensities i_j computed. We use goal programming to balance three constrains:
        
        (1) Number of reps.
            We want \sum_j x_j * r_j = reps_goal. In other words, the total number of
            reps chosen should be close to the goal. We will replace equality with slack
            variables using the goal progamming techniquer.
            
        (2) Average intensity.
            We want (\sum_j x_j * r_j * i_j) / (\sum_j x_j * r_j) = intensities_goal. 
            We rewrite to: (\sum_j x_j * r_j * i_j) = intensities_goal * (\sum_j x_j * r_j)
            Then we use slack variables and goal programming to get close.
            
        (3) Dense solutions.
            We do not want solutions such as x_8 = 2 and x_3 = 4 and every other
            component of x to be zero. The jump from 8 reps to 3 reps is too high for
            the athlete. The first measure taken to ensure this is to maximize the
            density of the solution. We define z_j as
            
                z_j = 1 if x_j >= 1, else z_j = 0
                
            Which is achieved by adding the following constraints for every j:
                
                z_j <= x_j <= M z_j
                M = upper bound on x_j
                z_j \in {0, 1} (binary integer variable)
                
            And then we add -\sum_j z_j to the minimization problem.
            
        (4) Solutions with a small range (i.e. maximum - minimum).
            With the three constrains above, solutions tend to almost always use the 
            entire range, going from .e.g 8 reps to 1 reps very often. It is not 
            desireable to use the entire range of possible repetitions in every workout.
            
            We minimize the range by defining variables `minimum` and `maximum` and 
            adding the constrains
            
                maximum >= z_j * r_j
                minimum <= z_j * r_j + (1 - z_j) * M
                M = upper bound on z_j * r_j
                
            The second constraint is interpreted as "`minimum` is smaller than z_j * r_j
            when z_j = 1 (when x_j >= 1), when z_j = 0 `minimum` is smaller than M".
            Then we add `maximum` - `minimum` to the objective, which we minimize.
            
    We use goal programming on all of these objectives, and we normalize them in a
    sensible way so a user can weight them as he pleases.
    
    Example
    -------
    >>> reps = tuple([8, 7, 6, 5, 4, 3, 2, 1])
    >>> intensities = tuple([0.7, 0.74, 0.78, 0.82, 0.86, 0.9, 0.94, 0.98])
    >>> reps_goal = 25
    >>> intensities_goal = 0.8
    >>> x, data = optimize_sets(reps, intensities, reps_goal, intensities_goal)        
    """
    assert isinstance(reps, tuple)
    assert isinstance(intensities, tuple)
    assert len(reps) == len(intensities)
    assert all(r_j >= 1 for r_j in reps)
    assert all(0 <= i_j <= 1 for i_j in intensities)

    if max(intensities) < intensities_goal:
        # =============================================================================
        #         msg = (
        #             "Cannot reach goal intensity {} with intensities {}. Recasting goal value."
        #         )
        #         warnings.warn(msg.format(intensities_goal, intensities))
        # =============================================================================
        return optimize_sets(reps, intensities, reps_goal, intensities_goal=max(intensities))

    if min(intensities) > intensities_goal:
        # =============================================================================
        #         msg = (
        #             "Cannot reach goal intensity {} with intensities {}. Recasting goal value."
        #         )
        #         warnings.warn(msg.format(intensities_goal, intensities))
        # =============================================================================
        return optimize_sets(reps, intensities, reps_goal, intensities_goal=min(intensities))

    # The loss measure are normalized in the code, so the ratio of these values
    # will prioritize the goals relatively to each other.
    # If a value is set to 0, the solver will not care about it
    penalty_reps = 2.0
    penalty_intensity = 1.0
    reward_density = 1.0
    penality_spread = 0.9

    # =============================================================================
    #     SET UP PROBLEM, SOLVER AND DECISION VARIABLES
    # =============================================================================

    # Create a solver and an objective function
    solver = pywraplp.Solver("solver", pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    objective_function = 0
    INF = solver.infinity()

    # Create decision variables. x_j = number of sets with j reptitions
    x = [solver.IntVar(0, INF, "x_{}".format(r_j)) for r_j in reps]
    # Must choose at least one set
    solver.Add(sum(x) >= 1)

    # =============================================================================
    #     GOAL 1 : REPS AS CLOSE AS POSSIBLE TO DESIRED
    # =============================================================================

    # Set repetition goals
    total_reps = sum(x_j * r_j for (x_j, r_j) in zip(x, reps))

    # Add many linear penalities with increasing 'diff' to create a convex penalty
    for diff in range(10):
        delta = solver.NumVar(0, INF, "slack_reps_{}".format(diff))
        solver.Add(total_reps - reps_goal <= delta + diff)
        solver.Add(reps_goal - total_reps <= delta + diff)
        objective_function += penalty_reps * (delta) / reps_goal

    # =============================================================================
    #     GOAL 2 : INTENSITY AS CLOSE AS POSSIBLE TO DESIRED
    # =============================================================================

    numerator = sum(r_j * x_j * i_j for (r_j, x_j, i_j) in zip(reps, x, intensities))
    denominator = sum(r_j * x_j for (r_j, x_j) in zip(reps, x))

    # Add many linear penalities with increasing 'diff' to create a convex penalty
    for diff in range(10):
        delta = solver.NumVar(0, INF, "slack_intensity_{}".format(diff))
        solver.Add(numerator - intensities_goal * denominator <= delta + diff)
        solver.Add(intensities_goal * denominator - numerator <= delta + diff)
        objective_function += penalty_intensity * (delta) / intensities_goal

    # =============================================================================
    #     GOAL 3: AS DENSE SOLUTION AS POSSIBLE
    # =============================================================================

    # Create binary indicator variables z_j
    # z_j = 1 if and only if x_j >= 1, if not then z_j = 0
    M = 2 * reps_goal
    z = [solver.IntVar(0, 1, "z_{}".format(r_j)) for r_j in reps]
    for x_j, z_j in zip(x, z):
        solver.Add(z_j <= x_j)
        solver.Add(x_j <= M * z_j)

    # Maximize the density of the solution vector
    objective_function -= reward_density * sum(z) / len(intensities)

    # =============================================================================
    #     GOAL 4: AS LITTLE SPREAD (MAX - MIN) AS POSSIBLE
    # =============================================================================

    minimum = solver.NumVar(0, INF, "minimum_reps")
    maximum = solver.NumVar(0, INF, "maximum_reps")
    # This is to prevent numerical issues
    solver.Add(minimum <= maximum)

    for r_j, z_j in zip(reps, z):
        solver.Add(z_j * r_j <= maximum)
        solver.Add(z_j * r_j + (1 - z_j) * M >= minimum)

    denom = max(max(reps) - min(reps), 0.0001)
    objective_function += penality_spread * (maximum - minimum) / denom

    # =============================================================================
    #     SOLVE THE PROBLEM, PARSE THE SOLUTION AND RETURN
    # =============================================================================

    # Minimize the deviation from the goal
    solver.Minimize(objective_function)
    result_status = solver.Solve()

    assert result_status == pywraplp.Solver.OPTIMAL
    assert solver.VerifySolution(1e-7, True)

    x = [x_j.solution_value() for x_j in x]
    z = [z_j.solution_value() for z_j in z]

    # Assert that the property of the z's hold
    for (x_j, z_j) in zip(x, z):
        if z_j == 1:
            assert x_j >= 1
        else:
            assert x_j == 0

    numerator = sum(r_j * x_j * i_j for (r_j, x_j, i_j) in zip(reps, x, intensities))
    denominator = sum(r_j * x_j for (r_j, x_j) in zip(reps, x))

    return (
        x,
        {
            "intensity": round(numerator / denominator, 4),
            "reps": denominator,
            "obj_func_value": round(solver.Objective().Value(), 4),
            "minimum": minimum.solution_value(),
            "maximum": maximum.solution_value(),
        },
    )


def optimize_mealplan(
    meals,
    dietary_constraints,
    meals_limits=None,
    num_days=1,
    num_meals=4,
    time_limit_secs=10,
    epsilon=1e-3,
    weight_price=0.1,
    weight_nutrients=2.0,
    weight_range=0.75,
    params=None,
):
    """Optimize the quantitiy of each meal in a day, given constraints."""

    # =============================================================================
    #     PARSE INPUT ARGUMENTS
    # =============================================================================

    assert isinstance(meals, (list, tuple))
    assert isinstance(dietary_constraints, (dict,))
    assert isinstance(params, (dict,)) or params is None
    assert (meals_limits is None) or isinstance(meals_limits, (list, tuple))

    meals = meals.copy()
    dietary_constraints = dietary_constraints.copy()

    if meals_limits is None:
        meals_limits = [(None, None) for meal in meals]

    if params is None:
        params = dict()

    # A small number such as 0.001. x_ij >= EPSILON <=> z_ij = 1
    EPSILON = epsilon

    expected_daily_price = params.get("expected_daily_price", 75)
    M1 = params.get("M1", 50)  # Upper bound on x_ij
    M2 = params.get("M2", 50)  # Upper bound on x[i][j] * meal.kcal, i.e. calories in a meal

    # A strange bug is that sometime the optimizer will return INFEASIBLE on attempt #1,
    # but calling this function again with the same inputs works. So we allow calling it
    # two times. This is very hacky and not suitable for production, but it works for
    # 'hobby usage'.
    first_call = params.get("first_call", True)

    # Create a solver and an objective function
    solver_name = str(hash(tuple(meals)) + hash((num_days, num_meals)))
    solver = pywraplp.Solver(solver_name, pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    solver.set_time_limit(time_limit_secs * 1000)
    objective_function = 0
    INF = solver.infinity()

    # =============================================================================
    #     ERROR CHECKING AND USER INPUT SANITATION
    # =============================================================================

    # Error checking
    meals_total = num_days * num_meals
    maximum_limit = sum(9999 if high is None else high for (low, high) in meals_limits)
    if maximum_limit < meals_total:
        msg = "Cannot achieve {} totals meals with a total of {} meals."
        raise RuntimeError(msg.format(meals_total, maximum_limit))

    allowed_macros = ("kcal", "protein", "fat", "carbs")
    assert all(key in allowed_macros for key in dietary_constraints.keys())

    assert len(meals_limits) == len(meals)

    # =============================================================================
    #     CREATE VARIABLES
    # =============================================================================

    x = [[None for j in range(num_days)] for i in range(len(meals))]
    z = [[None for j in range(num_days)] for i in range(len(meals))]

    # Loop over every combination of meal and days, create variables
    for i, meal in enumerate(meals):
        for j in range(num_days):
            z[i][j] = solver.IntVar(0, 1, "z_{}{}".format(i, j))

            if meal.discrete:
                x[i][j] = solver.IntVar(0, INF, "x_{}{}".format(i, j))
            else:
                x[i][j] = solver.NumVar(0, INF, "x_{}{}".format(i, j))

            # These constraints ensure that z_ij = 1 iff x_ij >= EPSILON
            solver.Add(EPSILON * z[i][j] <= x[i][j])
            eps = EPSILON / 10
            solver.Add(x[i][j] <= (M1 + eps) * z[i][j] + EPSILON - eps)

    # =============================================================================
    #     CREATE CONSTRAINTS / OBJECTIVE FUNCTION TERM
    # =============================================================================

    # OBJECTIVE FUNCTION TERM 1: Total price of the meals in the program
    denom = expected_daily_price * num_days
    for j in range(num_days):
        daily_price = sum(x[i][j] * meal.price for i, meal in enumerate(meals))
        objective_function += (weight_price / denom) * daily_price

    # OBJECTIVE FUNCTION TERM 2: Deviation from nutrients (on a daily basis)
    for j in range(num_days):
        for macro, (low, high) in dietary_constraints.items():

            # No point in adding any constraints if it's None
            if low is None and high is None:
                continue

            food_macros = [getattr(meal, macro) for meal in meals]

            # Create the sum: sum_i food_i * macro_i
            x_meals = [x[i][j] for i in range(len(meals))]
            total_macro = sum(c * x for x, c in zip(x_meals, food_macros))

            # The maximal deviation in a day is approx mean([low, high]) * nutrients
            # The maximal deviation is the above times the number of days
            denom = statistics.mean([value for value in [low, high] if value is not None])
            denom = denom * num_days  # * len(dietary_constraints)

            # Slack variables related to the lower limit. Only "undershooting" is penalized.
            if low is not None:
                low_positive = solver.NumVar(0, INF, "over_low_lim_" + macro + str(j))
                low_negative = solver.NumVar(0, INF, "under_low_lim_" + macro + str(j))
                solver.Add(total_macro + low_positive - low_negative == low)
                objective_function += (weight_nutrients / denom) * low_positive

            # Slack variables related to the upper limit. Only "overshooting" is penalized.
            if high is not None:
                high_positive = solver.NumVar(0, INF, "over_up_lim_" + macro + str(j))
                high_negative = solver.NumVar(0, INF, "under_upp_lim_" + macro + str(j))
                solver.Add(total_macro + high_positive - high_negative == high)
                objective_function += (weight_nutrients / denom) * high_negative

    # OBJECTIVE FUNCTION TERM 3: Minimal range on calories (on a daily basis)
    for j in range(num_days):
        lower = solver.NumVar(0, INF, "lower_kcal_{}".format(j))
        upper = solver.NumVar(0, INF, "upper_kcal_{}".format(j))

        for i, meal in enumerate(meals):

            solver.Add(lower <= x[i][j] * meal.kcal + (1 - z[i][j]) * M2)
            solver.Add(upper >= x[i][j] * meal.kcal)

        # The maximal spread per day is approximately mean([kcal_low, kcal_high]) / meals
        # The maximal spread is the above times the number of days. Normalize w.r.t this
        denom = statistics.mean([value for value in dietary_constraints["kcal"] if value is not None])
        denom = denom * num_days / num_meals
        objective_function += (weight_range / denom) * (upper - lower)

    # HARD CONSTRAINT 1 : Number of meals per day
    for j in range(num_days):
        solver.Add(sum(z[i][j] for i in range(len(meals))) == num_meals)

    # HARD CONSTRAINT 2: Number of times a food is used
    for i, (meal, (low, high)) in enumerate(zip(meals, meals_limits)):

        times_used = sum(z[i])
        assert len(z[i]) == num_days

        # Add lower limit
        if low is not None:
            if low > num_days:
                msg = "Lower limit on '{}' is {}, but there are {} days."
                raise RuntimeError(msg.format(meal.name, low, num_days))
            solver.Add(times_used >= low)

        # Add upper limit
        if high is not None:
            solver.Add(times_used <= high)

    # =============================================================================
    #     SOLVE THE OPTIMIZATION PROBLEM
    # =============================================================================

    # Minimize the deviation from the goal
    solver.Minimize(objective_function)
    result_status = solver.Solve()
    if result_status == solver.INFEASIBLE:

        if first_call:
            params["first_call"] = False

            return optimize_mealplan(
                meals=meals,
                dietary_constraints=dietary_constraints,
                meals_limits=meals_limits,
                num_days=num_days,
                num_meals=num_meals,
                time_limit_secs=time_limit_secs,
                epsilon=epsilon,
                weight_price=weight_price,
                weight_nutrients=weight_nutrients,
                weight_range=weight_range,
                params=params,
            )

        else:
            raise RuntimeError("Infeasible problem.")

    assert solver.VerifySolution(1e-7, True)

    # =============================================================================
    #     POSTPROCESS THE SOLUTION AND RETURN
    # =============================================================================

    # Parse the variables and get the solution values
    for j in range(num_days):
        for i, meal in enumerate(meals):
            x[i][j] = x[i][j].solution_value()
            z[i][j] = z[i][j].solution_value()

            # Food is chosen
            if z[i][j] > 0.5:
                # If the food is chosen, x_ij is no smaller than epsilon
                x[i][j] = max(x[i][j], EPSILON)
            else:
                x[i][j] = 0

    # Compute the total price
    total_price = 0
    for j in range(num_days):
        daily_price = sum(x[i][j] * meal.price for i, meal in enumerate(meals))
        total_price += daily_price

    return (
        x,
        {
            "obj_func_value": round(solver.Objective().Value(), 6),
            "wall_time": round(solver.wall_time() / 1000, 3),
            "iterations": solver.iterations(),
            "total_price": round(total_price, 1),
        },
    )


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
