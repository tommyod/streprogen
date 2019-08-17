#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import warnings
from ortools.linear_solver import pywraplp


@functools.lru_cache(maxsize=128, typed=False)
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
        msg = (
            "Cannot reach goal intensity {} with intensities {}. Recasting goal value."
        )
        warnings.warn(msg.format(intensities_goal, intensities))
        return optimize_sets(
            reps, intensities, reps_goal, intensities_goal=max(intensities)
        )

    if min(intensities) > intensities_goal:
        msg = (
            "Cannot reach goal intensity {} with intensities {}. Recasting goal value."
        )
        warnings.warn(msg.format(intensities_goal, intensities))
        return optimize_sets(
            reps, intensities, reps_goal, intensities_goal=min(intensities)
        )

    # The loss measure are normalized in the code, so the ratio of these values
    # will prioritize the goals relatively to each other.
    # If a value is set to 0, the solver will not care about it
    penalty_reps = 1.0
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
    delta_pos = solver.NumVar(0, INF, "slack_reps_+")
    delta_neg = solver.NumVar(0, INF, "slack_reps_-")
    total_reps = sum(x_j * r_j for (x_j, r_j) in zip(x, reps))

    solver.Add(total_reps + delta_pos - delta_neg == reps_goal)
    objective_function += penalty_reps * (delta_pos + delta_neg) / reps_goal

    # =============================================================================
    #     GOAL 2 : INTENSITY AS CLOSE AS POSSIBLE TO DESIRED
    # =============================================================================

    # Set intensity
    delta_pos = solver.NumVar(0, INF, "slack_intensity_+")
    delta_neg = solver.NumVar(0, INF, "slack_intensity_-")

    numerator = sum(r_j * x_j * i_j for (r_j, x_j, i_j) in zip(reps, x, intensities))
    denominator = sum(r_j * x_j for (r_j, x_j) in zip(reps, x))

    solver.Add(numerator + delta_pos - delta_neg == intensities_goal * denominator)

    denom = max(intensities_goal - min(intensities), 0.0001)
    objective_function += penalty_intensity * delta_pos / denom

    denom = max(max(intensities) - intensities_goal, 0.0001)
    objective_function += penalty_intensity * delta_neg / denom

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


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])
