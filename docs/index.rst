.. streprogen documentation master file, created by
   sphinx-quickstart on Thu Jul 27 23:49:14 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Streprogen documentation
======================================
Streprogen is a Python strength program generator.
It helps strength athletes and their trainers efficiently build
dynamic strength training programs with great flexibility and power.

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
    :linenos:

    from streprogen import Program
    
    # Create an 8-week program, rounding every exercise to nearest unit og 5kg
    program = Program("My first program!", duration=8, units="kg", round_to=5)
    
    with program.Day("Day A"):
        program.DynamicExercise("Bench press", start_weight=80, min_reps=3, max_reps=8)
        program.DynamicExercise("Squats", start_weight=100, min_reps=3, max_reps=8)
        
    with program.Day("Day B"):
        program.DynamicExercise("Deadlifts", start_weight=100, min_reps=2, max_reps=7)
        program.StaticExercise("Curls", "3 x 10 @ 18kg")

    # Render the program, then print it
    program.render()
    print(program)


.. code-block:: none

    ----------------------------------------------------------------
    Program: My first program!
    
    Program parameters
      duration: 8
      reps_per_exercise: 25
      intensity: 83
      units: kg
    ----------------------------------------------------------------
    Exercise information
      Day A
       Bench press    80kg -> 89.6kg 
        reps: [3, 8]   weekly inc.: 1.5%
       Squats        100kg -> 112kg  
        reps: [3, 8]   weekly inc.: 1.5%
      Day B
       Deadlifts     100kg -> 112kg  
        reps: [2, 7]   weekly inc.: 1.5%
       Curls         3 x 10 @ 18kg
    ----------------------------------------------------------------
    Program
     Week 1
      Day A
       Bench press   8 x 60kg   7 x 65kg   7 x 65kg   7 x 65kg   
       Squats        8 x 75kg   7 x 80kg   7 x 80kg   7 x 80kg   
    
      Day B
       Deadlifts     7 x 80kg   7 x 80kg   6 x 80kg   6 x 80kg   5 x 85kg   
       Curls         3 x 10 @ 18kg
    
     Week 2
      Day A
       Bench press   7 x 65kg   7 x 65kg   6 x 65kg   5 x 70kg   5 x 70kg   
       Squats        7 x 80kg   7 x 80kg   6 x 85kg   5 x 85kg   5 x 85kg   
    
      Day B
       Deadlifts     7 x 80kg   7 x 80kg   6 x 85kg   5 x 85kg   5 x 85kg   
       Curls         3 x 10 @ 18kg
    
     Week 3
      ...
       ...  

Contents
-----------------

.. toctree::
   :maxdepth: 2

   examples/Essential features.ipynb
   examples/Intermediate features.ipynb
   examples/Advanced features.ipynb
   examples/Beginner 5x5.ipynb
   examples/Beginner 5x5 modified.ipynb
   examples/3 day split.ipynb
   examples/3 day full body.ipynb
   examples/Meal planning.ipynb
   classes
   functions
 
Indices and tables
==================
 
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
