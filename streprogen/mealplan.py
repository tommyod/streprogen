#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 31 18:28:06 2019

@author: tommy
"""
import operator
from os import path

from jinja2 import Environment, FileSystemLoader

from streprogen.optimization import optimize_mealplan
import warnings


class Bunch(dict):
    def __init__(self, *args, **kwds):
        super(Bunch, self).__init__(*args, **kwds)
        self.__dict__ = self


class Mealplan:

    TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")
    TEMPLATE_NAMES = {extension: "mealplan_template." + extension for extension in ["txt"]}

    def __init__(
        self,
        meals,
        dietary_constraints,
        num_meals=4,
        num_days=1,
        meal_limits=None,
        weight_price=0.1,
        weight_nutrients=2.0,
        weight_meal_sizes=0.75,
    ):
        """Initialize a new program.
    
        Parameters
        ----------
        meals
            A list of Meal instances.

        dietary_constraints
            A dict of dietary constraints. The keys can be 'kcal', 'protein', 'fat' or
            'carbs'. The values must be (low, high) limits of the macronutrients, or
            (None, high) to only set an upper limit. Example: {'kcal' : (1600, 1800)}
            
        num_meals
            The number of meals per day. 
            
        num_days
            The number of days in the meal plan.
            
        meal_limits
            A dictionary with keys equal to meal names. The values must be (low, high) 
            and limit the number of times a food can be used. Use (None, high) to only 
            set an upper limit. Example: To have the meal 'bread' at most twice in a
            multi-day meal plan, use {'bread' : (None, 2)}.
            
        weight_price
            Positive number weighting the overall price of the meal plan. 
            A higher value weights this objective higher. 
            This value must be set in relation to the other weights.
            
        weight_nutrients
            Positive number weighting the objective of getting as close as possible to
            satisfying the dietary constraints. A higher value weights this objective 
            higher.  This value must be set in relation to the other weights.
            
        weight_meal_sizes
            Positive number weighting the goal of having equal meal sizes.
            A higher value weights this objective higher. 
            This value must be set in relation to the other weights.
            
        """
        assert num_meals >= 1
        assert num_days >= 1

        self.meals = meals
        self.dietary_constraints = dietary_constraints
        self.num_meals = num_meals
        self.num_days = num_days

        self.weight_price = weight_price
        self.weight_nutrients = weight_nutrients
        self.weight_meal_sizes = weight_meal_sizes

        if meal_limits is None:
            self.meal_limits = dict()
        else:
            self.meal_limits = meal_limits

        # Add None keys if no keys are present
        for meal in self.meals:
            if meal.name not in set(self.meal_limits.keys()):
                self.meal_limits[meal.name] = (None, None)

        assert len(self.meals) == len(self.meal_limits)

        meal_names = set([meal.name for meal in self.meals])
        for key in self.meal_limits.keys():
            if key not in meal_names:
                msg = "`meal_limits` has a key `{}` which is not a meal name."
                warnings.warn(msg.format(key))

        self._rendered = False
        self._set_jinja2_enviroment()

    def render(self, time_limit_secs=5, epsilon=1e-3, params=None):
        """Render the meal plan to perform the calculations.
    
        Parameters
        ----------
        time_limit_secs
            Solver time limit.
            
        epsilon
            Small number used in optimization routine.
            
        params
            Additional low-level parameters used in optimization. See source code.

        """
        limits = [self.meal_limits[meal.name] for meal in self.meals]

        x, optimization_results = optimize_mealplan(
            self.meals,
            self.dietary_constraints,
            meals_limits=limits,
            num_days=self.num_days,
            num_meals=self.num_meals,
            time_limit_secs=time_limit_secs,
            epsilon=epsilon,
            weight_price=self.weight_price,
            weight_nutrients=self.weight_nutrients,
            weight_range=self.weight_meal_sizes,
            params=params,
        )

        self.x = x
        self.optimization_results = optimization_results
        self._rendered = True

        # Parse the results
        self.results = Bunch()
        for attr in ["price", "protein", "fat", "carbs", "kcal"]:
            self.results[attr] = []
        self.results["pretty"] = []

        num_meals = len(x)
        num_days = len(x[0])

        # Store used meals
        self.results["meals"] = set()
        for i in range(len(x)):
            for j in range(len(x[i])):
                if x[i][j] > 0:
                    self.results["meals"].add(self.meals[i])

        self.results["meals"] = list(sorted(self.results["meals"], key=operator.attrgetter("name")))

        def format_qntity(qnty):
            """Format a number."""
            qnty = round(qnty, 1)
            if qnty % 1 == 0:
                qnty = int(qnty)
            return qnty

        for day_num in range(num_days):

            x_day = [x[i][day_num] for i in range(num_meals)]

            result = [(meal, qnty) for (meal, qnty) in zip(self.meals, x_day) if qnty > 0]
            result = sorted(result, key=lambda r: r[0].carbs * r[1], reverse=True)

            self.results[day_num] = dict()
            for attr in ["price", "protein", "fat", "carbs", "kcal"]:
                self.results[day_num][attr] = [getattr(m, attr) * q for (m, q) in result]
                self.results[attr].append(sum(self.results[day_num][attr]))

            # Heuristics to get more carbohydrates earlier in the day
            result = [(meal, format_qntity(qnty)) for (meal, qnty) in result]
            result = [(meal, str(qnty).ljust(3)) for (meal, qnty) in result]
            self.results["pretty"].append(result)

    def _set_jinja2_enviroment(self):
        """
        Set up the jinja2 environment.
        """

        template_loader = FileSystemLoader(searchpath=self.TEMPLATE_DIR)
        env = Environment(loader=template_loader, trim_blocks=True, lstrip_blocks=True)
        # env.globals.update(chunker=chunker, enumerate=enumerate, str=str)

        self.jinja2_environment = env

    def to_txt(self, verbose=False):
        """Write the program information to text, which can be printed in a terminal.

        Parameters
        ----------
        verbose
            If True, more information is shown.

        Returns
        -------
        string
            Meal plan as text.
        """

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["txt"])
        return template.render(mealplan=self, results=self.results, verbose=verbose)

    def to_html(self, verbose=False):
        # TODO: Implement this.
        raise NotImplementedError("Not implemented yet.")

    def to_tex(self, verbose=False):
        # TODO: Implement this.
        raise NotImplementedError("Not implemented yet.")

    def __str__(self):
        """
        String formatting for readable human output.
        """
        return self.to_txt()
