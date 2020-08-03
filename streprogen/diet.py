#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data classes for optimizing meals.
"""
import warnings

# =============================================================================
# CLASSES - Used to store data and ease computations in hierarchical data
# =============================================================================


class Food:
    """
    A food consists of a name and nutritional data given in units of 100 grams.
    
    Examples
    --------
    >>> eggs = Food(name='eggs', protein=13.0, fat=10.6, carbs=0.3, kcal=149, 
    ...             price_per_product=32.9, grams_per_product=690)
    >>> eggs.price
    4.768115942028985
    >>> eggs.name
    'eggs'
    >>> eggs.kcal
    149
    """

    def __init__(self, name, protein, fat, carbs, kcal, price_per_product, grams_per_product):
        """TODO"""
        self.name = name
        self.protein = protein
        self.fat = fat
        self.carbs = carbs
        self.kcal = kcal
        self.price_per_product = price_per_product
        self.grams_per_product = grams_per_product

        self._verify()

    @property
    def price(self):
        return self.price_per_product / self.grams_per_product * 100

    def _verify(self):
        """Verify the relationship between macros and kcal."""
        computed_kcal = 4 * self.protein + 4 * self.carbs + 9 * self.fat
        relative_error = abs((self.kcal - computed_kcal) / computed_kcal)
        if relative_error > 0.1:
            msg = "Got a {} % error on kcal: '{}'."
            warnings.warn(msg.format(round(relative_error * 100, 1), self.name))

    def __repr__(self):
        name = type(self).__name__
        args = ("{}={}".format(arg, value) for (arg, value) in self.__dict__.items())
        args = ", ".join(args)

        return name + "({})".format(args)

    def __hash__(self):
        return hash((self.name, self.protein, self.fat, self.carbs, self.kcal))


class Meal:
    """
    A meal consists of several foods given at some "base" unit of grams. In the example
    below 'eggs' is the general food, an a meal consists of discrete units of eggs,
    weighing approximately 65 grams each.
    
    Examples
    --------
    >>> eggs = Food(name='eggs', protein=13.0, fat=10.6, carbs=0.3, kcal=149, 
    ...             price_per_product=32.9, grams_per_product=690)
    >>> egg = Meal(name='egg', foods={eggs:65}, discrete=True)
    >>> egg.price # price of the meal
    3.0992753623188407
    """

    # Foods are added as: foods={all_foods["lettmelk"]:100, all_foods["musli"]:100}
    # This means that a baseline

    def __init__(self, name, foods, discrete=True):

        self.name = name
        self.foods = foods
        self.discrete = discrete
        if self.kcal < 10:
            warnings.warn("Food only has {} calories.".format(self.kcal))

    def __getattr__(self, key):
        """Allow accessing attributes of foods, summing over them."""
        return sum(getattr(food, key) * quantity / 100 for (food, quantity) in self.foods.items())

    @property
    def grams(self):
        return int(sum(self.foods.values()))

    def __hash__(self):
        return hash(self.name) + hash(frozenset(self.foods.keys()))

    def __iter__(self):
        return iter(self.foods.keys())

    def __copy__(self):
        return type(self)(name=self.name, foods=self.foods.copy(), discrete=self.discrete)

    def __str__(self):
        name = type(self).__name__
        foods_names = (
            "{" + ", ".join("{}g {}".format(quantity, food.name) for food, quantity in self.foods.items()) + "}"
        )
        return name + "(name='{}', grams={}, foods={})".format(self.name, self.grams, foods_names)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[__file__, "--doctest-modules", "-v", "--capture=sys"])
