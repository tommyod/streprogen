#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools
import statistics
import warnings
from os import path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from streprogen.day import Day
from streprogen.exercises import (DynamicExercise)
from streprogen.modeling import (RepellentGenerator, reps_to_intensity,
                                 progression_sinusoidal)
from streprogen.utils import (round_to_nearest, all_equal, min_between,
                              spread, prioritized_not_None,
                              generate_reps, chunker, escape_string)


class ProgramError(Exception):
    pass


class Program(object):
    """
    The program class is a container for days and exercises,
    along with the methods and functions used to create training programs.
    """

    REP_SET_SEP = ' x '
    TIMES_TO_RENDER = 50
    TEMPLATE_DIR = path.join(path.dirname(__file__), 'templates')
    TEMPLATE_NAMES = {extension: 'program_template.' + extension
                      for extension in ['html', 'txt', 'tex']}

    def __init__(self, name='Untitled', duration=8, reps_per_exercise=25,
                 rep_scalers=None, intensity=75, intensity_scalers=None,
                 units='kg', round_to=2.5, progress_func=None,
                 reps_to_intensity_func=None, min_reps_consistency=None,
                 minimum_percentile=0.2, go_to_min=False, verbose=False):

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

        min_reps_consistency
            This is an advanced feature.  By default, the program will
            examine the dynamic exercises and try to set a minimum
            repetition consistency mode. If all dynamic exercises in the
            program use the same repetition range, it will be set to
            'weekly'. If all dynamic exercises in each day use the same
            repetition range, it will be set to 'daily'.
            If neither, it will be set to 'exercise'.

            The minimum reps consistency mode tells the program how often
            it should draw a new random value for the minimum repetition
            to work up to. If 'min_reps_consistency' is 'weekly' and
            the 'go_to_min' parameter is set to True, you can expect that
            every exercise will work up to the same minimum number of
            repetitions.

            The 'min_reps_consistency' argument will override the program
            default. If, for example, every exercise is set to the
            repetition range 3-8 but you wish to work up to different
            minimum values, set 'min_reps_consistency' to 'daily' or
            'exercise'.

        minimum_percentile
            This is an advanced feature. To protect the athlete against
            often working up to heavy weights, the repetition range is
            "clipped" randomly. A repetition range 1-8 might be clipped
            to, say, 3-8, 2-8 or 1-8. If clipped to 3-8, the repetitions
            are drawn from [3, ..., 8] instead of [1, ..., 8].

            The 'minimum_percentile' determines the percentile of the
            repetition range to clip away. If 0, no clipping occurs.
            If 0.5, half the repetition range could potentially be clipped
            away. How often the range is clipped and a new minimum
            repetition value is computed is determined by the minimum
            repetition consistency mode, which may be controlled by the
            'minimum_percentile' argument.

        go_to_min
            This is an advanced feature.
            Whether or not to force the program to work up to the minimum
            repetition possible for a given dynamic exercise. Consider a
            program where 'minimum_percentile' is 0.2, and a dynamic exercise
            has a repetition range 1-8. The program will drawn repetitions
            in ranges 1-8, 2-8 or 3-8. If 'go_to_min' is True, the program
            will be forced to work up to 1, 2 or 3 repetitions respectively.
            If 'go_to_min' is False, the same range will be used, but the
            program need not go to the minimum number of repeitions.

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
        self.duration = duration
        self.reps_per_exercise = reps_per_exercise
        self.intensity = intensity
        self.rep_scalers = rep_scalers
        self.intensity_scalers = intensity_scalers
        self.units = units
        self.round = functools.partial(round_to_nearest, nearest=round_to)
        self.min_reps_consistency = min_reps_consistency
        self.minimum_percentile = minimum_percentile
        self.go_to_min = go_to_min
        self.verbose = verbose
        user, default = progress_func, progression_sinusoidal
        self.progression_func = prioritized_not_None(user, default)

        user, default = reps_to_intensity_func, reps_to_intensity
        self.reps_to_intensity_func = prioritized_not_None(user, default)

        self.days = []
        self._rendered = False
        self._set_jinja2_enviroment()

    def _set_scalers(self):
        """
        Set the variables self._scalers as given by self.scalers,
        if self.scalers is None, then a default value is used.
        """

        # Set default value for rep_scalers if None
        if self.rep_scalers is None:
            # Draw self-repellent numbers from domain
            domain = [0.8, 1, 1.2]
            gen = RepellentGenerator(domain)
            self._rep_scalers = list(gen.yield_from_domain(self.duration))
        else:
            if len(self.rep_scalers) != self.duration:
                raise ProgramError(
                    'Length of `rep_scalers` must match program duration.')
            self._rep_scalers = self.rep_scalers

        # Set default value for intensity_scalers if None
        if self.intensity_scalers is None:
            # Draw self-repellent numbers from domain
            domain = [0.95, 1, 1.05]
            gen = RepellentGenerator(domain)
            self._intensity_scalers = list(gen.yield_from_domain(self.duration))
        else:
            if len(self.intensity_scalers) != self.duration:
                raise ProgramError(
                    'Length of `intensity_scalers` must match program duration.')
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
            warnings.warn('\nWARNING: Average intensity is > 85.')

        if min([s * self.intensity for s in self._intensity_scalers]) < 65:
            warnings.warn('\nWARNING: Average intensity is < 65.')

        # Validate the repetitions
        if max([s * self.reps_per_exercise for s in self._rep_scalers]) > 45:
            warnings.warn('\nWARNING: Number of repetitions > 45.')

        if min([s * self.reps_per_exercise for s in self._rep_scalers]) < 15:
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
                start, end = dynamic_ex.start_weight, dynamic_ex.final_weight
                percentage_growth = (end / start) ** (1 / self.duration)
                percentage_growth = dynamic_ex.weekly_growth(self.duration)
                if percentage_growth > 4:
                    msg = '\n"{}" grows with {}% each week.'.format(
                        dynamic_ex.name, percentage_growth)
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
        float
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

        # Punish when the repetitions are far from the desired amount
        error2 = abs(sum(reps) - desired_reps)

        # Punish when the spread of repetitions is large
        error3 = spread(reps)

        # Punish deviation from the minimum reptition
        error4 = abs(min(reps) - minimum_rep)

        # Take a linear combination and return
        return sum([2 * error1, 0.5 * error2, 2.5 * error3, 0.5 * error4])

    def _render_dynamic(self, dynamic_exercise, min_rep,
                        desired_reps, desired_intensity, validate):
        """
        Render a single dynamic exercise.
        This is done for each exercise every week.
        """

        # --------------------------------
        # Generate possible repstring and calculate penalties
        # --------------------------------
        repstrings = []
        for k in range(self.TIMES_TO_RENDER):

            # If going to minimum, add the minimum repetition to the reps
            if self.go_to_min:
                reps = generate_reps(min_rep,
                                     dynamic_exercise.max_reps,
                                     desired_reps - min_rep,
                                     [min_rep])
            else:
                reps = generate_reps(min_rep,
                                     dynamic_exercise.max_reps,
                                     desired_reps)

            # Calculate the penalty
            intensities = list(map(self.reps_to_intensity_func, reps))

            pargs = reps, intensities, desired_reps, desired_intensity, min_rep
            penalty_value = self.repstring_penalty(*pargs)

            repstrings.append((penalty_value, reps, intensities))

        # --------------------------------
        # Find the best generated repstring and verify it
        # --------------------------------
        best_repstring = min(repstrings)
        (penalty_value, reps, intensities) = best_repstring

        # Perform a sanity check:
        # If repetitions are too high, a low average intensity cannot be attained
        if desired_intensity > self.reps_to_intensity_func(min_rep) and validate:
            msg = """
WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}],
but the desired average intensity for this week is {}. Reaching this intensity
is not attainable since it corresponds to repetitions lower than {}.
SOLUTION: Either (1) allow lower repetitions, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(dynamic_exercise.name, dynamic_exercise.max_reps, min_rep,
           desired_intensity, min_rep)
            warnings.warn(msg)

        # Perform a sanity check:
        # If repetitions are too low, a high average intensity cannot be attained
        if desired_intensity < self.reps_to_intensity_func(
                dynamic_exercise.max_reps) and validate:
            msg = """
