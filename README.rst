Streprogen - the Python strength program generator.
=====================================================================
.. image:: https://badge.fury.io/py/streprogen.svg
   :target: https://pypi.org/project/streprogen/
   :alt: PyPi


.. image:: https://readthedocs.org/projects/streprogen/badge/?version=latest
   :target: http://streprogen.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Install by running ``pip install streprogen``. Remember to read the documentation_.

.. _documentation: http://streprogen.readthedocs.io/en/latest/


Project summary
-----------------

Streprogen (short for **stre**\ ngth **pro**\ gram **gen**\ erator) is a
Python_
package which allows the user to easily create dynamic, flexible
strength training programs. The main features are:

* **Sensible defaults**\ : The software comes with sensible default values for all input parameters,
  giving the novice strength athlete some guidance on parameter selection.
  The software will raise warnings if the input parameters are unreasonable, but will still run.
* **High level of customization**\ : Every important parameter can be changed by the user.
  It is possible to create long-term training programs with several layers of periodization
  if the user wishes to do so.
* **Simple object oriented interface**\ : The software is essentially built
  on four classes ``StaticExercise``, ``DynamicExercise``, ``Day`` and
  ``Program``. In addition to these classes, a set of utility functions is
  provided for advanced usage.
* **Pretty output**\ : The training programs are easily
  saved as ``.txt``, ``.html`` or ``.tex`` files. From there you
  can print it and bring it to the gym.


Installation
-----------------
Here's the layman guide to installation.

(1) Download Anaconda_ distribution of Python_ 3.x from the Anaconda_ Website.
(2) Install ``streprogen`` from PyPI_.

    (a) **Windows**: Open the Anaconda prompt from the start menu and run
        ``pip install streprogen``.
    (b) **Linux**: Open the terminal and run
        ``pip install streprogen``.

(3) Open a Python Editor (such as Spyder, which comes with Anaconda_).
(4) Write ``from streprogen import *`` to import everything from
    ``streprogen``.


.. _Python: http://www.python.org/
.. _Anaconda: https://www.continuum.io/downloads
.. _PyPI: https://pypi.org/project/streprogen/


Sample code
-----------------

.. code-block:: python

    from streprogen import Program, Day, DynamicExercise, StaticExercise

    # Create a 4-week program
    program = Program('My first program!', duration = 4)

    # Create some dynamic and static exercises
    bench = DynamicExercise('Bench press',
                            start_weight = 60, final_weight = 80)
    squats = DynamicExercise('Squats',
                            start_weight = 80, final_weight = 95)
    curls = StaticExercise('Curls', '3 x 12')
    day = Day(exercises = [bench, squats, curls])

    # Add day(s) to program and render it
    program.add_days(day)
    program.render()
    print(program)


.. code-block::

    ----------------------------------------------------------------
    Program: My first program!

    Program parameters
      duration: 4
      reps_per_exercise: 25
      avg_intensity: 75
      reps_scalers: 1.2, 1, 0.8, 1
      intensity_scalers: 0.9, 1, 1, 1
      units: kg
    ----------------------------------------------------------------
    Exercise information
      Day 1
       Bench press   60kg -> 80kg     reps: [3, 8]   weekly inc.: 7.5%
       Squats        80kg -> 95kg     reps: [3, 8]   weekly inc.: 4.4%
       Curls         3 x 12
    ----------------------------------------------------------------
    Program
     Week 1
      Day 1
       Bench press   6 x 45kg    7 x 42.5kg  7 x 42.5kg  7 x 42.5kg
       Squats        6 x 60kg    7 x 57.5kg  8 x 52.5kg  8 x 52.5kg
       Curls         3 x 12

     Week 2
      Day 1
       Bench press   4 x 55kg    5 x 52.5kg  5 x 52.5kg  5 x 52.5kg  6 x 50kg
       Squats        4 x 70kg    4 x 70kg    5 x 65kg    6 x 62.5kg  7 x 57.5kg
       Curls         3 x 12

     Week 3
      Day 1
       Bench press   6 x 55kg    6 x 55kg    6 x 55kg
       Squats        6 x 67.5kg  6 x 67.5kg  6 x 67.5kg
       Curls         3 x 12

     Week 4
      Day 1
       Bench press   5 x 62.5kg  6 x 60kg    6 x 60kg    7 x 57.5kg
       Squats        5 x 75kg    6 x 70kg    6 x 70kg    7 x 67.5kg
       Curls         3 x 12

    ----------------------------------------------------------------