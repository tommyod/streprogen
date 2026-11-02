# streprogen

**Stre**ngth **pro**gram **gen**erator for Python.

[![PyPI](https://badge.fury.io/py/streprogen.svg)](https://pypi.org/project/streprogen/)
[![Docs](https://readthedocs.org/projects/streprogen/badge/?version=latest)](http://streprogen.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://github.com/tommyod/streprogen/workflows/Python%20CI/badge.svg?branch=master)](https://github.com/tommyod/streprogen/actions)

## Overview

streprogen is a Python package for generating non-trivial strength training programs.
It's based on mathematical optimization, which means that you set the goal and the software will fill in the details.
For instance, instead of manually setting weight every single training session,
you can set a `start_weight` and `final_weight`, and streprogen will work out the rest.
Of course, many other options are available.
To use streprogen efficiently, you should know some strength training theory; 
it's possible to create very advanced programs, but also completely unrealistic ones.

**Features**

- Linear progression, waves, blocks and deloads, defined by functions or lists.
- A rep scheme optimizer with configurable constraints.
- Per-exercise overrides for rep range, volume, intensity, rounding and progression.
- Output as `.txt`, `.html`, `.tex` or dict/JSON.
- Some warnings for unreasonable input.

## Installation

```bash
pip install streprogen
```

Dependencies are installed automatically.

## Examples that can be run in the browser

The example notebooks run in Google Colab without a local install.
Click "Runtime", then "Run all".

- [Essential features](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Essential%20features.ipynb)
- [Intermediate features](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Intermediate%20features.ipynb)
- [Advanced features](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Advanced%20features.ipynb)
- [Custom optimization](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Custom%20optimization.ipynb)
- [Beginner 5x5](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Beginner%205x5.ipynb) · [Beginner 5x5 modified](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Beginner%205x5%20modified.ipynb)
- [3 day full body](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/3%20day%20full%20body.ipynb) · [3 day split](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/3%20day%20split.ipynb) · [Block periodization](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Block%20periodization.ipynb)
- [Meal planning](https://colab.research.google.com/github/tommyod/streprogen/blob/master/docs/examples/Meal%20planning.ipynb)


## Tutorial

Below is a tutorial.
Play with these examples to get a feel for how streprogen works.
It can be helpful to play with a program with only one or two when learning the concepts.
LLMs are quite good at reading this documentation and making programs too,
since they are often able to combine the Python package syntax with their existing
knowledge of strength training.
I would urge you to keep it simple if in doubt though - no need to create overly complex
training programs just because you can!

### Quickstart

Here is a somewhat dense, minimal example:

```python
from streprogen import Program

# An 8-week program, where weights are rounded to the nearest 5 kg.
program = Program("My first program!", duration=8, units="kg", round_to=5)

with program.Day("Day A"):
    program.DynamicExercise("Bench press",   #  name of exercise
                            start_weight=80, #  1 RM starting weight
                            min_reps=3,      #  min reps for this exercise
                            max_reps=8,      #  min reps for this exercise
                            reps=25,         #  total number of reps for exercise
                            intensity=80,    #  average intensity for this exercise
                            )
    program.DynamicExercise("Squats", 
                            # Set two of the three parameters below. The third
                            # will be auto-completed. Setting final_weight=116
                            # is equal to percent_inc_per_week=2 on an 8 week-program.
                            start_weight=100,
                            final_weight=120,
                            percent_inc_per_week=2,
                            )

with program.Day("Day B"):
    program.DynamicExercise("Deadlifts", 
                            start_weight=100,
                            round_to=10, #  can be a number or a function
                            )
    program.StaticExercise("Curls", "3 x 10 @ 18kg")

program.render()  # compute sets, reps and weights
print(program)
```

### Overrides

Many parameters are set on the Program level, but can be overridden on the DynamicExercise level.
Examples include:

- `round_to`: set on Program for general rounding, override on exercises as you like.
- `percent_inc_per_week`: can be set on Program for general level, e.g. `1` for one percent per week, but can also be overwritten on each exercise.
- `reps_per_exercise`: set on Program, override it with `reps` on each exercise.
- `intensity`: set on Program, override it with `intensity` on each exercise.

The logic is simple; first streprogen checks on the lower level (DynamicExercise),
and if there is nothing set or not enough information, it moves up to the higher
level (Program) to get information.

### Static exercises

In the simplest case, a static exercise is a name and a string.
streprogen prints the string every week.
Use static exercises for anything you want to control by hand:
accessories, conditioning, or a full program you already have.

In the slightly more advanced case, a static exercise takes a function of 
week number (1 to `duration`), and within that function you can do whatever
you want as long as you return a string.
This means that linear schemes, two-steps-foward-one-step-back schemes,
linear schemes with deload weeks every fourth week, randomness, etc. can
all be expressed as static exercises.

```python
from streprogen import Program
from streprogen.utils import round_to_nearest

def squat(week):
    """+2.5 kg per week, with a lighter week 4."""
    weight = 100 + 2.5 * (week - 1)
    if week == 4:
        weight = weight * 0.9
    weight = round_to_nearest(weight, nearest=2.5)
    return f"5 x 5 @ {weight}kg"


def bench(week):
    """Alternate volume and heavy weeks."""
    if week % 2 == 1:
        return "5 x 5 @ 80kg"  # odd weeks
    return "5 x 3 @ 87.5kg"    # even weeks


def chin_ups(week):
    """Add one rep per set every week."""
    return f"4 x {5 + week}"


program = Program(name="StaticByWeek", duration=4)
    
with program.Day("A"):
    program.StaticExercise("Squat", "5 x 5 @ 100kg")
    program.StaticExercise("Cardio", "20 min")
    
with program.Day("B"):
    program.StaticExercise("Squat", squat)
    program.StaticExercise("Bench press", bench)
    program.StaticExercise("Chin-ups", chin_ups)

program.render()
print(program)
```

The function is called each time the program is exported.
Keep it deterministic or seed any randomness.

### Volume, intensity and weight

The function `reps_to_intensity_func` maps a number of repetitions to an intensity (percentage of 1RM).
It maps from positive integers to values between 0 and 100.
For instance, the default function maps like this:

```text
reps_to_intensity(1)  => 97.5
reps_to_intensity(5)  => 84.3
reps_to_intensity(10) => 70.05
```

This function can be passed to Program upon initialization, and represents the
relationship between repetitions and intensity.

When streprogen is tasked with finding a good set-rep scheme, 
such as `[5, 4, 3]` or `[5, 5, 5]` or the infamous 3 x 12 `[12, 12, 12]`,
it will evaluate the total number of reptitions for each of these.
Then it will evaluate the average intensity.
Every feasible set-rep scheme is evaluated, and whatever is the closest to 
optimal is chosen.
You can read more about this in the article
[Optimizing sets and reps for strength training](https://tommyodland.com/articles/2020/optimizing-sets-and-reps-for-strength-training/).

### Long-term progress

Suppose we start with an 1RM specified by `start_weight=100` and we set
`percent_inc_per_week=1` in a 12-week program.
Then this is equivalent to setting `final_weight=112`.
However, it does not mean that we increase literally by one percent every single week.
`percent_inc_per_week=1` is only a shorthand to setting `start_weight` or `final_weight`.

Once `start_weight` and `final_weight` is set (maybe using `percent_inc_per_week`),
then the `progression_func` determines the actual 1RM progression week-by-week.
The signature is

```text
progression_func(week, start_weight, final_weight, start_week, end_week)
```
where `week >= 1` is the week number. Typically the returned weight is somewhere
between `start_weight` and `final_weight`. The simplest type of progression function 
is linear, but sinusoidal, two-steps-forward-one-step-back, the more general sawtooth,
and other variants are possible. Randomization can be injected here too.
Several progressions functions are available, or you can make your own.


```






                            start_weight=100,
                            final_weight=120,
                            percent_inc_per_week=2,









        progression_func
            The function used to model overall 1RM progression in the
            training program. The function must have a signature like:
                func(week, start_weight, final_weight, start_week, end_week)

Suppose we 











        name: str = "Untitled",
        duration: int = 8,
        reps_per_exercise: int = 25,
        min_reps: int = 3,
        max_reps: int = 8,
        rep_scaler_func: typing.Callable[[int], float] | None = None,
        intensity: float = 83,
        intensity_scaler_func: typing.Callable[[int], float] | None = None,
        units: str = "kg",
        round_to: float | typing.Callable = 2.5,
        percent_inc_per_week: float = 1.5,
        progression_func: typing.Callable | None = None,
        reps_to_intensity_func: typing.Callable[[int], float] | None = None,
        verbose: bool = False,



        name,
        start_weight=None,
        final_weight=None,
        min_reps=None,
        max_reps=None,
        percent_inc_per_week=None,
        reps=None,
        intensity=None,
        round_to=None,
        shift=0,


## Concepts

| Object | Role |
|---|---|
| `Program` | Container for days. Holds global settings: duration, volume, intensity, progression, rounding, optimizer. |
| `Day` | Container for exercises. Created with `with program.Day("name"):`. |
| `StaticExercise` | A name and a string (or a function `week -> string`). Printed as-is. |
| `DynamicExercise` | A name, a 1RM and a progression. Sets, reps and weights are computed. |
| `program.render()` | Computes all dynamic exercises for all weeks. Call before exporting. |
| `to_txt`, `to_html`, `to_tex`, `to_dict` | Export the rendered program. |

Terms used below:

- **1RM**: one-repetition maximum. `start_weight` is your 1RM at the start of the program, not a working weight.
- **Intensity**: weight as a percentage of the current week's 1RM. The program `intensity` is the rep-weighted average over all sets of one exercise in one week.
- **Reps goal**: total reps for one exercise in one week. Set by `reps_per_exercise` (program) or `reps` (exercise).
- **Scalers**: per-week multipliers applied to the reps goal and the intensity. They create periodization.
- **Weeks** are numbered from 1 to `duration`.

## Quick start

```python
from streprogen import Program

# An 8-week program. Weights are rounded to the nearest 5 kg.
program = Program("My first program!", duration=8, units="kg", round_to=5)

with program.Day("Day A"):
    # start_weight is the 1RM. min_reps/max_reps bound the reps in each set.
    program.DynamicExercise("Bench press", start_weight=80, min_reps=3, max_reps=8)
    program.DynamicExercise("Squats", start_weight=100, min_reps=3, max_reps=8)

with program.Day("Day B"):
    program.DynamicExercise("Deadlifts", start_weight=100, min_reps=2, max_reps=7)
    program.StaticExercise("Curls", "3 x 10 @ 18kg")

program.render()  # compute sets, reps and weights
print(program)    # same as print(program.to_txt())
```

Output (abbreviated; exact numbers may differ between versions):

```text
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
  ...
```

Each set is printed as `reps x weight`.

---

# Beginner

## 1. A program with static exercises

A static exercise is a name and a string. streprogen prints the string every week. Use static exercises for anything you want to control by hand: accessories, conditioning, or a full program you already have.

```python
from streprogen import Program

# duration: number of weeks (int > 1)
program = Program(name="StaticOnly", duration=4)

with program.Day("Monday"):
    program.StaticExercise("Squat", "5 x 5 @ 100kg")
    program.StaticExercise("Bench press", "5 x 5 @ 80kg")
    program.StaticExercise("Barbell row", "5 x 5 @ 70kg")

with program.Day("Thursday"):
    program.StaticExercise("Deadlift", "1 x 5 @ 140kg")
    program.StaticExercise("Overhead press", "5 x 5 @ 50kg")
    program.StaticExercise("Plank", "3 x 60 seconds")

program.render()
print(program)
```

Notes:

- The string can be anything: `"3 x 12"`, `"AMRAP"`, `"20 min easy bike"`.
- The default for `sets_reps` is `"4 x 10"`.
- These characters are removed from names and strings: `& % $ # _ { } ~ ^ \`. Write `"80 pct"`, not `"80%"`.
- Exercise names must be unique within a day.

## 2. Static exercises that change by week

Pass a function instead of a string. It receives the week number (1 to `duration`) and must return a string.

```python
from streprogen import Program
from streprogen.utils import round_to_nearest


def squat(week):
    """+2.5 kg per week, with a lighter week 4."""
    weight = 100 + 2.5 * (week - 1)
    if week == 4:
        weight = weight * 0.9
    weight = round_to_nearest(weight, nearest=2.5)  # 109.25 -> 110
    return f"5 x 5 @ {weight}kg"


def bench(week):
    """Alternate volume and heavy weeks."""
    if week % 2 == 1:
        return "5 x 5 @ 80kg"  # odd weeks
    return "5 x 3 @ 87.5kg"    # even weeks


def chin_ups(week):
    """Add one rep per set every week."""
    return f"4 x {5 + week}"


program = Program(name="StaticByWeek", duration=4)

with program.Day("A"):
    program.StaticExercise("Squat", squat)
    program.StaticExercise("Bench press", bench)
    program.StaticExercise("Chin-ups", chin_ups)
    # Lambdas work too
    program.StaticExercise("Curls", lambda week: f"3 x {8 + week}")

program.render()
print(program)
```

The function is called each time the program is exported. Keep it deterministic (seed any randomness, see [section 22](#22-random-variation-with-markov-chains)).

## 3. Your first dynamic exercise

A dynamic exercise needs a name and enough information to define a 1RM progression. The program computes everything else.

```python
from streprogen import Program

program = Program(
    name="FirstDynamic",
    duration=8,               # weeks
    reps_per_exercise=25,     # baseline total reps per exercise per week
    intensity=83,             # baseline average intensity, % of 1RM
    units="kg",               # appended to weights in output
    round_to=2.5,             # round weights to nearest 2.5
    percent_inc_per_week=1.5, # 1RM increase per week, in % of start_weight
)

with program.Day("A"):
    # 1RM is 140 kg in week 1. It grows 1.5 % per week: 140 -> 156.8 in week 8.
    program.DynamicExercise("Squat", start_weight=140)
    # Static and dynamic exercises can be mixed freely
    program.StaticExercise("Back extensions", "3 x 12")

program.render()
print(program)
```

The values above are the defaults, except `name`. With the defaults:

- The reps goal falls linearly from 1.2 × 25 = 30 in week 1 to 0.8 × 25 = 20 in the last week.
- Intensity rises linearly from 0.95 × 83 ≈ 79 % to 1.05 × 83 ≈ 87 %.
- Sets have 3 to 8 reps.

[Section 16](#16-periodization-with-scalers) explains how to change this.

## 4. Rendering and exporting

`render()` does the computation. Exports read the rendered result.

```python
import json
from streprogen import Program

program = Program(name="OutputDemo", duration=4, units="kg", round_to=2.5)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)
    program.StaticExercise("Back extensions", "3 x 12")

program.render()

# --- Plain text -------------------------------------------------------------
print(program)                      # same as program.to_txt()
print(program.to_txt(verbose=True)) # more detail

with open(f"{program.name}.txt", "w", encoding="utf-8") as file:
    file.write(program.to_txt())

# --- HTML (open in a browser, print or save as PDF) ------------------------
# table_width: number of set columns per row in the table
with open(f"{program.name}.html", "w", encoding="utf-8") as file:
    file.write(program.to_html(table_width=8))

# --- LaTeX (compile with pdflatex) ------------------------------------------
# text_size: LaTeX size name, e.g. "small", "normalsize", "large", "Large"
# clear_pages: start each week on a new page
with open(f"{program.name}.tex", "w", encoding="utf-8") as file:
    file.write(program.to_tex(text_size="large", table_width=8, clear_pages=False))

# --- Python dict / JSON -----------------------------------------------------
data = program.to_dict()
with open(f"{program.name}.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)
```

To build a PDF from the `.tex` file:

```bash
pdflatex OutputDemo.tex
```

Without LaTeX installed, paste the `.tex` content into an online editor such as [latexbase.com](https://latexbase.com/), or print the `.html` file to PDF from a browser.

Rendering again recomputes everything. Change a parameter, call `render()`, export again.

## 5. Setting progression

A dynamic exercise's 1RM goes from `start_weight` in week 1 to `final_weight` in the last week. You specify two of these three:

| Given | Computed |
|---|---|
| `start_weight` + `percent_inc_per_week` | `final_weight = start_weight * (1 + percent_inc_per_week/100 * duration)` |
| `start_weight` + `final_weight` | `percent_inc_per_week` |
| `final_weight` + `percent_inc_per_week` | `start_weight = final_weight / (1 + percent_inc_per_week/100 * duration)` |

The increase is additive, not compounded: 2 % per week for 2 weeks is 4 %, not 4.04 %. If the exercise does not set `percent_inc_per_week`, the program value (default 1.5) is used. Setting all three on one exercise raises `ValueError`.

```python
from streprogen import Program

program = Program(name="Progression", duration=10, percent_inc_per_week=1.5)

with program.Day("A"):
    # start_weight + program percent_inc_per_week (1.5): 100 -> 115
    program.DynamicExercise("Squat", start_weight=100)

    # start_weight + exercise percent_inc_per_week (2): 100 -> 120
    program.DynamicExercise("Bench press", start_weight=100, percent_inc_per_week=2)

    # start_weight + final_weight: 100 -> 110. percent_inc_per_week is ignored.
    program.DynamicExercise("Deadlift", start_weight=100, final_weight=110)

    # final_weight + program percent_inc_per_week: 60 -> 69
    program.DynamicExercise("Overhead press", final_weight=69)

program.render()
print(program)
```

The shape of the curve between start and final is set by `progression_func` ([section 18](#18-custom-1rm-progression)). The default bends slightly: faster gains early, slower near the end.

If you know a working weight rather than a 1RM, convert it with the same function the program uses to map reps to intensity:

```python
from streprogen import reps_to_intensity

# You currently squat 5 reps at 100 kg.
working_weight = 100
reps = 5
estimated_1rm = working_weight / (reps_to_intensity(reps) / 100)
print(round(estimated_1rm, 1))  # 100 / 0.843 = 118.6
```

## 6. Rep ranges and per-exercise overrides

Most program settings can be overridden per exercise.

```python
from streprogen import Program

program = Program(
    name="Overrides",
    duration=8,
    reps_per_exercise=25,
    min_reps=3,
    max_reps=8,
    intensity=83,
    round_to=2.5,
)

with program.Day("A"):
    # Uses all program defaults
    program.DynamicExercise("Squat", start_weight=140)

    # Narrower, heavier rep range
    program.DynamicExercise("Bench press", start_weight=100, min_reps=2, max_reps=6)

    # Less volume: 15 reps instead of 25 (still scaled per week)
    program.DynamicExercise("Deadlift", start_weight=180, reps=15, min_reps=2, max_reps=5,
                            intensity=88)

    # Small increments
    program.DynamicExercise("Overhead press", start_weight=60, round_to=1.25)

program.render()
print(program)
```

Keep `intensity` reachable with the rep range. With the default reps-to-intensity mapping, sets of 3–8 reps cover about 75–91 %. If the target intensity falls outside the range, you get a warning and the optimizer does its best ([section 12](#12-validation-warnings-and-errors)).

## 7. Example: 5x5

Straight 5x5 with constant volume and intensity. Day A and B alternate, three sessions per week.

```python
from streprogen import Program, reps_to_intensity, progression_diffeq
import functools

program = Program(
    name="Beginner5x5",
    duration=12,
    reps_per_exercise=25,           # 5 sets x 5 reps
    min_reps=5,
    max_reps=5,                     # every set has exactly 5 reps
    percent_inc_per_week=1.4,
    intensity=reps_to_intensity(5), # ~84.3 %, the intensity of a 5-rep set
    rep_scaler_func=lambda week: 1, # no weekly variation in volume
    intensity_scaler_func=lambda week: 1, # no weekly variation in intensity
    units="kg",
    round_to=2.5,
    progression_func=functools.partial(progression_diffeq, k=0), # linear 1RM progression
)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=80)
    program.DynamicExercise("Bench press", start_weight=60)
    program.DynamicExercise("Barbell row", start_weight=50)

with program.Day("B"):
    program.DynamicExercise("Squat", start_weight=80)
    program.DynamicExercise("Overhead press", start_weight=40)
    # reps=5 overrides reps_per_exercise: a single set of 5
    program.DynamicExercise("Deadlift", start_weight=80, reps=5)

program.render()
print(program)
```

To loosen this into a 3–7 rep variant, set `min_reps=3, max_reps=7, reps_per_exercise=22` and remove the two scaler arguments to get the default periodization.

---

# Intermediate

## 8. How a dynamic exercise is computed

For each week `w` (1 to `duration`) and each dynamic exercise:

1. **Reps goal**: `round(reps * rep_scalers[w])`, where `reps` is the exercise `reps` or the program `reps_per_exercise`.
2. **Intensity goal**: `intensity * intensity_scalers[w]`, where `intensity` is the exercise value or the program value.
3. **1RM this week**: `progression_func(w, start_weight, final_weight, 1, duration)`.
4. **Rep scheme**: the optimizer picks a list of set sizes from `range(min_reps, max_reps + 1)`, such as `[8, 7, 7, 6]`. It minimizes `(total_reps - reps_goal)² + (avg_intensity - intensity_goal)²`, where `avg_intensity` is the rep-weighted mean of `reps_to_intensity_func(r)` over the sets.
5. **Weights**: each set's weight is `round_to(1RM_this_week * reps_to_intensity_func(r) / 100)`.

Consequences:

- A set's weight depends only on its rep count and the week. Within one week, all 6-rep sets of an exercise use the same weight.
- Sets are listed from most to fewest reps, so weight rises through the session.
- Volume and intensity are targets, not guarantees. The actual values depend on what the rep range allows.

## 9. Reps and intensity

`reps_to_intensity_func` maps a rep count to a percentage of 1RM. Three built-ins:

| Function | Formula |
|---|---|
| `reps_to_intensity` (default) | `97.5 - 3.5 * (r - 1) + 0.05 * (r - 1)**2` |
| `reps_to_intensity_tight` | slope `-3.25`: higher % for the same reps (heavier sets) |
| `reps_to_intensity_relaxed` | slope `-3.75`: lower % for the same reps (lighter sets) |

| Reps | default | tight | relaxed |
|---|---|---|---|
| 1 | 97.5 | 97.5 | 97.5 |
| 2 | 94.05 | 94.3 | 93.8 |
| 3 | 90.7 | 91.2 | 90.2 |
| 4 | 87.45 | 88.2 | 86.7 |
| 5 | 84.3 | 85.3 | 83.3 |
| 6 | 81.25 | 82.5 | 80.0 |
| 7 | 78.3 | 79.8 | 76.8 |
| 8 | 75.45 | 77.2 | 73.7 |
| 9 | 72.7 | 74.7 | 70.7 |
| 10 | 70.05 | 72.3 | 67.8 |

All three accept an int or an iterable of ints:

```python
from streprogen import reps_to_intensity, reps_to_intensity_tight, reps_to_intensity_relaxed

print(reps_to_intensity(5))           # 84.3
print(reps_to_intensity([1, 5, 10]))  # list of three values

for reps in range(1, 11):
    print(reps,
          round(reps_to_intensity(reps), 2),
          round(reps_to_intensity_tight(reps), 2),
          round(reps_to_intensity_relaxed(reps), 2))
```

A custom function must take an int and return a percentage. It should decrease with reps and stay within 0–100 for reps 1–20, or validation warns. Example based on the Epley formula (`1RM = w * (1 + r/30)`):

```python
from streprogen import Program


def epley_intensity(reps):
    """% of 1RM you can lift for `reps` reps, by the Epley formula."""
    return 100 / (1 + reps / 30)


program = Program(
    name="EpleyProgram",
    duration=6,
    intensity=80,
    reps_to_intensity_func=epley_intensity,
)

with program.Day("A"):
    program.DynamicExercise("Bench press", start_weight=100, min_reps=3, max_reps=8)

program.render()
print(program)
```

Use the same function when converting working weights to 1RMs ([section 5](#5-setting-progression)), so the numbers stay consistent.

## 10. Rounding

`round_to` is either a number (round to the nearest multiple) or a callable `weight -> weight`. It can be set on the program and overridden per exercise.

```python
import math
from streprogen import Program
from streprogen.utils import round_to_nearest


def round_down(weight):
    """Always round down to a multiple of 2.5."""
    return 2.5 * math.floor(weight / 2.5)


program = Program(name="Rounding", duration=4, round_to=5)  # default for all exercises

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)                       # nearest 5
    program.DynamicExercise("Bench press", start_weight=100, round_to=2.5)   # nearest 2.5
    program.DynamicExercise("Overhead press", start_weight=60, round_to=round_down)
    program.DynamicExercise("Curls", start_weight=40,
                            round_to=lambda w: round_to_nearest(w, nearest=2))  # dumbbells

program.render()
print(program)
```

Set `units=""` to print plain numbers, for example when weights are percentages or when you add bodyweight yourself.

## 11. Program-level vs. exercise-level parameters

The exercise value is used when it is not `None`; otherwise the program value applies.

| Program parameter | Exercise parameter |
|---|---|
| `reps_per_exercise` | `reps` |
| `min_reps` | `min_reps` |
| `max_reps` | `max_reps` |
| `intensity` | `intensity` |
| `round_to` | `round_to` |
| `percent_inc_per_week` | `percent_inc_per_week` |

These exist only at program level and apply to every dynamic exercise: `duration`, `rep_scaler_func`, `intensity_scaler_func`, `progression_func`, `reps_to_intensity_func`, `units`, `optimizer`.

These exist only at exercise level: `start_weight`, `final_weight`, `shift`.

## 12. Validation, warnings and errors

`render(validate=True)` (the default) runs sanity checks and issues `warnings.warn` messages. The program still renders.

Warnings:

| Check | Warns when |
|---|---|
| Intensity | any week's `intensity * intensity_scaler` is above 90 or below 65 |
| Volume | any week's `reps_per_exercise * rep_scaler` is above 45 or below 15 |
| Rep range | the target intensity cannot be reached with `min_reps`–`max_reps` |
| Growth | an exercise grows more than 4 % per week |
| `reps_to_intensity_func` | it is not decreasing, or leaves 0–100, for reps 1–20 |
| Day names | two days share a name |
| Weight | a week's 1RM is far outside the start/final range (checked even with `validate=False`) |

Errors (raised, rendering stops):

| Error | Cause |
|---|---|
| `ValueError` | Two exercises with the same name in one day. |
| `ValueError` | `min_reps > max_reps`. |
| `ValueError` | `start_weight`, `final_weight` and `percent_inc_per_week` all set on one exercise. |
| `ValueError` from `min()` | The optimizer found no rep scheme that satisfies its constraints ([section 21](#21-the-optimizer)). |
| `TypeError` | `shift` used with list scalers ([section 20](#20-shifting-an-exercise-in-time)). |

Capture warnings to inspect them in code:

```python
import warnings
from streprogen import Program

# Intensity 95 is too high: above 90, and above what 3-rep sets give.
program = Program(name="TooHeavy", duration=4, intensity=95)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    program.render()

for warning in caught:
    print(warning.message)
```

Turn warnings into exceptions with `warnings.simplefilter("error")`, or skip the checks with `program.render(validate=False)`.

## 13. The object API

`with program.Day(...)` is shorthand. You can also build objects first and attach them. This suits programs generated from data.

```python
from streprogen import Program, Day, DynamicExercise, StaticExercise

squat = DynamicExercise("Squat", start_weight=140, min_reps=3, max_reps=8)
bench = DynamicExercise("Bench press", start_weight=100)
plank = StaticExercise("Plank", "3 x 60 seconds")

day_a = Day("Day A", exercises=[squat, bench, plank])

day_b = Day("Day B")
day_b.add_exercises(
    DynamicExercise("Deadlift", start_weight=180, min_reps=2, max_reps=7),
    StaticExercise("Curls", "3 x 12"),
)

program = Program(name="ObjectAPI", duration=6)
program.add_days(day_a, day_b)

program.render()
print(program)
```

Generating days from a dict:

```python
from streprogen import Program

one_rep_maxes = {"Squat": 140, "Bench press": 100, "Deadlift": 180, "Overhead press": 65}

program = Program(name="Generated", duration=8)

# One day per lift, each with the lift and a fixed accessory
for lift, one_rm in one_rep_maxes.items():
    with program.Day(f"{lift} day"):
        program.DynamicExercise(lift, start_weight=one_rm)
        program.StaticExercise("Core", "3 x 15")

program.render()
print(program)
```

Days without a name are named `Day 1`, `Day 2`, ... in the order they were added.

## 14. Reading rendered data

`program.to_dict()` returns the program definition and every computed set. Structure:

```text
{
  "program": {...},                 # same as program.serialize()
  "rendered": [                     # one entry per week, index 0 = week 1
    [                               # one entry per day, in program order
      {
        "name": "Day A",
        "exercises": [
          # Dynamic exercise: its parameters plus computed values
          {
            "name": "Squat", "start_weight": 140, ...,
            "desired_reps": 30,           # reps goal this week
            "desired_intensity": 78.85,   # intensity goal this week
            "reps": [8, 8, 7, 7],         # chosen rep scheme
            "intensities": [75.45, ...],  # % of 1RM per set
            "weights": [105, ...],        # rounded weight per set
            "strings": ["8 x 105kg", ...],
            "1RM_this_week": 140.0
          },
          # Static exercise
          {"name": "Curls", "sets_reps": "3 x 12"}
        ]
      }
    ]
  ]
}
```

The values above are illustrative. Example: compare targets with the result and compute tonnage.

```python
from streprogen import Program

program = Program(name="Analysis", duration=6)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)
    program.DynamicExercise("Bench press", start_weight=100)
    program.StaticExercise("Curls", "3 x 12")

program.render()
data = program.to_dict()

for week_number, week in enumerate(data["rendered"], start=1):
    for day in week:
        for exercise in day["exercises"]:
            if "sets_reps" in exercise:  # static exercise: nothing computed
                continue

            reps = exercise["reps"]
            total_reps = sum(reps)
            actual_intensity = sum(r * i for r, i in zip(reps, exercise["intensities"])) / total_reps
            tonnage = sum(r * w for r, w in zip(reps, exercise["weights"]))

            print(
                f"Week {week_number} {exercise['name']:<12}"
                f" reps {total_reps:>2}/{exercise['desired_reps']:<2}"
                f" intensity {actual_intensity:5.1f}/{exercise['desired_intensity']:5.1f}"
                f" tonnage {tonnage}"
            )
```

`to_dict()` fails if a static exercise uses a function or if `round_to` is a callable, because those cannot be serialized ([section 23](#23-saving-and-loading-programs)).

## 15. Example: 3-day split

```python
from streprogen import Program

program = Program(
    name="ThreeDaySplit",
    duration=8,
    reps_per_exercise=22,
    intensity=80,
    units="kg",
    round_to=5,
)

with program.Day("Day A - Chest/triceps"):
    program.DynamicExercise("Bench press", start_weight=100)
    # Weighted dips: start_weight is bodyweight (80) + added 1RM (25).
    # Printed weights include bodyweight; subtract 80 for the belt.
    program.DynamicExercise("Dips", start_weight=105, min_reps=4)
    program.DynamicExercise("Incline bench", start_weight=80, round_to=2.5)
    program.StaticExercise("French press", "3 x 12")

with program.Day("Day B - Back/biceps"):
    program.DynamicExercise("Deadlift", start_weight=140, reps=15, min_reps=2, max_reps=5,
                            intensity=89)
    program.DynamicExercise("Seated rows", start_weight=90, min_reps=5)
    program.StaticExercise("Chin-ups", "4 x 8")
    program.StaticExercise("Curls", "3 x 10")

with program.Day("Day C - Legs"):
    program.DynamicExercise("Squat", start_weight=120)
    program.DynamicExercise("Stiff-leg deadlift", start_weight=100)
    program.StaticExercise("Calf raises", "4 x 15")

program.render()
print(program)

with open(f"{program.name}.html", "w", encoding="utf-8") as file:
    file.write(program.to_html(table_width=8))
```

---

# Advanced

## 16. Periodization with scalers

Two per-week multipliers control volume and intensity:

- `rep_scaler_func`: multiplies the reps goal.
- `intensity_scaler_func`: multiplies the intensity goal.

Each accepts either:

- a function `week -> float`, called for weeks 1 to `duration`, or
- a list of floats of length `duration` (index 0 = week 1).

Defaults: reps go linearly from 1.2 to 0.8, intensity from 0.95 to 1.05. The computed values are stored on the program:

```python
from streprogen import Program

program = Program(duration=8)
print([round(s, 3) for s in program.rep_scalers])        # 1.2 ... 0.8
print([round(s, 3) for s in program.intensity_scalers])  # 0.95 ... 1.05
```

Function example: three 4-week blocks.

```python
from streprogen import Program


def rep_scaler(week):
    # Weeks 1-4: 1.2, weeks 5-8: 1.0, weeks 9-12: 0.8. Modulo keeps it defined past week 12.
    return [1.2, 1.0, 0.8][((week - 1) // 4) % 3]


def intensity_scaler(week):
    return [0.95, 1.0, 1.05][((week - 1) // 4) % 3]


program = Program(
    name="Blocks",
    duration=12,
    rep_scaler_func=rep_scaler,
    intensity_scaler_func=intensity_scaler,
)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)

program.render()
print(program)
```

List example: a 4-week wave with a deload, repeated three times.

```python
from streprogen import Program

#       week:  1     2     3     4 (deload)
rep_wave =   [1.1,  1.0,  0.9,  0.7]
int_wave =   [0.96, 1.0,  1.04, 0.93]

program = Program(
    name="Waves",
    duration=12,
    reps_per_exercise=24,
    intensity=82,
    rep_scaler_func=rep_wave * 3,       # list of length 12
    intensity_scaler_func=int_wave * 3,
)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)
    program.DynamicExercise("Bench press", start_weight=100)

program.render()
print(program)
```

A list must have exactly `duration` entries. Lists cannot be combined with `shift`.

## 17. Built-in wave functions

These functions model a value going from `start_weight` (at `start_week`) to `final_weight` (at `final_week`). Use them as `progression_func` for the 1RM, or with `start_weight=1, final_weight=1` as scalers.

```text
progression_diffeq(week, start_weight, final_weight, start_week, final_week, k=0)
    k=0: linear. k>0: faster early, flattening toward final_week.

progression_sinh(week, start_weight, final_weight, start_week, final_week, k=0)
    k=0: linear. k>0: steeper at the ends, flatter in the middle.
    Asserts start_week <= week <= final_week.

progression_sinusoidal(week, start_weight, final_weight, start_week, final_week,
                       period=4, scale=0.025, offset=0, k=0, correct_boundaries=False)
    progression_diffeq(...) * (1 + scale * sin(...)).

progression_sawtooth(week, start_weight, final_weight, start_week, final_week,
                     period=4, scale=0.025, offset=0, k=0, correct_boundaries=False)
    progression_diffeq(...) * (1 + scale * saw), saw ramps from -1 to 1 over each period.

    period:              cycle length in weeks
    scale:               amplitude as a fraction; negative scale inverts the wave
    offset:              shift of the wave in weeks
    k:                   bend of the underlying progression_diffeq
    correct_boundaries:  adjust so the curve passes exactly through start and final values
```

All four accept an int week or an iterable of weeks (returning a list).

Wave scalers: intensity ramps up within each 4-week cycle while volume ramps down.

```python
import functools
from streprogen import Program, progression_sawtooth

duration = 12

# start_weight=final_weight=1, so the output is a factor around 1
wave = functools.partial(
    progression_sawtooth,
    start_weight=1,
    final_weight=1,
    start_week=1,
    final_week=duration,
    period=4,
)

intensity_scaler = functools.partial(wave, scale=0.04)  # 0.96, 0.987, 1.013, 1.04, repeat
rep_scaler = functools.partial(wave, scale=-0.15)       # 1.15, 1.05, 0.95, 0.85, repeat

for week in range(1, duration + 1):
    print(week, round(rep_scaler(week), 3), round(intensity_scaler(week), 3))

program = Program(
    name="SawtoothWaves",
    duration=duration,
    rep_scaler_func=rep_scaler,
    intensity_scaler_func=intensity_scaler,
)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)

program.render()
print(program)
```

The program calls `progression_func(week, start_weight, final_weight, start_week, final_week)` with five positional arguments. Bind any extra parameters as keywords:

```python
import functools
from streprogen import Program, progression_diffeq, progression_sinusoidal

# Linear 1RM progression
linear = functools.partial(progression_diffeq, k=0)

# Strongly bent: most gains early
bent = functools.partial(progression_diffeq, k=3)

# 1RM rises with a 4-week sine wave on top
wavy = functools.partial(progression_sinusoidal, period=4, scale=0.02, k=1)

for name, func in [("linear", linear), ("bent", bent), ("wavy", wavy)]:
    values = [round(func(w, 100, 120, 1, 8), 1) for w in range(1, 9)]
    print(f"{name:<7}", values)

program = Program(name="WavyProgression", duration=8, progression_func=wavy)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)

program.render()
print(program)
```

## 18. Custom 1RM progression

`progression_func` can be any function with the signature `(week, start_weight, final_weight, start_week, final_week) -> 1RM`. Lowering the 1RM in a week lowers every weight in that week.

```python
from streprogen import Program, progression_diffeq


def progression_with_deload(week, start_weight, final_weight, start_week, final_week):
    """Default curve, with every 4th week at 90 %."""
    weight = progression_diffeq(week, start_weight, final_weight, start_week, final_week, k=1)
    if week % 4 == 0:
        return weight * 0.9
    return weight


def progression_stepwise(week, start_weight, final_weight, start_week, final_week):
    """1RM increases every second week and holds in between."""
    step_week = start_week + 2 * ((week - start_week) // 2)
    return progression_diffeq(step_week, start_weight, final_weight, start_week, final_week, k=0)


for week in range(1, 9):
    print(week,
          round(progression_with_deload(week, 100, 112, 1, 8), 1),
          round(progression_stepwise(week, 100, 112, 1, 8), 1))

program = Program(name="Deloads", duration=8, progression_func=progression_with_deload)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)
    program.DynamicExercise("Bench press", start_weight=100)

program.render()
print(program)
```

If the curve drops far below `start_weight` or rises far above `final_weight`, a warning is issued. With small total increases, a deep deload can trigger it.

## 19. Example: block periodization

Three 4-week blocks: volume, transition, intensity. The first week of each block is lighter.

```python
from streprogen import Program, progression_diffeq

duration = 12


def rep_scaler(week):
    """Factor applied to reps_per_exercise."""
    factors = [1.18] * 4 + [1.0] * 4 + [0.82] * 4
    return factors[(week - 1) % len(factors)]


def intensity_scaler(week):
    """Factor applied to intensity."""
    factors = [0.94] * 4 + [1.0] * 4 + [1.06] * 4
    return factors[(week - 1) % len(factors)]


def progression(week, start_weight, final_weight, start_week, final_week):
    """Default curve, 5 % lighter in the first week of each block."""
    weight = progression_diffeq(week, start_weight, final_weight, start_week, final_week, k=1)
    if (week - 1) % 4 == 0:
        return weight * 0.95
    return weight


program = Program(
    name="BlockPeriodization",
    duration=duration,
    reps_per_exercise=20,
    min_reps=1,
    max_reps=8,
    percent_inc_per_week=1,
    intensity=84,
    rep_scaler_func=rep_scaler,
    intensity_scaler_func=intensity_scaler,
    progression_func=progression,
    units="kg",
    round_to=2.5,
)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)
    program.DynamicExercise("Bench press", start_weight=100)

with program.Day("B"):
    program.DynamicExercise("Deadlift", start_weight=180, reps=15)
    program.DynamicExercise("Overhead press", start_weight=65)

program.render()
print(program)

with open(f"{program.name}.html", "w", encoding="utf-8") as file:
    file.write(program.to_html(table_width=8))
```

## 20. Shifting an exercise in time

`shift=n` evaluates an exercise's reps scaler, intensity scaler and 1RM progression at week `w + n` instead of `w`. Use it to put the same lift on two days at different points of a wave.

```python
import functools
from streprogen import Program, progression_sawtooth

duration = 8

wave = functools.partial(
    progression_sawtooth, start_weight=1, final_weight=1,
    start_week=1, final_week=duration, period=4,
)

program = Program(
    name="Shifted",
    duration=duration,
    rep_scaler_func=functools.partial(wave, scale=-0.15),
    intensity_scaler_func=functools.partial(wave, scale=0.04),
)

with program.Day("Monday"):
    program.DynamicExercise("Squat", start_weight=140)

with program.Day("Thursday"):
    # Half a cycle ahead: heavy when Monday is light, and vice versa.
    # The 1RM is also evaluated 2 weeks ahead, so start_weight is set a bit lower.
    program.DynamicExercise("Squat", start_weight=136, shift=2)

program.render()
print(program)
```

Rules:

- `shift` must be an int. Negative values are allowed.
- Weeks outside 1–`duration` are computed by calling the scaler functions directly. With list scalers this raises `TypeError`.
- The 1RM progression is extrapolated past `final_weight` for weeks beyond `duration`.
- `shift` is not saved by `serialize()`.

## 21. The optimizer

### How it works

Each week, for each dynamic exercise, the program calls

```text
program.optimizer(sets, intensities, reps_goal, intensity_goal) -> list of reps per set
```

with `sets = tuple(range(min_reps, max_reps + 1))` and `intensities` the matching `reps_to_intensity_func` values.

`RepSchemeOptimizer` asks its generator for every candidate scheme, scores each with `(total_reps - reps_goal)² + (avg_intensity - intensity_goal)²`, and returns the best one, reversed. Results are cached per optimizer instance.

`RepSchemeGenerator` produces candidate schemes as non-decreasing tuples, such as `(6, 7, 7, 8)`. The optimizer reverses them to `[8, 7, 7, 6]`. Hard constraints:

| Parameter | Default | Meaning |
|---|---|---|
| `reps_slack` | 3 | `abs(total_reps - reps_goal) <= reps_slack` |
| `max_diff` | 1 | Consecutive sets differ by at most this many reps. |
| `max_unique` | 3 | At most this many distinct rep counts in a scheme. |
| `min_sets` | 0 | At least this many sets. |
| `max_sets` | 99 | At most this many sets (must be ≤ 99). |

If no candidate satisfies the constraints, rendering fails with `ValueError: min() arg is an empty sequence`. Loosen the constraints or widen the rep range.

### Using the generator and optimizer directly

```python
from streprogen import RepSchemeGenerator, RepSchemeOptimizer, reps_to_intensity

# All schemes from sets of 2, 3 or 4 reps that sum to exactly 6,
# with at most 2 reps between consecutive sets.
generator = RepSchemeGenerator(reps_slack=0, max_diff=2)
print(list(generator.generate(sets=[2, 3, 4], reps_goal=6)))
# [(2, 2, 2), (2, 4), (3, 3)]

# The optimizer requires tuples. `sets` must be sorted ascending.
optimizer = RepSchemeOptimizer(generator=RepSchemeGenerator())
sets = tuple(range(3, 9))                     # 3..8 reps per set
intensities = tuple(reps_to_intensity(sets))  # % of 1RM for each rep count
scheme = optimizer(sets=sets, intensities=intensities, reps_goal=25, intensity_goal=80)
print(scheme)  # a list of reps per set, most reps first
```

Requirements for direct calls: `sets` and `intensities` are tuples of equal length, `sets` is sorted, `reps_goal` is a positive int, and intensities are percentages (greater than 1).

### Configuring the program's optimizer

Assign `program.optimizer` before `render()`. The optimizer is shared by all exercises in the program.

```python
from streprogen import Program, RepSchemeGenerator, RepSchemeOptimizer


def make_program(name):
    program = Program(name=name, duration=4)
    with program.Day("A"):
        program.DynamicExercise("Squat", start_weight=140)
    return program


# 1) Default: small jumps between sets, up to 3 distinct rep counts
default = make_program("DefaultOptimizer")
default.render()
print(default)

# 2) Larger jumps between consecutive sets, more variety
varied = make_program("VariedSets")
varied.optimizer = RepSchemeOptimizer(
    generator=RepSchemeGenerator(max_diff=4, max_unique=4)
)
varied.render()
print(varied)

# 3) Straight sets only: one rep count per exercise per week
straight = make_program("StraightSets")
straight.optimizer = RepSchemeOptimizer(
    generator=RepSchemeGenerator(max_unique=1)
)
straight.render()
print(straight)

# 4) Exactly 5 straight sets: 5 x 4, 5 x 5 or 5 x 6 depending on the week
five_sets = make_program("FiveSets")
five_sets.optimizer = RepSchemeOptimizer(
    generator=RepSchemeGenerator(max_unique=1, min_sets=5, max_sets=5)
)
five_sets.render()
print(five_sets)

# 5) Hit the reps goal exactly
exact = make_program("ExactReps")
exact.optimizer = RepSchemeOptimizer(
    generator=RepSchemeGenerator(reps_slack=0)
)
exact.render()
print(exact)
```

`program.set_optimization_params(reps_slack=..., max_diff=..., max_unique=..., min_sets=..., max_sets=...)` does the same as assigning `program.optimizer`. Pass all five values: an omitted `max_diff` or `max_unique` falls back to 3, not to the generator defaults.

### A custom generator

A generator is any object with a method `generate(sets, reps_goal)` that yields tuples of ints taken from `sets`. The optimizer scores every yielded tuple and returns the best one reversed. You control which schemes are allowed and, through the reversal, the set order.

Top set followed by back-off sets, such as `[3, 6, 6, 6]`:

```python
from streprogen import Program, RepSchemeOptimizer


class TopSetGenerator:
    """One low-rep top set, then back-off sets with more reps.

    The optimizer reverses each scheme, so tuples are yielded with the
    back-off sets first: (6, 6, 6, 3) is printed as 3, 6, 6, 6.
    """

    def __init__(self, reps_slack=3, max_backoff_sets=6):
        self.reps_slack = reps_slack
        self.max_backoff_sets = max_backoff_sets

    def generate(self, sets, reps_goal):
        for top in sets:
            for backoff in sets:
                if backoff <= top:
                    continue
                for num_backoff in range(1, self.max_backoff_sets + 1):
                    scheme = (backoff,) * num_backoff + (top,)
                    if abs(sum(scheme) - reps_goal) <= self.reps_slack:
                        yield scheme


program = Program(name="TopSets", duration=6)
program.optimizer = RepSchemeOptimizer(generator=TopSetGenerator())

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140, min_reps=2, max_reps=8)
    program.DynamicExercise("Bench press", start_weight=100, min_reps=2, max_reps=8)

program.render()
print(program)
```

This generator yields nothing if `min_reps == max_reps`, which makes rendering fail. To change the scoring itself, subclass `RepSchemeOptimizer` and override `_optimize`; see the source.

## 22. Random variation with Markov chains

`sample_markov_loop` and `sample_markov_ladder` produce infinite sequences of state indices `0..n-1`. Use them to rotate exercise variations across weeks without random jumps.

```text
sample_markov_loop(probabilities, structure=None)
    probabilities: relative long-run frequency of each state.
    structure:     relative preference for [stay, move +1, move +2, ...].
                   Default [0.01, 0.99]: almost always move to the next state.
    Wraps around: after the last state comes state 0. The first sample is 0.

sample_markov_ladder(probabilities, structure=None)
    Same, but moves to neighbours in both directions and does not wrap.
```

Sample once, store the result, then read it in a static exercise function. This keeps output identical across exports.

```python
import itertools
import random
from streprogen import Program, sample_markov_loop, sample_markov_ladder

random.seed(42)  # the samplers use the `random` module
duration = 8

# Rotate squat variations
variations = ["Front squat", "Pause squat", "Box squat"]
chain = sample_markov_loop([1, 1, 1])  # equal long-run frequency
squat_schedule = [variations[i] for i in itertools.islice(chain, duration)]

# Move up and down a ladder of rep schemes; the middle one is most frequent
schemes = ["3 x 12", "4 x 10", "5 x 8"]
chain = sample_markov_ladder([1, 2, 1], structure=[0.5, 0.5])
curl_schedule = [schemes[i] for i in itertools.islice(chain, duration)]

print(squat_schedule)
print(curl_schedule)

program = Program(name="Variation", duration=duration)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140)
    program.StaticExercise("Squat variation", lambda week: f"{squat_schedule[week - 1]} 3 x 6")
    program.StaticExercise("Curls", lambda week: curl_schedule[week - 1])

program.render()
print(program)
```

## 23. Saving and loading programs

`serialize()` returns the program definition (not the rendered sets) as a dict. `Program.deserialize(data)` rebuilds it.

```python
import copy
import json
from streprogen import Program

program = Program(name="Saved", duration=6, round_to=2.5)

with program.Day("A"):
    program.DynamicExercise("Squat", start_weight=140, min_reps=3, max_reps=8)
    program.StaticExercise("Curls", "3 x 12")

# Save
data = program.serialize()
with open("saved_program.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

# Load. deserialize() removes "days" from the dict it receives, so pass a copy.
with open("saved_program.json", "r", encoding="utf-8") as file:
    loaded_data = json.load(file)

loaded = Program.deserialize(copy.deepcopy(loaded_data))
loaded.render()
print(loaded)
```

What is saved:

- Program: `name`, `duration`, `min_reps`, `max_reps`, `reps_per_exercise`, `intensity`, `units`, `round_to`, `percent_inc_per_week`, `verbose`, and the scalers as lists of numbers.
- Days and exercises, with exercise parameters that are not `None` or zero.

What is lost or fails:

- `progression_func`, `reps_to_intensity_func`, the optimizer and `shift` are not saved. The loaded program uses defaults.
- A static exercise with a function raises `ValueError` on `serialize()` and `to_dict()`.
- A callable `round_to` cannot be written to JSON.

## 24. Example: 12-week upper/lower

Combines list-based waves with deloads, a custom optimizer, static exercises that change by week, weighted chin-ups and all exports.

```python
from streprogen import Program, RepSchemeGenerator, RepSchemeOptimizer
from streprogen.utils import round_to_nearest

duration = 12
bodyweight = 85

# 4-week wave, repeated. Week 4 is a deload: less volume, lower intensity.
#            week:  1     2     3     4
rep_wave =        [1.1,  1.0,  0.9,  0.7]
intensity_wave =  [0.96, 1.0,  1.04, 0.93]


def is_deload(week):
    return week % 4 == 0


def accessory(base_sets, reps):
    """Static exercise: drop one set in deload weeks."""
    def sets_reps(week):
        sets = base_sets - 1 if is_deload(week) else base_sets
        return f"{sets} x {reps}"
    return sets_reps


def rdl(week):
    """Romanian deadlift: +2.5 kg per week, reset after each deload."""
    weight = 100 + 2.5 * ((week - 1) % 4)
    if is_deload(week):
        weight = 90
    return f"3 x 8 @ {round_to_nearest(weight, 2.5)}kg"


program = Program(
    name="UpperLower12",
    duration=duration,
    reps_per_exercise=24,
    min_reps=3,
    max_reps=8,
    intensity=82,
    rep_scaler_func=rep_wave * 3,
    intensity_scaler_func=intensity_wave * 3,
    percent_inc_per_week=1.25,
    units="kg",
    round_to=2.5,
    verbose=True,  # print render time
)

# Allow jumps of up to 2 reps between sets, at most 2 distinct rep counts
program.optimizer = RepSchemeOptimizer(
    generator=RepSchemeGenerator(reps_slack=3, max_diff=2, max_unique=2)
)

with program.Day("Upper A"):
    program.DynamicExercise("Bench press", start_weight=110)
    # Bodyweight + added 1RM. Printed weights include bodyweight.
    program.DynamicExercise(f"Chin-ups BW{bodyweight}+", start_weight=bodyweight + 40,
                            round_to=5)
    program.StaticExercise("Dumbbell rows", accessory(base_sets=4, reps=10))

with program.Day("Lower A"):
    program.DynamicExercise("Squat", start_weight=150)
    program.StaticExercise("Romanian deadlift", rdl)
    program.StaticExercise("Calf raises", accessory(base_sets=4, reps=15))

with program.Day("Upper B"):
    program.DynamicExercise("Overhead press", start_weight=70)
    program.DynamicExercise("Close-grip bench", start_weight=95)
    program.StaticExercise("Face pulls", accessory(base_sets=3, reps=15))

with program.Day("Lower B"):
    program.DynamicExercise("Deadlift", start_weight=190, reps=15, min_reps=2, max_reps=5,
                            intensity=88)
    program.DynamicExercise("Front squat", start_weight=120, reps=18)
    program.StaticExercise("Hanging leg raises", accessory(base_sets=3, reps=12))

program.render()
print(program)

with open(f"{program.name}.txt", "w", encoding="utf-8") as file:
    file.write(program.to_txt())

with open(f"{program.name}.html", "w", encoding="utf-8") as file:
    file.write(program.to_html(table_width=8))

with open(f"{program.name}.tex", "w", encoding="utf-8") as file:
    file.write(program.to_tex(table_width=8, clear_pages=True))

# to_dict() and serialize() would fail here: static exercises use functions.
```

---

# Meal planning

streprogen also includes a meal plan optimizer. It chooses meal quantities that meet nutrient targets while balancing price and equal meal sizes.

- `Food`: nutrients per 100 g, plus price and package size.
- `Meal`: foods with grams per base portion. `discrete=True` means whole portions only (1, 2, 3, ...). `discrete=False` allows fractional portions.
- `Mealplan`: picks `num_meals` distinct meals per day for `num_days` days.

```python
from streprogen import Food, Meal, Mealplan

# protein, fat, carbs, kcal: per 100 g
oats = Food(name="oats", protein=13.0, fat=7.0, carbs=60.0, kcal=370,
            price_per_product=25.0, grams_per_product=1000)
milk = Food(name="milk", protein=3.5, fat=0.5, carbs=4.5, kcal=37,
            price_per_product=16.4, grams_per_product=1000)
chicken = Food(name="chicken filet", protein=19.0, fat=1.8, carbs=0.3, kcal=94,
               price_per_product=260.0, grams_per_product=2500)
rice = Food(name="jasmin rice", protein=2.7, fat=0.1, carbs=31.1, kcal=136,
            price_per_product=45.8, grams_per_product=1000)
egg = Food(name="egg", protein=13.0, fat=10.6, carbs=0.3, kcal=149,
           price_per_product=32.9, grams_per_product=690)
yogurt = Food(name="yogurt", protein=3.7, fat=3.1, carbs=10.5, kcal=84,
              price_per_product=17.0, grams_per_product=600)
nuts = Food(name="mixed nuts", protein=13, fat=26, carbs=47, kcal=464,
            price_per_product=39.7, grams_per_product=350)

# foods: {Food: grams per base portion}
meals = [
    Meal(name="oats with milk", foods={oats: 60, milk: 200}, discrete=False),
    Meal(name="chicken and rice", foods={chicken: 40, rice: 60}, discrete=False),
    Meal(name="eggs", foods={egg: 70}, discrete=True),          # 1 egg per portion
    Meal(name="yogurt", foods={yogurt: 150}, discrete=True),    # 1 cup per portion
    Meal(name="mixed nuts", foods={nuts: 10}, discrete=False),  # 10 g base portion
]

# (lower, upper) per day. None means no limit. Keys: kcal, protein, carbs, fat.
dietary_constraints = {"kcal": (2400, 2400), "protein": (150, None)}

# (min, max) number of days a meal appears. Matters for multi-day plans.
meal_limits = {"mixed nuts": (None, 2)}

plan = Mealplan(
    meals,
    dietary_constraints,
    meal_limits=meal_limits,
    num_meals=4,             # distinct meals per day
    num_days=3,
    weight_price=0.1,        # higher = cheaper plan
    weight_nutrients=2.0,    # higher = closer to nutrient targets
    weight_meal_sizes=0.75,  # higher = more equal calories per meal
)

plan.render(time_limit_secs=10)  # returns the best solution found within the limit
print(plan.to_txt(verbose=True))
```

Notes:

- Solve time grows mainly with the number of discrete meals.
- Without `meal_limits`, every day of a multi-day plan is the same optimal day.
- Optimize 3–4 days and cycle them.
- If results are poor, adjust the weights or raise `time_limit_secs`.

# Utilities

```python
from streprogen.utils import round_to_nearest
from streprogen.modeling import wilks

print(round_to_nearest(83.7, nearest=2.5))  # 82.5
print(round_to_nearest(83.7, nearest=1))    # 84

# Wilks score: lifted_kg, bodyweight_kg, gender="male" or "female"
print(wilks(500, 100, gender="male"))       # 304.29
```

# API reference

Everything below is importable from `streprogen` unless noted.

### `Program`

```text
Program(
    name="Untitled",             # str
    duration=8,                  # int > 1, weeks
    reps_per_exercise=25,        # int > 0, baseline reps per dynamic exercise per week
    min_reps=3,                  # int > 0, min reps per set
    max_reps=8,                  # int > 0, max reps per set
    rep_scaler_func=None,        # callable(week) -> float, or list of length duration
                                 # default: linear 1.2 -> 0.8
    intensity=83,                # float > 0, baseline average intensity, % of 1RM
    intensity_scaler_func=None,  # callable(week) -> float, or list of length duration
                                 # default: linear 0.95 -> 1.05
    units="kg",                  # str appended to weights
    round_to=2.5,                # float, or callable(weight) -> weight
    percent_inc_per_week=1.5,    # float, additive weekly 1RM increase in %
    progression_func=None,       # callable(week, start_weight, final_weight, start_week, final_week)
                                 # default: progression_diffeq with k=1
    reps_to_intensity_func=None, # callable(reps) -> % of 1RM. default: reps_to_intensity
    verbose=False,               # print render time
)
```

| Method / attribute | Description |
|---|---|
| `Day(name=None)` | Context manager. Exercises created inside belong to this day. |
| `DynamicExercise(...)` | Create a dynamic exercise in the active day. Same arguments as the class. |
| `StaticExercise(name, sets_reps="4 x 10")` | Create a static exercise in the active day. |
| `add_days(*days)` | Attach `Day` objects. |
| `render(validate=True)` | Compute the program. Required before export. |
| `to_txt(verbose=False)` | Text output. `str(program)` is `to_txt()`. |
| `to_html(table_width=5)` | HTML string. |
| `to_tex(text_size="large", table_width=5, clear_pages=False)` | LaTeX string. |
| `to_dict()` | Definition plus rendered sets, as a dict. |
| `serialize()` | Definition as a dict. |
| `Program.deserialize(data)` | Build a program from `serialize()` output. Mutates `data`. |
| `set_optimization_params(reps_slack, max_diff, max_unique, min_sets, max_sets)` | Replace the optimizer. Pass all values. |
| `optimizer` | The `RepSchemeOptimizer` used by `render()`. Assignable. |
| `rep_scalers`, `intensity_scalers` | Lists of per-week factors, computed at construction. |
| `days` | List of `Day` objects. |

### `DynamicExercise`

```text
DynamicExercise(
    name,                      # str, unique within its day
    start_weight=None,         # 1RM in week 1
    final_weight=None,         # 1RM in the last week
    min_reps=None,             # overrides program min_reps
    max_reps=None,             # overrides program max_reps
    percent_inc_per_week=None, # overrides program percent_inc_per_week
    reps=None,                 # overrides program reps_per_exercise
    intensity=None,            # overrides program intensity
    round_to=None,             # overrides program round_to; float or callable
    shift=0,                   # int, evaluate week w as week w + shift
)
```

Set at most two of `start_weight`, `final_weight`, `percent_inc_per_week`.

### `StaticExercise`

```text
StaticExercise(
    name,               # str, unique within its day
    sets_reps="4 x 10", # str, or callable(week) -> str
)
```

### `Day`

```text
Day(name=None, exercises=None)  # exercises: list of DynamicExercise / StaticExercise
day.add_exercises(*exercises)
```

### Optimizer

```text
RepSchemeGenerator(reps_slack=3, max_diff=1, max_unique=3, min_sets=0, max_sets=99)
generator.generate(sets, reps_goal)  # yields tuples, sorted ascending

RepSchemeOptimizer(generator=None)   # None -> RepSchemeGenerator()
optimizer(sets, intensities, reps_goal, intensity_goal)  # -> list, most reps first
```

### Functions

```text
reps_to_intensity(reps, slope=-3.5, constant=97.5, quadratic=True)
reps_to_intensity_tight(reps)     # slope=-3.25
reps_to_intensity_relaxed(reps)   # slope=-3.75

progression_diffeq(week, start_weight, final_weight, start_week, final_week, k=0)
progression_sinh(week, start_weight, final_weight, start_week, final_week, k=0)
progression_sinusoidal(week, start_weight, final_weight, start_week, final_week,
                       period=4, scale=0.025, offset=0, k=0, correct_boundaries=False)
progression_sawtooth(week, start_weight, final_weight, start_week, final_week,
                     period=4, scale=0.025, offset=0, k=0, correct_boundaries=False)

sample_markov_loop(probabilities, structure=None)    # infinite generator of ints
sample_markov_ladder(probabilities, structure=None)  # infinite generator of ints

streprogen.utils.round_to_nearest(number, nearest=1)
streprogen.modeling.wilks(lifted_kg, bodyweight_kg, gender="male")
```

### Meal planning

```text
Food(name, protein, fat, carbs, kcal, price_per_product, grams_per_product)  # nutrients per 100 g
Meal(name, foods, discrete)  # foods: {Food: grams}
Mealplan(meals, dietary_constraints, meal_limits=None, num_meals=4, num_days=1,
         weight_price=0.1, weight_nutrients=2.0, weight_meal_sizes=0.75)
mealplan.render(time_limit_secs=10)
mealplan.to_txt(verbose=True)
```

# Gotchas

- `start_weight` is a 1RM, not a working weight. Convert with `working_weight / (reps_to_intensity(reps) / 100)`.
- Call `render()` before exporting, and again after changing anything.
- Names and static strings lose these characters: `& % $ # _ { } ~ ^ \`.
- Exercise names must be unique within a day. The same name on different days is fine.
- Weeks are 1-based. List scalers are indexed `week - 1` and must have length `duration`.
- `percent_inc_per_week` is additive over `duration` weeks: `final = start * (1 + p/100 * duration)`.
- Intensity outside what the rep range allows gives a warning, not an error.
- Tight optimizer constraints can leave no valid scheme; rendering then fails with `ValueError` from `min()`.
- The optimizer is program-wide. Vary rep schemes per exercise with `min_reps`, `max_reps` and `reps`.
- `shift` needs function scalers, not lists.
- Static exercises with functions, and a callable `round_to`, cannot be serialized or exported with `to_dict()`.
- `serialize()` drops `progression_func`, `reps_to_intensity_func`, the optimizer and `shift`.
- `Program.deserialize(data)` removes `"days"` from `data`. Pass a copy.

# License and contributing

Contributions are welcome. Report issues and request features on [GitHub](https://github.com/tommyod/streprogen/issues).