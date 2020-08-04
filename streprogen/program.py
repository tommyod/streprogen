#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import statistics
import warnings
import numbers
import time
import typing
from os import path

from jinja2 import Environment, FileSystemLoader

from streprogen.day import Day
from streprogen.exercises import DynamicExercise, StaticExercise
from streprogen.modeling import (
    progression_diffeq,
    reps_to_intensity,
)
from streprogen.optimization import RepSchemeOptimizer
from streprogen.utils import (
    chunker,
    escape_string,
    prioritized_not_None,
    round_to_nearest,
)


class Program(object):
    """The program class is a container for days and exercises, along with 
    the methods and functions used to create training programs."""

    REP_SET_SEP = " x "
    TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")
    TEMPLATE_NAMES = {extension: "program_template." + extension for extension in ["html", "txt", "tex"]}

    # Default functions
    _default_rep_scaler_func = staticmethod(
        functools.partial(progression_diffeq, start_weight=1 + 0.2, final_weight=1 - 0.2, start_week=1, k=0,)
    )
    _default_intensity_scaler_func = staticmethod(
        functools.partial(progression_diffeq, start_weight=1 - 0.05, final_weight=1 + 0.05, start_week=1, k=0,)
    )

    _default_reps_to_intensity_func = staticmethod(reps_to_intensity)
    _default_progression_func = staticmethod(functools.partial(progression_diffeq, k=1))

    def __init__(
        self,
        name: str = "Untitled",
        duration: int = 8,
        reps_per_exercise: int = 25,
        min_reps: int = 3,
        max_reps: int = 8,
        rep_scaler_func: typing.Callable[[int], float] = None,
        intensity: float = 83,
        intensity_scaler_func: typing.Callable[[int], float] = None,
        units: str = "kg",
        round_to: float = 2.5,
        percent_inc_per_week: float = 1.5,
        progression_func: typing.Callable = None,
        reps_to_intensity_func: typing.Callable[[int], float] = None,
        verbose: bool = False,
    ):

        """Initialize a new program.


        Parameters
        ----------
        name
            The name of the training program, e.g. 'TommyAugust2017'.

        duration
            The duration of the training program in weeks, e.g. 8.

        reps_per_exercise
            The baseline number of repetitions per dynamic exercise.
            Typically a value in the range [15, 30].
            
        min_reps
            The minimum number of repetitions for the exercises, e.g. 3.
            This value can be set globally for the program, or for a specific
            dynamic exercise. If set at the dynamic exercise level, it will
            override the global program value.
            
        max_reps
            The maximum number of repetitions for the exercises, e.g. 8.
            This value can be set globally for the program, or for a specific
            dynamic exercise. If set at the dynamic exercise level, it will
            override the global program value.

        rep_scaler_func
            A function mapping from a week in the range [1, `duration`] to a scaling
            value (factor). The scaling value will be multiplied with the 
            `reps_per_exercise` parameter for that week. Should typically return factors
            between 0.7 and 1.3.

        intensity
            The baseline intensity for each dynamic exercise. The intensity
            of an exercise for a given week is how heavy the average
            repetition is compared to the expected 1RM (max weight one can
            lift) for that given week. Typically a value around 80.

        intensity_scaler_func
            A function mapping from a week in the range [1, `duration`] to a scaling
            value (factor). The scaling value will be multiplied with the 
            `intensity` parameter for that week. 
            Should typically return factors between 0.9 and 1.1.

        units
            The units used for exporting and printing the program, e.g. 'kg'.

        round_to
            Round the dynamic exercise to the nearest multiple of this
            parameter. Typically 2.5, 5 or 10.
            This value can be set globally for the program, or for a specific
            dynamic exercise. If set at the dynamic exercise level, it will
            override the global program value.

        percent_inc_per_week
            If `final_weight` is not set, this value will be used. Percentage
            increase per week can be set globally for the program, or for each
            dynamic exercise. If set at the dynamic exercise level, it will
            override the global program value. The increase is  additive, not 
            multipliactive. For instance, if the increase is set to 
            `percent_inc_per_week=2`, then after 2 weeks the increase is 4, 
            not (1.02 * 1.02 - 1) * 100 = 4.04. The `final_weight` parameter 
            must be set to `None` for this parameter to have effect.

        progression_func
            The function used to model overall 1RM progression in the
            training program. The function must have a signature like:
                func(week, start_weight, final_weight, start_week, end_week)

        reps_to_intensity_func
            The function used to model the relationship between repetitions
            and intensity. Maps from a repetition to an intensity in the range 0-100.

        verbose
            If True, information will be outputted as the program is created.


        Returns
        -------
        Program
            A Program instance.
    
    
        Examples
        -------
        >>> program = Program('My training program')
        >>> program._rendered
        False

        """
        self.name = escape_string(name)

        assert isinstance(duration, numbers.Integral) and duration > 1
        self.duration = duration

        assert isinstance(reps_per_exercise, numbers.Integral) and reps_per_exercise > 0
        self.reps_per_exercise = reps_per_exercise

        assert isinstance(min_reps, numbers.Integral) and min_reps > 0
        assert isinstance(max_reps, numbers.Integral) and max_reps > 0
        self.min_reps = min_reps
        self.max_reps = max_reps
        if self.min_reps and self.max_reps:
            if self.min_reps > self.max_reps:
                raise ValueError("'min_reps' larger than 'max_reps'")

        assert isinstance(intensity, numbers.Number) and intensity > 0
        self.intensity = intensity

        assert isinstance(units, str)
        self.units = units
        self.round = functools.partial(round_to_nearest, nearest=round_to)
        self.verbose = verbose

        # Set functions to user supplied, or defaults if None was passed
        user, default = (
            rep_scaler_func,
            functools.partial(self._default_rep_scaler_func, final_week=self.duration),
        )
        self.rep_scaler_func = prioritized_not_None(user, default)
        assert callable(self.rep_scaler_func)

        user, default = (
            intensity_scaler_func,
            functools.partial(self._default_intensity_scaler_func, final_week=self.duration),
        )
        self.intensity_scaler_func = prioritized_not_None(user, default)
        assert callable(self.intensity_scaler_func)

        user, default = progression_func, self._default_progression_func
        self.progression_func = prioritized_not_None(user, default)
        assert callable(self.progression_func)

        user, default = reps_to_intensity_func, self._default_reps_to_intensity_func
        self.reps_to_intensity_func = prioritized_not_None(user, default)
        assert callable(self.reps_to_intensity_func)

        # Setup variables that the user has no control over
        self.days = []
        self.active_day = None  # Used for Program.Day context manager API
        self._rendered = False
        self._set_jinja2_enviroment()

        assert isinstance(percent_inc_per_week, numbers.Number)
        self.percent_inc_per_week = percent_inc_per_week

        # TODO: make explicit
        self.optimizer = RepSchemeOptimizer()

    def Day(self, name=None):
        day = Day(name=name)
        day.program = self
        return day

    def DynamicExercise(
        self,
        name,
        start_weight=None,
        final_weight=None,
        min_reps=None,
        max_reps=None,
        percent_inc_per_week=None,
        reps=None,
        intensity=None,
        round_to=None,
    ):
        ex = DynamicExercise(
            name, start_weight, final_weight, min_reps, max_reps, percent_inc_per_week, reps, intensity, round_to,
        )
        self.active_day.dynamic_exercises.append(ex)
        return ex

    def StaticExercise(self, name, sets_reps="4 x 10"):
        ex = StaticExercise(name, sets_reps)
        self.active_day.static_exercises.append(ex)
        return ex

    def _validate(self):
        """
        The purpose of this method is to verify that the user has set sensible
        values for the training program before rendering. The user will still
        be able to render, but error messages will be printed. This method:
            
            * Validates that the average intensity is in the range [65, 85].
            * Validates that the number of repetitions is in the range [15, 45].
            * Validates that 'reps_to_intensity_func' maps to [0, 100].
            * Validates that 'reps_to_intensity_func' is a decreasing function.
            * Validates that the exercises do not grow too much.
            
        Apart from these sanity checks, the user is on their own.
        """
        weeks = list(range(1, self.duration + 1))

        # Validate the intensity
        intensities = [self.intensity_scaler_func(w) * self.intensity for w in weeks]

        if max(intensities) > 90:
            warnings.warn("\nWARNING: Average intensity is > 90.")

        if min(intensities) < 65:
            warnings.warn("\nWARNING: Average intensity is < 65.")

        # Validate the repetitions
        repetitions = [self.rep_scaler_func(w) * self.reps_per_exercise for w in weeks]
        if max(repetitions) > 45:
            warnings.warn("\nWARNING: Number of repetitions > 45.")

        if min(repetitions) < 15:
            warnings.warn("\nWARNING: Number of repetitions < 15.")

        # Validate the 'reps_to_intensity_func'
        for x1, x2 in zip(range(1, 20), range(2, 21)):
            y1 = self.reps_to_intensity_func(x1)
            y2 = self.reps_to_intensity_func(x2)
            if y1 < y2:
                warnings.warn("\n'reps_to_intensity_func' is not decreasing.")

        if any(self.reps_to_intensity_func(x) > 100 for x in range(1, 20)):
            warnings.warn("\n'reps_to_intensity_func' maps to > 100.")

        if any(self.reps_to_intensity_func(x) < 0 for x in range(1, 20)):
            warnings.warn("\n'reps_to_intensity_func' maps to < 0.")

        # Validate the exercises
        for day in self.days:

            ex_names = set()

            for dynamic_ex in day.dynamic_exercises:

                if dynamic_ex.name in ex_names:
                    raise ValueError(f"Exercise name not unique: {dynamic_ex.name}")
                else:
                    ex_names.add(dynamic_ex.name)

                percentage_growth = dynamic_ex.weekly_growth(self.duration, self.percent_inc_per_week)
                if percentage_growth > 4:
                    msg = '\n"{}" grows with {}% each week.'.format(dynamic_ex.name, percentage_growth)
                    warnings.warn(msg)

    def add_days(self, *days):
        """Add one or several days to the program.
    
        Parameters
        ----------
        *days
            Unpacked tuple containing
            :py:class:`streprogen.Day` instances.
    
    
        Examples
        -------
        >>> program = Program('My training program')
        >>> day1, day2 = Day(), Day()
        >>> program.add_days(day1, day2)
        >>> program.add_days(day1)
        """
        self.days.extend(days)

    def _render_dynamic(self, dynamic_exercise, desired_reps, desired_intensity, validate):
        """
        Render a single dynamic exercise.
        This is done for each exercise every week.
        """

        sets = tuple(range(dynamic_exercise.min_reps, dynamic_exercise.max_reps + 1))
        intensities = tuple(map(self.reps_to_intensity_func, sets))

        reps = self.optimizer(
            sets=sets, intensities=intensities, reps_goal=desired_reps, intensity_goal=desired_intensity
        )

        intensities = list(map(self.reps_to_intensity_func, reps))

        # If repetitions are too high, a low average intensity cannot be attained
        int_highest = self.reps_to_intensity_func(dynamic_exercise.min_reps)
        int_lowest = self.reps_to_intensity_func(dynamic_exercise.max_reps)

        if (not (int_lowest - 0.1 <= desired_intensity <= int_highest + 0.1)) and validate:
            msg = """WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}].
This maps to intensities in the range [{}, {}], but the goal average intensity is {},
which is not achievable with this rep range.
SOLUTION: Either (1) change the repetition range, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(
                dynamic_exercise.name,
                dynamic_exercise.min_reps,
                dynamic_exercise.max_reps,
                round(int_lowest, 1),
                round(int_highest, 1),
                round(desired_intensity, 1),
            )
            warnings.warn(msg)

        return {"reps": reps, "intensities": intensities}

    def _initialize_render_dictionary(self):
        """Initialize a dictionary for rendered values.
    
        Examples
        -------
        >>> program = Program('My training program')
        >>> program._initialize_render_dictionary()
        >>> program._rendered is False
        False
        """

        self._rendered = dict()

        # Iterate over all weeks
        for week in range(1, self.duration + 1):
            self._rendered[week] = dict()

            # Iterate over all days
            for day in self.days:
                self._rendered[week][day] = dict()

                # Iterate over all main exercises
                for dynamic_ex in day.dynamic_exercises:
                    self._rendered[week][day][dynamic_ex] = dict()

    def _yield_week_day_dynamic(self):
        """A helper function to reduce the number of nested loops.

        Yields
        -------
        tuple
            A tuple with (week, day, dynamic_ex).

        """
        # Iterate over all weeks
        for week in range(1, self.duration + 1):
            # Iterate over all days
            for day in self.days:
                # Iterate over all main exercises
                for dynamic_ex in day.dynamic_exercises:
                    yield (week, day, dynamic_ex)

    def _yield_week_day(self, enumeration=False):
        """A helper function to reduce the number of nested loops.
        
        Parameters
        ----------
        enumeration
            Whether or not to wrap the days in enumerate().
            
    
        Yields
        -------
        tuple
            A tuple with (week, day_index, day) or (week, day),
            depending on 'enumeration' parameter.

        """
        if enumeration:
            # Iterate over all weeks
            for week in range(1, self.duration + 1):
                # Iterate over all days
                for day_index, day in enumerate(self.days):
                    yield (week, day_index, day)
        else:
            # Iterate over all weeks
            for week in range(1, self.duration + 1):
                # Iterate over all days
                for day in self.days:
                    yield (week, day)

    def _yield_dynamic_exercises(self):
        """A helper function to reduce the number of nested loops.


        Yields
        -------
        :py:class:`streprogen.DynamicExercise`
            Yields the dynamic exercises in the program.

        """
        for day in self.days:
            for dynamic_ex in day.dynamic_exercises:
                yield dynamic_ex

    def _yield_exercises(self):
        """A helper function to reduce the number of nested loops.
        

        Yields
        -------
        (dynamic_ex) or (static_ex)
            Yields the exercises in the program.

        """
        for day in self.days:
            for dynamic_ex in day.dynamic_exercises:
                yield dynamic_ex
            for static_ex in day.static_exercises:
                yield static_ex

    def render(self, validate=True):
        """Render the training program to perform the calculations.
        The program can be rendered several times to produce new
        information given the same input parameters.
    
        Parameters
        ----------
        validate
            Boolean that indicates whether or not to run a validation
            heurestic on the program before rendering. The validation
            will warn the user if inputs seem unreasonable.

        """
        start_time = time.time()

        # --------------------------------
        # Prepare for rendering the dynamic exercises
        # --------------------------------

        # Initialize the structure of the _rendered dictionary
        self._initialize_render_dictionary()

        # Set the day names
        for i, day in enumerate(self.days):
            day.name = prioritized_not_None(day.name, "Day {}".format(i + 1))

        # Validate the program if the user wishes to validate
        if validate:
            self._validate()

        # --------------------------------
        # Render the dynamic exercises
        # --------------------------------

        for (week, day, dyn_ex) in self._yield_week_day_dynamic():

            # Set min and max reps from program, if not set on exercise
            dyn_ex.min_reps = prioritized_not_None(dyn_ex.min_reps, self.min_reps)
            dyn_ex.max_reps = prioritized_not_None(dyn_ex.max_reps, self.max_reps)

            if dyn_ex.min_reps > dyn_ex.max_reps:
                msg = "'min_reps' larger than 'max_reps' for exercise '{}'."
                raise ValueError(msg.format(dyn_ex.name))

            # Use the local rounding function if available,
            # if not use the global rounding function
            round_func = prioritized_not_None(dyn_ex.round, self.round)

            # The desired repetitions to work up to
            local_r, global_r = dyn_ex.reps, self.reps_per_exercise
            total_reps = prioritized_not_None(local_r, global_r)
            desired_reps = round(total_reps * self.rep_scaler_func(week))
            self._rendered[week][day][dyn_ex]["desired_reps"] = int(desired_reps)

            # The desired average intensity
            local_i, global_i = dyn_ex.intensity, self.intensity
            intensity_unscaled = prioritized_not_None(local_i, global_i)
            scale_factor = self.intensity_scaler_func(week)
            desired_intensity = intensity_unscaled * scale_factor
            self._rendered[week][day][dyn_ex]["desired_intensity"] = desired_intensity

            # A dictionary is returned with keys 'reps' and 'intensities'
            render_args = dyn_ex, desired_reps, desired_intensity, validate
            out = self._render_dynamic(*render_args)

            # Get increase from program if not available on the exercise
            inc_week = prioritized_not_None(dyn_ex.percent_inc_per_week, self.percent_inc_per_week)

            # Case 1: Start weight and final weight is given
            if (dyn_ex.start_weight is not None) and (dyn_ex.final_weight is not None):
                start_w, final_w = dyn_ex.start_weight, dyn_ex.final_weight

            # Case 2: Start weight and increase is given
            elif (dyn_ex.start_weight is not None) and (inc_week is not None):
                factor = 1 + (inc_week / 100) * self.duration
                dyn_ex.final_weight = dyn_ex.start_weight * factor
                start_w, final_w = dyn_ex.start_weight, dyn_ex.final_weight

            # Case 3: Final weight and increase is given
            elif (dyn_ex.final_weight is not None) and (inc_week is not None):
                factor = 1 + (inc_week / 100) * self.duration
                dyn_ex.start_weight = dyn_ex.final_weight / factor
                start_w, final_w = dyn_ex.start_weight, dyn_ex.final_weight

            else:
                raise Exception(f"Exercise {dyn_ex} is overspecified.")

            weight = self.progression_func(week, start_w, final_w, 1, self.duration)
            if weight > max(start_w, final_w) or weight < min(start_w, final_w):
                msg = "Weight for '{dyn_ex}' was {round(weight, 1)} in week {week}. "
                msg += "This is out of bounds. Start weight is {round(start_w, 1)}. "
                msg += "Final weight is {round(start_w, 1)}."

            # Define a function to prettify the weights
            def pretty_weight(weight, i, round_function):
                weight = round_function(weight * i / 100)
                if weight % 1 == 0:
                    return int(weight)
                return weight

            # Create pretty strings
            tuple_generator = zip(out["intensities"], out["reps"])
            pretty_gen = (
                (str(r), str(pretty_weight(weight, i, round_func)) + self.units) for (i, r) in tuple_generator
            )
            out["strings"] = list(self.REP_SET_SEP.join(list(k)) for k in pretty_gen)

            # Update with the ['intensities', 'reps', 'strings'] keys
            self._rendered[week][day][dyn_ex].update(out)

        if self.verbose:
            delta_time = round(time.time() - start_time, 3)
            print(f"Rendered program in {delta_time} seconds.")

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

    def to_html(self, table_width=5):
        """Write the program information to HTML code, which can be saved,
        printed and brought to the gym.

        Parameters
        ----------
        table_width
            The table with of the HTML code.

        Returns
        -------
        string
            HTML code.
        """

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["html"])
        return template.render(program=self, table_width=table_width)

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
        # Get information related to formatting
        exercises = list(self._yield_exercises())
        max_ex_name = 0
        if exercises:
            max_ex_name = max(len(ex.name) for ex in exercises)

        # If rendered, find the length of the longest '6 x 75kg'-type string
        max_ex_scheme = 0
        if self._rendered:
            for (week, day, dynamic_ex) in self._yield_week_day_dynamic():
                lengths = [len(s) for s in self._rendered[week][day][dynamic_ex]["strings"]]
                max_ex_scheme = max(max_ex_scheme, max(lengths))

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["txt"])
        return template.render(program=self, max_ex_name=max_ex_name, max_ex_scheme=max_ex_scheme, verbose=verbose,)

    def to_tex(self, text_size="large", table_width=5, clear_pages=False):
        r"""
        Write the program information to a .tex file, which can be
        rendered to .pdf running pdflatex. The program can then be
        printed and brought to the gym.

        Parameters
        ----------
        text_size
            The tex text size, e.g. '\small', 'normalsize', 'large', 'Large'
            or 'LARGE'.

        table_width
            The table width of the .tex code.
        
        clear_pages
            If True, the page will be cleared after each week is printed.

        Returns
        -------
        string
            Program as tex.
        """

        # If rendered, find the length of the longest '6 x 75kg'-type string
        max_ex_scheme = 0
        if self._rendered:
            for (week, day, dynamic_ex) in self._yield_week_day_dynamic():
                lengths = [len(s) for s in self._rendered[week][day][dynamic_ex]["strings"]]
                max_ex_scheme = max(max_ex_scheme, max(lengths))

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["tex"])

        return template.render(program=self, text_size=text_size, table_width=table_width, clear_pages=clear_pages,)

    def __str__(self):
        """
        String formatting for readable human output.
        """
        return self.to_txt()


# Patch up the docs
Program.Day.__doc__ = Day.__doc__ + "\nSee streprogen.Day for accurate signature."
Program.DynamicExercise.__doc__ = DynamicExercise.__doc__ + "\nSee streprogen.DynamicExercise for accurate signature."
Program.StaticExercise.__doc__ = StaticExercise.__doc__ + "\nSee streprogen.StaticExercise for accurate signature."

if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v", "--capture=sys"])

if __name__ == "__main__":

    from streprogen import Program

    program = Program(
        "My first program!",
        duration=8,
        units="kg",
        reps_per_exercise=15,
        intensity=88,
        intensity_scaler_func=lambda w: 1,
        round_to=2.5,
        percent_inc_per_week=2,
        verbose=True,
    )

    with program.Day("Mandag"):
        program.DynamicExercise("Knebøy", start_weight=70, min_reps=3, max_reps=5)

    # Render the program, then print it
    program.render()
    print(program)

    def rep_scaler_func(week, *args):
        return 1

    def intensity_scaler_func(week, *args):
        return 1

    program = Program(
        # The name of the training program
        name="Beginner 5x5",
        # The duration of the training program in weeks.
        # duration=8,
        # The baseline number of repetitions per dynamic exercise.
        # reps_per_exercise=25,
        intensity=reps_to_intensity(5),
        # Units for the weights, typically 'kg', 'lbs' or '' (empty)
        units="kg",
        # What the weights are rounded to.
        round_to=2.5,
        rep_scaler_func=rep_scaler_func,
        intensity_scaler_func=intensity_scaler_func,
    )

    with program.Day("A"):
        program.DynamicExercise(name="Squat", start_weight=100, min_reps=5, max_reps=5)

    program.render()

    # print(program)
