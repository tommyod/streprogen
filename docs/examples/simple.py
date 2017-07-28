# Import the needed classes
from streprogen import Program, Day, DynamicExercise, StaticExercise

# Create a new 4 week program
program = Program('My first program!', duration = 4, reps_per_exercise = 25)

# Create exercises for the first day in the week
squats = DynamicExercise('Squats', start_weight = 80, end_weight = 90)
bench = DynamicExercise('Bench press', start_weight = 60, end_weight = 70)
curls = StaticExercise('Curls', '3 x 12')

# Create a day with the exercise objects
day1 = Day(exercises = [bench, squats, curls])

# Create exercises for the second day in the week. Notice that deadlifts have only 20 reps
deadlifts = DynamicExercise('Deadlifts', start_weight = 80, end_weight = 90, reps = 20)
military_press = DynamicExercise('Military press', start_weight = 50, end_weight = 60)
dips = StaticExercise('Dips', '3 x 12')
day2 = Day(exercises = [deadlifts, military_press, dips])

# Add the day(s) to program
program.add_days(day1, day2)

# Render the program, this calculates the (slightly random) dynamic set/rep schemes
program.render()

# Save the program as a .txt file. Programs can also be saved as .html and .tex
with open('simple_example_program.txt', 'w', encoding='utf-8') as file:
    file.write(program.to_text())