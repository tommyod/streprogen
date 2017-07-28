.. streprogen documentation master file, created by
   sphinx-quickstart on Thu Jul 27 23:49:14 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Streprogen Documentation
======================================
Welcome to the documentation for streprogen, the Python strength program generator.

Project summary
-----------------

Streprogen (short for **Stre**\ ngth **Pro**\ gram **Gen**\ erator) is a Python_
package which allows the user to easily create dynamic, flexible
strength training programs. The main features are:

* **Sensible defaults**\ : The software comes with sensible default values for all input parameters,
  giving the novice strength athlete some guidance on parameter selection.
  The software will raise warnings if the input parameters are unreasonable, but will still run.
* **High level of customization**\ : Every important parameter can be changed by the user.
  It is possible to create long-term training programs with several layers of periodization
  if the user wishes to do so.
* **Simple object oriented interface**\ : The four main classes are ``StaticExercise``, ``DynamicExercise``,
  ``Day`` and ``Program``.
* **Pretty output**\ : The training programs are easily saved as ``.txt``, ``.html`` or ``.tex`` files.



Installation
-----------------
(1) The Anaconda_ distribution of Python_ 3.x from the Anaconda_ Website.
(2) Run ``pip install streprogen`` in the terminal (cmd.exe on Windows)
    to install streprogen from PyPi_.
(3) Open a Python Editor (such as Spyder, which comes with Anaconda_).
(4) Look at the examples: :ref:`example_simple`, :ref:`example_intermediate` and :ref:`example_advanced`.


.. _Python: http://www.python.org/
.. _Anaconda: https://www.continuum.io/downloads
.. _PyPi: https://pypi.org/project/streprogen/


Sample code
-----------------

.. code-block:: python

    from streprogen import Program, Day, DynamicExercise, StaticExercise

    # Create a 4-week program
    program = Program('My first program!', duration = 4)

    # Create some dynamic and static exercises
    bench = DynamicExercise('Bench press', 60, 80)
    squats = DynamicExercise('Squats', 80, 95)
    curls = StaticExercise('Curls', '3 x 12')
    day = Day(exercises = [bench, squats, curls])

    # Add day(s) to program and render it
    program.add_days(day)
    program.render()
    print(program)


.. code-block:: none

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

Contents
-----------------

.. toctree::
   :maxdepth: 2

   classes_overview
   examples
   classes_full
 
Indices and tables
==================
 
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
