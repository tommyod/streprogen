from streprogen import Program, Day, DynamicExercise, StaticExercise

# Create a 4-week program with 25 repetitions per exercise
program = Program('My first program!', duration = 4, reps_per_exercise = 25)

# Create some dynamic and static exercises, add to the day
bench = DynamicExercise('Bench press', start_weight = 60, end_weight = 80)
squats = DynamicExercise('Squats', start_weight = 80, end_weight = 95)
curls = StaticExercise('Curls', '3 x 12')
day = Day(exercises = [bench, squats, curls])

# Add day(s) to program and render it
program.add_days(day)
program.render()
print(program)