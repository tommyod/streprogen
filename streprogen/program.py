#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import operator
import statistics
import warnings
from os import path
from jinja2 import Environment, PackageLoader, select_autoescape

from streprogen.utils import (round_to_nearest, all_equal, min_between,
                              spread, prioritized_not_None,
                              generate_reps, chunker)

from streprogen.modeling import (RepellentGenerator, reps_to_intensity_tight,
                                 reps_to_intensity, progression_sinusoidal)

from streprogen.exercises import (StaticExercise, DynamicExercise)

from streprogen.day import Day


class ProgramError(Exception):
    pass


class Program(object):
    """
    The program class is a container for days and exercises,
    along with the methods and functions used to create training programs.
    """

    REP_SET_SEP = ' x '

    def __init__(self,
                 name='Untitled',
                 duration=8,
                 reps_per_exercise=25,
                 reps_scalers=None,
                 avg_intensity=75,
                 intensity_scalers=None,
                 progression_func=None,
                 reps_to_intensity_func=None,
                 units='kg',
                 round_to=2.5,
                 min_reps_consistency=None,
                 minimum_percentile=0.2,
                 go_to_min=False,
                 times_to_render=100,
                 verbose=False):
        """Initialize a new program.
    
        Parameters
        ----------
        name
            The name of the training program, e.g. 'Tommy_Spring_2017'.
            
        duration
            The duration of the training program in weeks, typically 4-12 weeks.
            
        reps_per_exercise
            Number of baseline repetitions per dynamic exercise, 
            typically 20-35 repetitions. This can be overridden in a 
            specific dynamic exercise by passing the 'reps_per_exercise' 
            argument when constructing the dynamic exercise.
            
        reps_scalers
            A list of scaling factors for the repetitions, of the same length as
            the 'duration' variable, e.g. [1, 1.1, 0.9, 1.2, ...].
            
        avg_intensity
            Baseline average intensity for dynamic exercises, e.g. 75. 
            The average intensity is the percentage of maximum that the 
            average set is done with, weighted by the number of reptitions. 
            Mathematically, 
            avg_intensity = (sum_{sets} intensity * reps) / (sum_{sets} reps).
            This can be overridden in a specific dynamic exercise by passing
            the 'avg_intensity' argument when constructing the dynamic exercise.
            
        intensity_scalers
            A list of scaling factors for the average intensity, of the same 
            length as 'duration' variable, e.g. [1, 1.1, 0.9, 1.2, ...].
            
        progression_func
            A function mapping from a week to the current 1RM, i.e.
            it should have a signature like:
                progression_func(week, start_weight, end_weight, start_week, end_week)
            
        reps_to_intensity_func
            A function mapping from a repetition to an intensity, i.e.
            it should map [1, 20] to [100, 40] and be decreasing.
            
        units
            The weight units, e.g. 'kg' or 'lbs'.
            
        round_to
            Round the weights of closes multiple of this number, e.g. 2.5 or 5.
            
        min_reps_consistency
            Override the 'exercise',  'weekly' or 'daily' modes of 
            minimum repetitions. Overriding is only possible in one direction.
            
        minimum_percentile
            Percentile of the repeition range to draw the 'min_rep' variable
            from. If 'minimum_percentile' is 0.5 for and a dynamic
            exercise has min_reps = 4 and max_reps = 7,
            the minimum repetition always be drawn from [4, 5].
            If 'minimum_percentile' is 1, it will be drawn from [4,5,6,7].
            The 'min_rep' is what the program is minimally allowed to go to
            for that specific week/day/exercise.
            
        go_to_min
            Every week, day or for every exercise, a 'min_rep' value is 
            drawn from the percentile given by 'minimum_percentile'.
            Setting 'go_to_min' to True forces the program to include
            this repetition value in every repstring.
            
        times_to_render
            The number of times to render the dynamic exercises before
            picking the best generated values, default is 50.
            
        verbose
            If True, information is printed when the program is rendered.
            
    
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
        self.name = name
        self.duration = duration
        self.reps_per_exercise = reps_per_exercise
        self.avg_intensity = avg_intensity

        # Set default value for rep_scalers if None
        if reps_scalers is None:
            # Draw self-repellent numbers from domain
            domain = [0.8, 1, 1.2]
            generator = RepellentGenerator(domain)
            self.reps_scalers = list(generator.yield_from_domain(self.duration))
        else:
            if len(reps_scalers) != self.duration:
                raise ProgramError('Length of `reps_scalers` must match program duration.')
            self.reps_scalers = reps_scalers

        # Set default value for intensity_scalers if None
        if intensity_scalers is None:
            # Draw self-repellent numbers from domain
            domain = [0.95, 1, 1.05]
            generator = RepellentGenerator(domain)
            self.intensity_scalers = list(generator.yield_from_domain(self.duration))
        else:
            if len(intensity_scalers) != self.duration:
                raise ProgramError('Length of `intensity_scalers` must match program duration.')
            self.intensity_scalers = intensity_scalers

        self.progression_func = prioritized_not_None(progression_func,
                                                     progression_sinusoidal)

        self.reps_to_intensity_func = prioritized_not_None(reps_to_intensity_func,
                                                           reps_to_intensity)
        self.units = units
        self.round = functools.partial(round_to_nearest, nearest=round_to)
        self.days = []
        self.min_reps_consistency = min_reps_consistency
        self.minimum_percentile = minimum_percentile
        self.go_to_min = go_to_min
        self.times_to_render = times_to_render
        self.verbose = verbose
        self._rendered = False

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
        if max([s * self.avg_intensity for s in self.intensity_scalers]) > 85:
            warnings.warn('\nWARNING: Average intensity is > 85.')

        if min([s * self.avg_intensity for s in self.intensity_scalers]) < 65:
            warnings.warn('\nWARNING: Average intensity is < 65.')

        # Validate the repetitions
        if max([s * self.reps_per_exercise for s in self.reps_scalers]) > 45:
            warnings.warn('\nWARNING: Number of repetitions > 45.')

        if min([s * self.reps_per_exercise for s in self.reps_scalers]) < 15:
            warnings.warn('\nWARNING: Number of repetitions < 15.')

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
                start, end = dynamic_ex.start_weight, dynamic_ex.end_weight
                percentage_growth = (end / start) ** (1 / self.duration)
                percentage_growth = dynamic_ex.weekly_growth(self.duration)
                if percentage_growth > 2.5:
                    msg = '\n"{}" grows with {}% each week.'.format(
                        dynamic_ex.name, percentage_growth)
                    warnings.warn(msg)

    def add_days(self, *days):
        """Add several days to the prorgram.
    
        Parameters
        ----------
        list_of_days
            A list of days, e.g. [day1, day2, ...]
    
    
        Examples
        -------
        >>> program = Program('My training program')
        >>> day1, day2 = Day(), Day()
        >>> program.add_days([day1, day2])
        """
        for day in list(days):
            self.days.append(day)

    @staticmethod
    def repstring_penalty(reps, intensities, desired_reps, desired_intensity,
                          minimum_rep):
        """Penalty function which calculates how "bad" a set of
        reps and intensities is, compared to the desired repetitions,
        the desired intensity level and the minimum repetitions.
        Advanced users may substitute this function for their own version.
    
        Parameters
        ----------
        reps
            A list of repetitions (sorted), e.g. [8, 6, 5, 2].
        intensities
            A list of intensities corresponding to the repetitions,
            e.g. [64.7, 72.3, 76.25, 88.7].
        desired_reps
            Desired number of repetitions in total, e.g. 25.
        desired_intensity
            The desired average intensity, e.g. 75.
        minimum_rep
            The minimum repetition which is allowed, e.g. 2.
    
    
        Returns
        -------
        penalty
            A penalty, a positive real number.
    
    
        Examples
        -------
        >>> desired_reps = 25
        >>> desired_intensity = 75
        >>> minimum_rep = 1
        >>> high = Program().repstring_penalty([8, 8, 8], [60, 60, 60], 
        ...                              desired_reps, desired_intensity, 
        ...                              minimum_rep)
        >>> low = Program().repstring_penalty([8, 6, 5, 4, 2], [64, 72, 75, 80, 88], 
        ...                              desired_reps, desired_intensity, 
        ...                              minimum_rep)
        >>> high > low
        True
        """
        # Punish when the mean intensity is far from the desired one
        desired = desired_intensity
        error1 = abs(statistics.mean(intensities) - desired)

        # Punish when the repeitions are far from the desired amount
        error2 = abs(sum(reps) - desired_reps)

        # Punish when the spread of repetitions is large
        error3 = spread(reps)

        # Punish deviation from the minimum reptition
        error4 = abs(min(reps) - minimum_rep)

        # Take a linear combination and return.
        errors = [2 * error1, 0.5 * error2, 2.5 * error3, 0.5 * error4]

        # print(*[round(err, 4) for err in errors], sep = '\t')
        return sum(errors)

    def _render_dynamic(self, dynamic_exercise, minimum_rep,
                        desired_reps, desired_intensity):
        """
        Render a single dynamic exercise.
        This is done for each exercise every week.
        """

        # --------------------------------
        # Generate possible repstring and calculate penalties
        # --------------------------------
        generated_repstrings = []
        for k in range(self.times_to_render):
            if self.go_to_min:
                reps = generate_reps(minimum_rep,
                                     dynamic_exercise.max_reps,
                                     desired_reps - minimum_rep,
                                     [minimum_rep])
            else:
                reps = generate_reps(minimum_rep,
                                     dynamic_exercise.max_reps,
                                     desired_reps)

            intensities = list(map(self.reps_to_intensity_func, reps))

            penalty = self.repstring_penalty(reps,
                                             intensities,
                                             desired_reps,
                                             desired_intensity,
                                             minimum_rep)

            generated_repstrings.append((penalty, reps, intensities))

        # --------------------------------
        # Find the best generated repstring and verify it
        # --------------------------------
        best_repstring = min(generated_repstrings)
        (penalty, reps, intensities) = best_repstring

        # Perform a sanity check:
        # If repetitions are too high, a low average intensity cannot be attained
        if desired_intensity > self.reps_to_intensity_func(minimum_rep):
            msg = """
WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}],
but the desired average intensity for this week is {}. Reaching this intensity
is not attainable since it corresponds to repetitions lower than {}.
SOLUTION: Either (1) allow lower repetitions, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(dynamic_exercise.name, dynamic_exercise.max_reps, minimum_rep,
           desired_intensity, minimum_rep)
            warnings.warn(msg)

        # Perform a sanity check:
        # If repetitions are too low, a high average intensity cannot be attained
        if desired_intensity < self.reps_to_intensity_func(dynamic_exercise.max_reps):
            msg = """
WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}],
but the desired average intensity for this week is {}. Reaching this intensity
is not attainable since it corresponds to repetitions higher than {}.
SOLUTION: Either (1) allow higher repetitions, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(dynamic_exercise.name, dynamic_exercise.max_reps, minimum_rep,
           desired_intensity, dynamic_exercise.max_reps)
            warnings.warn(msg)

        if self.verbose:
            print('Found optimal repstring for "{}".'.format(dynamic_exercise.name))
            print(' Reps   (desired/actual):', int(desired_reps), int(sum(reps)), sep='\t')
            print(' MI     (desired/actual):', desired_intensity,
                  round(statistics.mean(intensities), 3), sep='\t')
            print(' minrep (limit/actual): ', minimum_rep,
                  min(reps), sep='\t')
            print(' largest jump:          ', spread(reps), sep='\t')

            print(best_repstring[1], best_repstring[0], sep='\t')
            print()

        return {'reps': reps, 'intensities': intensities}

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

    def _set_min_reps(self):
        """Populate the _rendered dictionary with entries corresponding
        to the minimum number of reps to go to for each exercise
        and for the entire duration.
    
    
        Examples
        -------
        >>> program = Program('My training program', duration = 2)
        >>> bench_press = DynamicExercise('Bench', 100, 120)
        >>> day = Day(exercises = [bench_press])
        >>> program.add_days(day)
        >>> program._initialize_render_dictionary()
        >>> program._autoset_min_reps_consistency()
        >>> program._set_min_reps()
        >>> for week in range(1, program.duration + 1):
        ...     for day in program.days:
        ...         for dynamic_ex in day.dynamic_exercises:
        ...             print(program._rendered[week][day][dynamic_ex]['minimum'] > 0)
        True
        True
        """

        # --------------------------------
        # If the mode is weekly, set minimum reps on a weekly basis
        # --------------------------------
        if self._min_reps_consistency == 'weekly':

            # Set up generator. Only one is needed
            exercise = self.days[0].dynamic_exercises[0]
            low, high = min_between(exercise.min_reps,
                                    exercise.max_reps,
                                    self.minimum_percentile)
            generator = RepellentGenerator(list(range(low, high + 1)))

            # Use generator to populate the dictionary with minimum values
            for week in range(1, self.duration + 1):
                minimum_rep_this_week = generator.generate_one()
                for day in self.days:
                    for dynamic_ex in day.dynamic_exercises:
                        self._rendered[week][day][dynamic_ex]['minimum'] = minimum_rep_this_week

        # --------------------------------
        # If the mode is daily, set minimum reps on a daily basis
        # --------------------------------
        if self._min_reps_consistency == 'daily':

            # Set up generators. One is needed for each day
            generators = dict()
            for day in self.days:
                exercise = day.dynamic_exercises[0]
                low, high = min_between(exercise.min_reps,
                                        exercise.max_reps,
                                        self.minimum_percentile)
                generator = RepellentGenerator(list(range(low, high + 1)))
                generators[day] = generator

            # Use generators to populate the dictionary with minimum values
            for week in range(1, self.duration + 1):
                for day in self.days:
                    minimum_rep_this_day = generators[day].generate_one()
                    for dynamic_ex in day.dynamic_exercises:
                        self._rendered[week][day][dynamic_ex]['minimum'] = minimum_rep_this_day

        # --------------------------------
        # If the mode is by exercise, set minimum reps on an exercise basis
        # --------------------------------           
        if self._min_reps_consistency == 'exercise':

            # Set up generators. One is needed for each exercise
            generators = dict()
            for day in self.days:
                for dynamic_ex in day.dynamic_exercises:
                    low, high = min_between(dynamic_ex.min_reps,
                                            dynamic_ex.max_reps,
                                            self.minimum_percentile)
                    generator = RepellentGenerator(list(range(low, high + 1)))
                    generators[dynamic_ex] = generator

            # Use generators to populate the dictionary with minimum values
            for week in range(1, self.duration + 1):
                for day in self.days:
                    for dynamic_ex in day.dynamic_exercises:
                        minimum_rep_this_ex = generators[dynamic_ex].generate_one()
                        self._rendered[week][day][dynamic_ex]['minimum'] = minimum_rep_this_ex

    def _yield_week_day_dynamic(self):
        """A helper function to reduce the number of nested loops.

        Yields
        -------
        (week, day, dynamic_ex)
            A tuple with information.

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
        (week, day_index, day) or (week, day)
            A tuple with information, depending on 'enumeration' parameter.

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
        (dynamic_ex)
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

    def render(self, validate_first=True):
        """Render the training program to perform the calculations.
        The program can be rendered several times to produce new
        information given the same input parameters.
    
        Parameters
        ----------
        validate_first
            Boolean that indicates whether or not to run a validation
            heurestic on the program before rendering. The validation
            will warn the user if inputs seem unreasonable.

        """

        # --------------------------------
        # Prepare for rendering the dynamic exercises
        # --------------------------------

        # Set the minimum consistency mode of the program
        if self.min_reps_consistency is None:
            self._autoset_min_reps_consistency()
        else:
            self._autoset_min_reps_consistency()

            # Make sure the user defined consistency mode is
            # never more broad than what is allowed by inputs
            if (self._min_reps_consistency == 'exercise' and
                        self.min_reps_consistency != 'exercise'):
                raise ProgramError("Error with 'min_reps_consistency'.")

            if (self._min_reps_consistency == 'daily' and
                        self.min_reps_consistency == 'weekly'):
                raise ProgramError("Error with 'min_reps_consistency'.")

            self._min_reps_consistency = self.min_reps_consistency

        # Check the minimum consistency mode of the program in
        # relation to the user input


        # Initialize the structure of the _rendered dictionary
        self._initialize_render_dictionary()

        # Set the day names
        for i, day in enumerate(self.days):
            day.name = prioritized_not_None(day.name, 'Day {}'.format(i + 1))

        # Set the minimum reps per week in the render dictionary
        self._set_min_reps()

        # Validate the program
        if validate_first:
            self._validate()

        # --------------------------------
        # Render the dynamic exercises
        # --------------------------------

        for (week, day, dynamic_ex) in self._yield_week_day_dynamic():

            # The minimum repeition to work up to
            min_rep = self._rendered[week][day][dynamic_ex]['minimum']

            # The reps to work up to
            total_reps = prioritized_not_None(dynamic_ex.reps,
                                              self.reps_per_exercise)
            desired_reps = total_reps * self.reps_scalers[week - 1]
            self._rendered[week][day][dynamic_ex]['desired_reps'] = int(desired_reps)

            # The desired intensity
            intensity_unscaled = prioritized_not_None(dynamic_ex.avg_intensity,
                                                      self.avg_intensity)
            intensity_scale = self.intensity_scalers[week - 1]
            desired_intensity = intensity_unscaled * intensity_scale
            self._rendered[week][day][dynamic_ex]['desired_intensity'] = int(desired_intensity)

            # A dictionary returned with keys 'reps' and 'intensities'
            out = self._render_dynamic(dynamic_ex,
                                       min_rep,
                                       desired_reps,
                                       desired_intensity)

            weight = self.progression_func(week,
                                           dynamic_ex.start_weight,
                                           dynamic_ex.end_weight,
                                           start_week=1,
                                           end_week=self.duration)

            def pretty_weight(weight, i, round_func):
                weight = round_func(weight * i / 100)
                if weight % 1 == 0:
                    return int(weight)
                return weight

            round_func = prioritized_not_None(dynamic_ex.round, self.round)

            out['strings'] = [self.REP_SET_SEP.join(
                [str(r), str(pretty_weight(weight, i, round_func)) + self.units])
                for (i, r) in zip(out['intensities'], out['reps'])]

            # Update the dictionary
            self._rendered[week][day][dynamic_ex].update(out)
            # print(out['string'])
            # print(self._rendered[week][day][dynamic_ex])

    def to_html(self, verbose=False, table_width=5):
        """

        :param verbosity:
        :return:
        """

        env = Environment(
            loader=PackageLoader('streprogen', 'templates'),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        env.globals.update(chunker=chunker, enumerate=enumerate)
        round2digits = functools.partial(round_to_nearest, nearest=0.1)
        env.filters['round2digits'] = round2digits

        template = env.get_template('program_template.html')

        return template.render(program=self,
                               table_width=table_width,
                               verbose=verbose)

    def to_text(self, verbose=False):
        """

        """

        # Get information related to formatting
        max_ex_name = max(len(ex.name) for ex in self._yield_exercises())
        # If rendered, find the length of the longest '6 x 75kg'-type string
        max_ex_scheme = 0
        if self._rendered:
            for (week, day, dynamic_ex) in self._yield_week_day_dynamic():
                lengths = [len(s) for s in
                           self._rendered[week][day][dynamic_ex]['strings']]
                max_ex_scheme = max(max_ex_scheme, max(lengths))

        env = Environment(
            loader=PackageLoader('streprogen', 'templates'),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        round2digits = functools.partial(round_to_nearest, nearest=0.1)
        env.filters['round2digits'] = round2digits
        env.filters['mean'] = statistics.mean

        template = env.get_template('program_template.txt')

        return template.render(program=self, max_ex_name=max_ex_name,
                               max_ex_scheme=max_ex_scheme,
                               verbose=verbose)

    def to_tex(self, verbose=False, text_size='large', table_width=5):
        """

        """

        # Get information related to formatting
        max_ex_name = max(len(ex.name) for ex in self._yield_exercises())
        # If rendered, find the length of the longest '6 x 75kg'-type string
        max_ex_scheme = 0
        if self._rendered:
            for (week, day, dynamic_ex) in self._yield_week_day_dynamic():
                lengths = [len(s) for s in
                           self._rendered[week][day][dynamic_ex]['strings']]
                max_ex_scheme = max(max_ex_scheme, max(lengths))

        env = Environment(
            loader=PackageLoader('streprogen', 'templates'),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        env.globals.update(chunker=chunker, enumerate=enumerate)

        round2digits = functools.partial(round_to_nearest, nearest=0.1)
        env.filters['round2digits'] = round2digits
        env.filters['mean'] = statistics.mean

        template = env.get_template('program_template.tex')

        return template.render(program=self, max_ex_name=max_ex_name,
                               max_ex_scheme=max_ex_scheme,
                               verbose=verbose,
                               text_size=text_size,
                               table_width=table_width)

    def __str__(self):
        """
        String formatting for readable human output.
        """
        return self.to_text()

    def _autoset_min_reps_consistency(self):
        """
        Sets the program mode to 'weekly', 'daily' or 'exercise'
        by automatically iterating over all exercises.
        """

        # Check whether the mode is WEEKLY
        min_reps, max_reps = [], []
        for day in self.days:
            for dynamic_ex in day.dynamic_exercises:
                min_reps.append(dynamic_ex.min_reps)
                max_reps.append(dynamic_ex.max_reps)
        if all_equal(min_reps) and all_equal(max_reps):
            self._min_reps_consistency = 'weekly'
            return None

        # Check if mode is DAILY
        for day in self.days:
            min_reps, max_reps = [], []
            for dynamic_ex in day.dynamic_exercises:
                min_reps.append(dynamic_ex.min_reps)
                max_reps.append(dynamic_ex.max_reps)
            if not all_equal(min_reps) or not all_equal(max_reps):
                self._min_reps_consistency = 'exercise'
                return None
        self._min_reps_consistency = 'daily'


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
