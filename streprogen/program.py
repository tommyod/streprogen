#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import statistics
import random
import warnings
from os import path

from jinja2 import Environment, FileSystemLoader

from streprogen.day import Day
from streprogen.exercises import DynamicExercise, StaticExercise
from streprogen.modeling import progression_sinusoidal, reps_to_intensity
from streprogen.utils import (
    all_equal,
    chunker,
    escape_string,
    min_between,
    prioritized_not_None,
    round_to_nearest,
)
from streprogen.optimization import optimize_sets


class ProgramError(Exception):
    pass


class Program(object):
    """
    The program class is a container for days and exercises,
    along with the methods and functions used to create training programs.
    """

    REP_SET_SEP = " x "
    TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")
    TEMPLATE_NAMES = {
        extension: "program_template." + extension
        for extension in ["html", "txt", "tex"]
    }

    def __init__(
        self,
        name="Untitled",
        duration=8,
        reps_per_exercise=25,
        rep_scalers=None,
        intensity=75,
        intensity_scalers=None,
        units="kg",
        round_to=2.5,
        progress_func=None,
        reps_to_intensity_func=None,
        verbose=False,
        random_seed=123,
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
            Typically a value in the range [20, ..., 35].

        rep_scalers
            A list of factors of length 'duration', e.g. [1, 0.9, 1.1, ...].
            For each week, the baseline number of repetitions is multiplied
            by the corresponding factor, adding variation to the training
            program. Each factor is typically in the range [0.7, ..., 1.3].
            If None, a list of random factors is generated.

        intensity
            The baseline intensity for each dynamic exercise. The intensity
            of an exercise for a given week is how heavy the average
            repetition is compared to the expected 1RM (max weight one can
            lift) for that given week. Typically a value around 75.

        intensity_scalers
            A list of factors of length 'duration', e.g. [1, 0.95, 1.05, ...].
            For each week, the baseline intensity is multiplied by the
            corresponding factor, adding variation to the training
            program. Each factor is typically in the range [0.95, ..., 1.05].
            If None, a list of random factors is generated.

        units
            The units used for exporting and printing the program, e.g. 'kg'.

        round_to
            Round the dynamic exercise to the nearest multiple of this
            parameter. Typically 2.5, 5 or 10.

        progress_func
            The function used to model overall 1RM progression in the
            training program. If None, the program uses
            :py:meth:`streprogen.progression_sinusoidal`. Custom functions
            may be used, but they must implement arguments like the
            :py:meth:`streprogen.progression_sinusoidal` and
            :py:meth:`streprogen.progression_linear` functions.

        reps_to_intensity_func
            The function used to model the relationship between repetitions
            and intensity. If None, the program uses
            :py:meth:`streprogen.reps_to_intensity`.
            Custom functions may be used,
            and the functions
            :py:meth:`streprogen.reps_to_intensity_tight`
            and
            :py:meth:`streprogen.reps_to_intensity_relaxed`
            are available.

        verbose
            If True, information will be outputted as the program is created.
            
        random_seed
            Random seed used for random generation.

    
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
        self.duration = duration
        self.reps_per_exercise = reps_per_exercise
        self.intensity = intensity
        self.rep_scalers = rep_scalers
        self.intensity_scalers = intensity_scalers
        self.units = units
        self.round = functools.partial(round_to_nearest, nearest=round_to)
        self.verbose = verbose
        user, default = progress_func, progression_sinusoidal
        self.progression_func = prioritized_not_None(user, default)
        self.random_seed = random_seed

        user, default = reps_to_intensity_func, reps_to_intensity
        self.reps_to_intensity_func = prioritized_not_None(user, default)

        self.days = []
        self.active_day = None
        self._rendered = False
        self._set_jinja2_enviroment()

    def Day(self, *args, **kwargs):
        """TODO"""
        day = Day(*args, **kwargs)
        day.program = self
        return day

    def DynamicExercise(self, *args, **kwargs):
        """TODO"""
        ex = DynamicExercise(*args, **kwargs)
        self.active_day.dynamic_exercises.append(ex)
        return ex

    def StaticExercise(self, *args, **kwargs):
        """TODO"""
        ex = StaticExercise(*args, **kwargs)
        self.active_day.static_exercises.append(ex)
        return ex

    def _set_scalers(self):
        """
        Set the variables self._scalers as given by self.scalers,
        if self.scalers is None, then a default value is used.
        """

        random_generator = random.Random(self.random_seed)

        # Set default value for rep_scalers if None
        if self.rep_scalers is None:
            # Draw self-repellent numbers from domain
            domain = [0.95, 1, 1.15]
            self._rep_scalers = random_generator.choices(domain, k=self.duration)

        else:
            if len(self.rep_scalers) != self.duration:
                raise ProgramError(
                    "Length of `rep_scalers` must match program duration."
                )
            self._rep_scalers = self.rep_scalers

        # Set default value for intensity_scalers if None
        if self.intensity_scalers is None:
            # Draw self-repellent numbers from domain
            domain = [0.95, 1, 1.05]
            self._intensity_scalers = random_generator.choices(domain, k=self.duration)
        else:
            if len(self.intensity_scalers) != self.duration:
                raise ProgramError(
                    "Length of `intensity_scalers` must match program duration."
                )
            self._intensity_scalers = self.intensity_scalers

    def _validate(self):
        """
        The purpose of this method is to verify that the user has set sensible
        values for the training program before rendering. The user will still
        be able to render, but error messages will be printed. This method:
            
            * Validates that the average intensity is in the range [65, 85].
            * Validates that the number of repetitions is in the range [15, 45].
            * Validates that 'reps_to_intensity_func' maps to [0, 100].
            * Validates that 'reps_to_intensity_func' is a decreasing function.
            * Validates that the exercises do not grow more than 2.5% per week.
            
        Apart from these sanity checks, the user is on his own.
        """
        # Validate the intensity
        if max([s * self.intensity for s in self._intensity_scalers]) > 85:
            warnings.warn("\nWARNING: Average intensity is > 85.")

        if min([s * self.intensity for s in self._intensity_scalers]) < 65:
            warnings.warn("\nWARNING: Average intensity is < 65.")

        # Validate the repetitions
        if max([s * self.reps_per_exercise for s in self._rep_scalers]) > 45:
            warnings.warn("\nWARNING: Number of repetitions > 45.")

        if min([s * self.reps_per_exercise for s in self._rep_scalers]) < 15:
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
            for dynamic_ex in day.dynamic_exercises:
                start, end = dynamic_ex.start_weight, dynamic_ex.final_weight
                percentage_growth = (end / start) ** (1 / self.duration)
                percentage_growth = dynamic_ex.weekly_growth(self.duration)
                if percentage_growth > 4:
                    msg = '\n"{}" grows with {}% each week.'.format(
                        dynamic_ex.name, percentage_growth
                    )
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

    def _render_dynamic(
        self, dynamic_exercise, min_rep, desired_reps, desired_intensity, validate
    ):
        """
        Render a single dynamic exercise.
        This is done for each exercise every week.
        """

        # Prepare input for the optimization routine
        reps_in = tuple(range(dynamic_exercise.min_reps, dynamic_exercise.max_reps))
        intensities_in = tuple(map(self.reps_to_intensity_func, reps_in))
        intensities_in = tuple([i / 100 for i in intensities_in])

        # Optimize
        # x is a vector with entries saying how many sets of each reps to do
        x, data = optimize_sets(
            reps=reps_in,
            intensities=intensities_in,
            reps_goal=int(desired_reps),
            intensities_goal=desired_intensity / 100,
        )

        # Collect the results
        reps = []
        intensities = []

        for rep, intensity, x_j in reversed(list(zip(reps_in, intensities_in, x))):
            if x_j == 0:
                continue
            for _ in range(int(x_j)):
                reps.append(rep)
                intensities.append(intensity * 100)

        # Perform a sanity check:
        # If repetitions are too high, a low average intensity cannot be attained
        if desired_intensity > self.reps_to_intensity_func(min_rep) and validate:
            msg = """
WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}],
but the desired average intensity for this week is {}. Reaching this intensity
is not attainable since it corresponds to repetitions lower than {}.
SOLUTION: Either (1) allow lower repetitions, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(
                dynamic_exercise.name,
                dynamic_exercise.max_reps,
                min_rep,
                desired_intensity,
                min_rep,
            )
            warnings.warn(msg)

        # Perform a sanity check:
        # If repetitions are too low, a high average intensity cannot be attained
        if (
            desired_intensity < self.reps_to_intensity_func(dynamic_exercise.max_reps)
            and validate
        ):
            msg = """
WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}],
but the desired average intensity for this week is {}. Reaching this intensity
is not attainable since it corresponds to repetitions higher than {}.
SOLUTION: Either (1) allow higher repetitions, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(
                dynamic_exercise.name,
                dynamic_exercise.max_reps,
                min_rep,
                desired_intensity,
                dynamic_exercise.max_reps,
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

        # --------------------------------
        # Prepare for rendering the dynamic exercises
        # --------------------------------

        # Initialize the structure of the _rendered dictionary
        self._initialize_render_dictionary()

        # Set the day names
        for i, day in enumerate(self.days):
            day.name = prioritized_not_None(day.name, "Day {}".format(i + 1))

        # Set the scalers
        self._set_scalers()

        # Validate the program if the user wishes to validate
        if validate:
            self._validate()

        # --------------------------------
        # Render the dynamic exercises
        # --------------------------------

        for (week, day, dyn_ex) in self._yield_week_day_dynamic():

            # The minimum repeition to work up to
            min_rep = dyn_ex.min_reps  # self._rendered[week][day][dyn_ex]["minimum"]

            # The desired repetitions to work up to
            local_r, global_r = dyn_ex.reps, self.reps_per_exercise
            total_reps = prioritized_not_None(local_r, global_r)
            desired_reps = round(total_reps * self._rep_scalers[week - 1])
            self._rendered[week][day][dyn_ex]["desired_reps"] = int(desired_reps)

            # The desired intensity to work up to
            local_i, global_i = dyn_ex.intensity, self.intensity
            intensity_unscaled = prioritized_not_None(local_i, global_i)
            scale_factor = self._intensity_scalers[week - 1]
            desired_intensity = round(intensity_unscaled * scale_factor)
            self._rendered[week][day][dyn_ex]["desired_intensity"] = int(
                desired_intensity
            )

            # A dictionary is returned with keys 'reps' and 'intensities'
            render_args = dyn_ex, min_rep, desired_reps, desired_intensity, validate
            out = self._render_dynamic(*render_args)

            # Calculate the 1RM at this point in time
            start_w, final_w = dyn_ex.start_weight, dyn_ex.final_weight
            args = (week, start_w, final_w, 1, self.duration)
            weight = self.progression_func(*args)

            # Define a function to prettify the weights
            def pretty_weight(weight, i, round_function):
                weight = round_function(weight * i / 100)
                if weight % 1 == 0:
                    return int(weight)
                return weight

            # Use the local rounding function if available,
            # if not use the global rounding function
            round_func = prioritized_not_None(dyn_ex.round, self.round)

            # Create pretty strings
            tuple_generator = zip(out["intensities"], out["reps"])
            pretty_gen = (
                (str(r), str(pretty_weight(weight, i, round_func)) + self.units)
                for (i, r) in tuple_generator
            )
            joined_gen = (self.REP_SET_SEP.join(list(k)) for k in pretty_gen)

            out["strings"] = list(joined_gen)

            # The _rendered dictionary has keys
            # ['minimum', 'desired_reps', 'desired_intensity'].
            # Update with the ['intensities', 'reps', 'strings'] keys
            self._rendered[week][day][dyn_ex].update(out)

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
        if len(exercises) != 0:
            max_ex_name = max(len(ex.name) for ex in exercises)

        # If rendered, find the length of the longest '6 x 75kg'-type string
        max_ex_scheme = 0
        if self._rendered:
            for (week, day, dynamic_ex) in self._yield_week_day_dynamic():
                lengths = [
                    len(s) for s in self._rendered[week][day][dynamic_ex]["strings"]
                ]
                max_ex_scheme = max(max_ex_scheme, max(lengths))

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["txt"])
        return template.render(
            program=self,
            max_ex_name=max_ex_name,
            max_ex_scheme=max_ex_scheme,
            verbose=verbose,
        )

    def to_tex(self, text_size="large", table_width=5, clear_pages=False):
        """
        Write the program information to a .tex file, which can be
        rendered to .pdf running pdflatex. The program can then be
        printed and brought to the gym.

        Parameters
        ----------
        text_size
            The tex text size, e.g. '\small', 'normalsize', 'large', 'Large'
            or 'LARGE'.

        table_width
            The table with of the .tex code.

        Returns
        -------
        string
            Program as tex.
        """

        # If rendered, find the length of the longest '6 x 75kg'-type string
        max_ex_scheme = 0
        if self._rendered:
            for (week, day, dynamic_ex) in self._yield_week_day_dynamic():
                lengths = [
                    len(s) for s in self._rendered[week][day][dynamic_ex]["strings"]
                ]
                max_ex_scheme = max(max_ex_scheme, max(lengths))

        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES["tex"])

        return template.render(
            program=self,
            text_size=text_size,
            table_width=table_width,
            clear_pages=clear_pages,
        )

    def __str__(self):
        """
        String formatting for readable human output.
        """
        return self.to_txt()


# Patch up the docs
Program.Day.__doc__ = Day.__doc__
Program.DynamicExercise.__doc__ = DynamicExercise.__doc__
Program.StaticExercise.__doc__ = StaticExercise.__doc__

if __name__ == "__main__":
    import doctest

    from streprogen import StaticExercise

    def curl_func(week):
        return "{} x 10".format(week)

    doctest.testmod(verbose=True)

    # Create a 4-week program
    program = Program("My first program!", duration=8)

    # Create some dynamic and static exercises
    bench = DynamicExercise("Bench press", 60, 80)
    squats = DynamicExercise("Squats", 80, 95)
    curls = StaticExercise("Curls", curl_func)
    day = Day(exercises=[bench, squats, curls])

    # Add day(s) to program and render it
    program.add_days(day)
    program.render()
    print(program)
