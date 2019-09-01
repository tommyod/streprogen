#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 31 18:28:06 2019

@author: tommy
"""
from jinja2 import Environment, FileSystemLoader
import functools
import statistics
import operator
from os import path

from jinja2 import Environment, FileSystemLoader

from streprogen.utils import (
    chunker,
    escape_string,
    prioritized_not_None,
    round_to_nearest,
)


class Bunch(dict):
    def __init__(self, *args, **kwds):
        super(Bunch, self).__init__(*args, **kwds)
        self.__dict__ = self


from streprogen.optimization import optimize_mealplan

# =============================================================================
#
# def optimize_mealplan(meals, dietary_constraints, *, meals_limits=None, params=None):
#     """Optimize the quantitiy of each meal in a day, given constraints."""
#
#     # =============================================================================
#     #     PARSE INPUT ARGUMENTS
#     # =============================================================================
#
#     assert isinstance(meals, (list, tuple))
#     assert isinstance(dietary_constraints, (dict,))
#     assert isinstance(params, (dict,))
#     assert (meals_limits is None) or isinstance(meals_limits, (list, tuple))
#
#     meals = meals.copy()
#     dietary_constraints = dietary_constraints.copy()
#
#     if meals_limits is None:
#         meals_limits = [(None, None) for meal in meals]
#
#     if params is None:
#         params = dict()
#
#     # Get parameters
#     num_days = params.get("num_days", 1)
#     num_meals = params.get("num_meals", 4)
#     time_limit_secs = params.get("time_limit_secs", 10)
#
#     # A small number such as 0.001. x_ij >= EPSILON <=> z_ij = 1
#     EPSILON = params.get("epsilon", 1e-3)
#
#     # These weights found to be good by in experiments
#     weight_price = params.get("weight_price", 0.1)
#     weight_nutrients = params.get("weight_nutrients", 2.0)
#     weight_range = params.get("weight_range", 0.75)
#
#
# =============================================================================


class Mealplan:

    TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")
    TEMPLATE_NAMES = {
        extension: "mealplan_template." + extension for extension in ["txt"]
    }

    def __init__(
        self,
        meals,
        dietary_constraints,
        num_meals=4,
        num_days=1,
        meal_limits=None,
        weight_price=0.1,
        weight_nutrients=2.0,
        weight_range=0.75,
    ):
        """TODO"""

        self.meals = meals
        self.dietary_constraints = dietary_constraints
        self.num_meals = num_meals
        self.num_days = num_days

        self.weight_price = weight_price
        self.weight_nutrients = weight_nutrients
        self.weight_range = weight_range

        if meal_limits is None:
            self.meal_limits = dict()
            for meal in self.meals:
                self.meal_limits[meal.name] = (None, None)

        self._rendered = False
        self._set_jinja2_enviroment()

    def render(self, time_limit_secs=5, epsilon=1e-3, params=None):

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
            weight_range=self.weight_range,
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

        self.results["meals"] = list(
            sorted(self.results["meals"], key=operator.attrgetter("name"))
        )

        def format_qntity(qnty):
            qnty = round(qnty, 1)
            if qnty % 1 == 0:
                qnty = int(qnty)
            return qnty

        for day_num in range(num_days):

            x_day = [x[i][day_num] for i in range(num_meals)]

            result = [
                (meal, qnty) for (meal, qnty) in zip(self.meals, x_day) if qnty > 0
            ]
            result = sorted(result, key=lambda r: r[0].carbs * r[1], reverse=True)

            self.results[day_num] = dict()
            for attr in ["price", "protein", "fat", "carbs", "kcal"]:
                self.results[day_num][attr] = [
                    getattr(m, attr) * q for (m, q) in result
                ]
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
        env.globals.update(chunker=chunker, enumerate=enumerate, str=str)

        # Add filters to the environment
        round2digits = functools.partial(round_to_nearest, nearest=0.1)
        env.filters["round2digits"] = round2digits
        env.filters["mean"] = statistics.mean

        self.jinja2_environment = env

    def to_txt(self, verbose=False):
        """Write the program information to text,
        which can be printed in a terminal.

        Parameters
        ----------
        verbose
            If True, more information is shown.

        Returns
        -------
        string
            Program as text.
        """

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["txt"])
        return template.render(
            mealplan=self, results=self.results, verbose=verbose, zip=zip
        )

    def __str__(self):
        """
        String formatting for readable human output.
        """
        return self.to_txt()


# =============================================================================
#                 x,
#         {
#             "obj_func_value": round(solver.Objective().Value(), 6),
#             "wall_time": round(solver.wall_time() / 1000, 3),
#             "iterations": solver.iterations(),
#             "total_price": round(total_price, 1),
#         },
# =============================================================================


if __name__ == "__main__":

    from streprogen.diet import Food, Meal

    all_foods = [
        Food(
            name="bacon",
            protein=14.0,
            fat=32.0,
            carbs=1.0,
            kcal=350,
            price_per_product=50.9,
            grams_per_product=400,
        ),
        Food(
            name="burger",
            protein=15.0,
            fat=18.0,
            carbs=2.0,
            kcal=230,
            price_per_product=87.3,
            grams_per_product=800,
        ),
        Food(
            name="coop bratwurst",
            protein=12.0,
            fat=20.0,
            carbs=5.2,
            kcal=253,
            price_per_product=25.9,
            grams_per_product=240,
        ),
        Food(
            name="cottage cheese",
            protein=13.0,
            fat=2.0,
            carbs=2.1,
            kcal=79,
            price_per_product=24.4,
            grams_per_product=400,
        ),
        Food(
            name="egg",
            protein=13.0,
            fat=10.6,
            carbs=0.3,
            kcal=149,
            price_per_product=32.9,
            grams_per_product=690,
        ),
        Food(
            name="frossen kyllingfilet",
            protein=19.0,
            fat=1.8,
            carbs=0.3,
            kcal=94,
            price_per_product=260.0,
            grams_per_product=2500,
        ),
        Food(
            name="grovt brød",
            protein=11.0,
            fat=4.8,
            carbs=36.0,
            kcal=245,
            price_per_product=39.5,
            grams_per_product=750,
        ),
        Food(
            name="gulost",
            protein=27.0,
            fat=27.0,
            carbs=0.0,
            kcal=351,
            price_per_product=110.0,
            grams_per_product=1000,
        ),
        Food(
            name="jasmin ris",
            protein=2.7,
            fat=0.1,
            carbs=31.1,
            kcal=136,
            price_per_product=45.8,
            grams_per_product=1000,
        ),
        Food(
            name="kjøttdeig",
            protein=19.0,
            fat=9.0,
            carbs=0.0,
            kcal=157,
            price_per_product=32.5,
            grams_per_product=400,
        ),
        Food(
            name="lettmelk",
            protein=3.5,
            fat=0.5,
            carbs=4.5,
            kcal=37,
            price_per_product=16.4,
            grams_per_product=1000,
        ),
        Food(
            name="melkesjokolade",
            protein=8.1,
            fat=33.0,
            carbs=55.0,
            kcal=550,
            price_per_product=38.6,
            grams_per_product=200,
        ),
        Food(
            name="musli",
            protein=9.0,
            fat=4.8,
            carbs=63.0,
            kcal=351,
            price_per_product=23.1,
            grams_per_product=750,
        ),
        Food(
            name="PF whey",
            protein=71.8,
            fat=8.1,
            carbs=7.9,
            kcal=377,
            price_per_product=599.0,
            grams_per_product=3000,
        ),
        Food(
            name="svinekotelett dypfryst",
            protein=20.0,
            fat=18.0,
            carbs=0.0,
            kcal=243,
            price_per_product=98.6,
            grams_per_product=2000,
        ),
        Food(
            name="sweet and sour sauce",
            protein=0.4,
            fat=0.2,
            carbs=16.4,
            kcal=71,
            price_per_product=35.0,
            grams_per_product=675,
        ),
        Food(
            name="coop sweet and sour",
            protein=0.6,
            fat=0.1,
            carbs=20,
            kcal=85,
            price_per_product=14.9,
            grams_per_product=500,
        ),
        Food(
            name="nøtti frutti",
            protein=13,
            fat=26,
            carbs=47,
            kcal=464,
            price_per_product=39.7,
            grams_per_product=350,
        ),
        Food(
            name="xtra jasminris",
            protein=7.5,
            fat=0.8,
            carbs=75,
            kcal=343,
            price_per_product=37.4,
            grams_per_product=5000,
        ),
        Food(
            name="currypaste",
            protein=3.9,
            fat=22.3,
            carbs=5.6,
            kcal=262,
            price_per_product=33.2,
            grams_per_product=165,
        ),
        Food(
            name="kokosmelk",
            protein=1.5,
            fat=17,
            carbs=2.4,
            kcal=169,
            price_per_product=13.3,
            grams_per_product=400,
        ),
        Food(
            name="hakkede tomater",
            protein=1,
            fat=0,
            carbs=6.8,
            kcal=34,
            price_per_product=7.1,
            grams_per_product=400,
        ),
        Food(
            name="tomatbønner",
            protein=3.8,
            fat=0.6,
            carbs=14.0,
            kcal=83,
            price_per_product=11.8,
            grams_per_product=420,
        ),
        Food(
            name="yoghurt",
            protein=3.7,
            fat=3.1,
            carbs=10.5,
            kcal=84,
            price_per_product=17.0,
            grams_per_product=600,
        ),
    ]

    foods = {food.name: food for food in all_foods}

    meals = [
        Meal(name="mixed nuts", foods={foods["nøtti frutti"]: 10}, discrete=False),
        Meal(
            name="yogurt w/ muesli",
            foods={foods["yoghurt"]: 150, foods["musli"]: 40},
            discrete=True,
        ),
        Meal(
            name="chicken w/ sweet&sour",
            foods={
                foods["frossen kyllingfilet"]: 40.7,
                foods["coop sweet and sour"]: 11.5,
                foods["jasmin ris"]: 47.8,
            },
            discrete=False,
        ),
        Meal(
            name="hamburger",
            foods={foods["grovt brød"]: 40, foods["burger"]: 80},
            discrete=True,
        ),
        Meal(name="egg", foods={foods["egg"]: 70}, discrete=True),
        Meal(
            name="scoop protein shake",
            foods={foods["PF whey"]: 25, foods["lettmelk"]: 150},
            discrete=False,
        ),
        Meal(
            name="yogurt w/ ct.cheese",
            foods={foods["yoghurt"]: 150, foods["cottage cheese"]: 100},
            discrete=True,
        ),
    ]

    dietary_constraints = {"kcal": (1800, 1800)}
    meal_plan = Mealplan(meals, dietary_constraints, num_days=2)

    meal_plan.render()

    print(meal_plan)

    print(meal_plan.to_txt(verbose=True))