WARNING: The exercise '{}' is restricted to repetitions in the range [{}, {}],
but the desired average intensity for this week is {}. Reaching this intensity
is not attainable since it corresponds to repetitions higher than {}.
SOLUTION: Either (1) allow higher repetitions, (2) change the desired intensity
or (3) ignore this message. The software will do it's best to remedy this.
""".format(dynamic_exercise.name, dynamic_exercise.max_reps, min_rep,
           desired_intensity, dynamic_exercise.max_reps)
            warnings.warn(msg)

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
        ...         for d_ex in day.dynamic_exercises:
        ...             print(program._rendered[week][day][d_ex]['minimum'] > 0)
        True
        True
        """

        min_percent = self.minimum_percentile
        # --------------------------------
        # If the mode is weekly, set minimum reps on a weekly basis
        # --------------------------------
        if self._min_reps_consistency == 'weekly':

            # Set up generator. Only one is needed
            exercise = self.days[0].dynamic_exercises[0]
            margs = exercise.min_reps, exercise.max_reps, min_percent
            low, high = min_between(*margs)
            generator = RepellentGenerator(list(range(low, high + 1)))

            # Use generator to populate the dictionary with minimum values
            for week in range(1, self.duration + 1):
                min_rep_week = generator.generate_one()
                for day in self.days:
                    for d_ex in day.dynamic_exercises:
                        self._rendered[week][day][d_ex]['minimum'] = min_rep_week

        # --------------------------------
        # If the mode is daily, set minimum reps on a daily basis
        # --------------------------------
        if self._min_reps_consistency == 'daily':

            # Set up generators. One is needed for each day
            generators = dict()
            for day in self.days:
                exercise = day.dynamic_exercises[0]
                margs = exercise.min_reps, exercise.max_reps, min_percent
                low, high = min_between(*margs)
                generator = RepellentGenerator(list(range(low, high + 1)))
                generators[day] = generator

            # Use generators to populate the dictionary with minimum values
            for week in range(1, self.duration + 1):
                for day in self.days:
                    min_rep_day = generators[day].generate_one()
                    for d_ex in day.dynamic_exercises:
                        self._rendered[week][day][d_ex]['minimum'] = min_rep_day

        # --------------------------------
        # If the mode is by exercise, set minimum reps on an exercise basis
        # --------------------------------           
        if self._min_reps_consistency == 'exercise':

            # Set up generators. One is needed for each exercise
            generators = dict()
            for day in self.days:
                for d_ex in day.dynamic_exercises:
                    margs = d_ex.min_reps, d_ex.max_reps, min_percent
                    low, high = min_between(*margs)
                    generator = RepellentGenerator(list(range(low, high + 1)))
                    generators[d_ex] = generator

            # Use generators to populate the dictionary with minimum values
            for week in range(1, self.duration + 1):
                for day in self.days:
                    for d_ex in day.dynamic_exercises:
                        min_rep_ex = generators[d_ex].generate_one()
                        self._rendered[week][day][d_ex]['minimum'] = min_rep_ex

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

        # Set the minimum repetitions consistency mode,
        # which is either 'weekly', 'daily' or 'exercise'
        self._autoset_min_reps_consistency()

        # Initialize the structure of the _rendered dictionary
        self._initialize_render_dictionary()

        # Set the day names
        for i, day in enumerate(self.days):
            day.name = prioritized_not_None(day.name, 'Day {}'.format(i + 1))

        # Set the minimum reps per week in the render dictionary
        self._set_min_reps()

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
            min_rep = self._rendered[week][day][dyn_ex]['minimum']

            # The desired repetitions to work up to
            local_r, global_r = dyn_ex.reps, self.reps_per_exercise
            total_reps = prioritized_not_None(local_r, global_r)
            desired_reps = total_reps * self._rep_scalers[week - 1]
            self._rendered[week][day][dyn_ex]['desired_reps'] = int(
                desired_reps)

            # The desired intensity to work up to
            local_i, global_i = dyn_ex.intensity, self.intensity
            intensity_unscaled = prioritized_not_None(local_i, global_i)
            scale_factor = self._intensity_scalers[week - 1]
            desired_intensity = intensity_unscaled * scale_factor
            self._rendered[week][day][dyn_ex]['desired_intensity'] = int(desired_intensity)

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
            tuple_generator = zip(out['intensities'], out['reps'])
            pretty_gen = ((str(r), str(pretty_weight(weight, i, round_func)) +
                           self.units) for (i, r) in tuple_generator)
            joined_gen = (self.REP_SET_SEP.join(list(k)) for k in pretty_gen)

            out['strings'] = list(joined_gen)

            # The _rendered dictionary has keys
            # ['minimum', 'desired_reps', 'desired_intensity'].
            # Update with the ['intensities', 'reps', 'strings'] keys
            self._rendered[week][day][dyn_ex].update(out)

    def _set_jinja2_enviroment(self):
        """
        Set up the jinja2 environment.
        """

        template_loader = FileSystemLoader(searchpath=self.TEMPLATE_DIR)

        env = Environment(loader=template_loader, trim_blocks=True,
                          lstrip_blocks=True)
        env.globals.update(chunker=chunker, enumerate=enumerate, str = str)

        # Add filters to the environment
        round2digits = functools.partial(round_to_nearest, nearest=0.1)
        env.filters['round2digits'] = round2digits
        env.filters['mean'] = statistics.mean

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
        template = env.get_template(self.TEMPLATE_NAMES['html'])
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
                lengths = [len(s) for s in
                           self._rendered[week][day][dynamic_ex]['strings']]
                max_ex_scheme = max(max_ex_scheme, max(lengths))


        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES['txt'])
        return template.render(program=self, max_ex_name=max_ex_name,
                               max_ex_scheme=max_ex_scheme, verbose=verbose)

    def to_tex(self, text_size='large', table_width=5, clear_pages = False):
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
                lengths = [len(s) for s in
                           self._rendered[week][day][dynamic_ex]['strings']]
                max_ex_scheme = max(max_ex_scheme, max(lengths))


        env = self.jinja2_environment
        template = env.get_template(self.TEMPLATE_NAMES['tex'])

        return template.render(program=self, text_size=text_size,
                               table_width=table_width, clear_pages = clear_pages)

    def __str__(self):
        """
        String formatting for readable human output.
        """
        return self.to_txt()

    def _autoset_min_reps_consistency(self):
        """
        Sets the program mode to 'weekly', 'daily' or 'exercise'
        by automatically iterating over all exercises.
        """

        # -------------------------------------------
        # Set automatically by investigating program
        # -------------------------------------------

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

        # -------------------------------------------
        # Respect user wishes if possible
        # -------------------------------------------

        # Set the minimum consistency mode of the program
        if self.min_reps_consistency is not None:

            # Make sure the user defined consistency mode is
            # never more broad than what is allowed by inputs
            if (self._min_reps_consistency == 'exercise' and
                        self.min_reps_consistency != 'exercise'):
                raise ProgramError("Error with 'min_reps_consistency'.")

            if (self._min_reps_consistency == 'daily' and
                        self.min_reps_consistency == 'weekly'):
                raise ProgramError("Error with 'min_reps_consistency'.")

            self._min_reps_consistency = self.min_reps_consistency


if __name__ == "__main__":
    import doctest

    from streprogen import StaticExercise

    def curl_func(week):
        return '{} x 10'.format(week)

    doctest.testmod(verbose=True)

    # Create a 4-week program
    program = Program('My first program!', duration=4)

    # Create some dynamic and static exercises
    bench = DynamicExercise('Bench press', 60, 80)
    squats = DynamicExercise('Squats', 80, 95)
    curls = StaticExercise('Curls', curl_func)
    day = Day(exercises=[bench, squats, curls])

    # Add day(s) to program and render it
    program.add_days(day)
    program.render()
    print(program)
