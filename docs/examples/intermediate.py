from streprogen import Program, Day, DynamicExercise, StaticExercise

# Create a 6 week program. Set 'reps_per_exercise' higher than the default
# value of 25 and set the 'avg_intensity' lower than the default value of 75
program = Program(name='Example program with more features!', duration = 6,
          reps_per_exercise = 30, avg_intensity = 70, units = 'lbs', round_to = 5)

# The rep range is [min_reps, max_reps], and can be changed when creating an exercise
squats = DynamicExercise('Squats',
                         start_weight = 80,
                         end_weight = 90,
                         min_reps = 5,
                         max_reps = 8)

# Days can be given custom names as below
dayA = Day('Day A')
dayA.add_exercises(squats)

# Create some deadlifts, up the intensity and lower the number of reps
deadlifts = DynamicExercise('Deadlifts',
                            start_weight = 80,
                            end_weight = 90,
                            min_reps = 1,
                            max_reps = 8,
                            reps = 20,
                            avg_intensity = 75,
                            round_to = 5)
dips = StaticExercise('Dips', '3 x 12')
dayB = Day('Day B')
dayB.add_exercises(deadlifts, dips)

# Add day(s) to program and render it
program.add_days(dayA, dayB)
program.render()

# Save the program as a .txt file.
with open('intermediate_program.html', 'w', encoding='utf-8') as file:
    file.write(program.to_html())

# Save the program as a .txt file.
with open('intermediate_program.tex', 'w', encoding='utf-8') as file:
    file.write(program.to_tex())