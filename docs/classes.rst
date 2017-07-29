API: Classes
====================================

Brief introduction to classes
----------------------------------------------------

There are four classes available:

* ``StaticExercise``: For exercises schemes such as "3 x 12", "5 x 5 @ 80kg" or "stretch for 5 mins".
  In other words, this class is merely a container for an exercise name and a string.

* ``DynamicExercise``: For exercises where you wish to render a dynamic set/rep scheme.
  The ``DynamicExercise`` class is part of what makes streprogen dynamic.

* ``Day``: A ``Day`` class is a container for exercises associated with the same day.

* ``Program``: This is where the magic happens. The ``Program`` class is a container
  for ``Day``s (and therefore also instances of ``StaticExercise`` and ``DynamicExercise``).
  The algorithms used to render the program is also contained in the ``Program``
  class. The most important method is the ``Program.render()`` method, which
  renders the dynamic exercises.

.. automodule:: streprogen

The DynamicExercise class
--------------------------
.. autoclass:: DynamicExercise
   :members:

   .. automethod:: __init__


The StaticExercise class
--------------------------
.. autoclass:: StaticExercise
   :members:

   .. automethod:: __init__


The Day class
--------------------------
.. autoclass:: Day
   :members:

   .. automethod:: __init__


The Program class
--------------------------
.. autoclass:: Program
   :members:

   .. automethod:: __init__