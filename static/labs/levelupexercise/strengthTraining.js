const EXERCISES = {
  beginnerMoves: {
    wallPushups: {
      name: "Wall Push-ups",
      description:
        "Stand facing wall at arm's length. Place hands at shoulder height, perform push-up motion.",
      type: "bodyweight",
      formCues: ["Keep core tight", "Shoulders down and back"],
      baseSets: 2,
      baseReps: 10,
    },
    chairSquats: {
      name: "Chair-Assisted Squats",
      description:
        "Stand in front of chair, lower yourself until you barely touch it, then stand.",
      type: "bodyweight",
      formCues: ["Knees track over toes", "Keep chest up"],
      baseSets: 3,
      baseReps: 12,
    },
    rowMachine: {
      name: "Seated Row Machine",
      description: "Pull handles to torso while maintaining upright posture.",
      type: "machine",
      formCues: ["Squeeze shoulder blades", "Keep elbows close to body"],
      baseSets: 3,
      baseReps: 10,
      baseWeight: 20,
    },
    modifiedPlank: {
      name: "Modified Plank",
      description:
        "Place forearms on ground with knees down. Keep body straight from head to knees.",
      type: "bodyweight",
      formCues: ["Keep hips level", "Look at floor"],
      baseSets: 2,
      baseDuration: 20,
    },
  },
  intermediateMoves: {
    legPress: {
      name: "Leg Press Machine",
      description: "Press weight away with feet shoulder-width apart.",
      type: "machine",
      formCues: ["Full range of motion", "Don't lock knees"],
      baseSets: 3,
      baseReps: 12,
      baseWeight: 50,
    },
    chestPress: {
      name: "Chest Press Machine",
      description: "Push handles forward until arms are nearly straight.",
      type: "machine",
      formCues: ["Keep back against pad", "Control the movement"],
      baseSets: 3,
      baseReps: 12,
      baseWeight: 30,
    },
    latPulldown: {
      name: "Lat Pulldown Machine",
      description: "Pull bar down to upper chest, controlling the return.",
      type: "machine",
      formCues: ["Lean back slightly", "Lead with elbows"],
      baseSets: 3,
      baseReps: 12,
      baseWeight: 40,
    },
    legExtension: {
      name: "Leg Extension Machine",
      description: "Extend legs to raise weight, then slowly lower.",
      type: "machine",
      formCues: ["Full extension", "Slow negatives"],
      baseSets: 2,
      baseReps: 15,
      baseWeight: 30,
    },
    fullPlank: {
      name: "Plank",
      description: "Hold straight body position on forearms and toes.",
      type: "bodyweight",
      formCues: ["Straight line head to heels", "Breathe steady"],
      baseSets: 3,
      baseDuration: 30,
    },
  },
  advancedMoves: {
    heavyLegPress: {
      name: "Leg Press Machine",
      description: "Heavy leg press with full range of motion.",
      type: "machine",
      formCues: ["Control eccentric phase", "Full depth"],
      baseSets: 4,
      baseReps: 10,
      baseWeight: 100,
    },
    heavyChestPress: {
      name: "Chest Press Machine",
      description: "Heavy chest press focusing on power.",
      type: "machine",
      formCues: ["Explosive press", "Controlled return"],
      baseSets: 4,
      baseReps: 10,
      baseWeight: 80,
    },
    heavyRow: {
      name: "Seated Row Machine",
      description: "Heavy rows with strict form.",
      type: "machine",
      formCues: ["Full contraction", "Controlled tempo"],
      baseSets: 4,
      baseReps: 10,
      baseWeight: 90,
    },
    tricepsPushdown: {
      name: "Triceps Pushdown Machine",
      description: "Isolation work for triceps.",
      type: "machine",
      formCues: ["Elbows at sides", "Full extension"],
      baseSets: 3,
      baseReps: 15,
      baseWeight: 40,
    },
    plankLegLifts: {
      name: "Plank with Leg Lifts",
      description: "Hold plank while alternating leg raises.",
      type: "bodyweight",
      formCues: ["Keep hips level", "Controlled leg raises"],
      baseSets: 3,
      baseDuration: 60,
    },
  },
};

// Helper function to scale exercise parameters based on level
function scaleStrengthExercise(exercise, level, levelOffset = 0) {
  const scaled = { ...exercise };
  function roundWeight(weight) {
    return Math.round(weight / 5) * 5;
  }

  // Helper function to round time to nearest 15 seconds
  function roundTime(seconds) {
    return Math.round(seconds / 15) * 15;
  }
  if (exercise.baseWeight) {
    scaled.weight = roundWeight(
      exercise.baseWeight + (level - levelOffset) * 5
    );
  }

  if (exercise.baseDuration) {
    scaled.duration =
      Math.round((exercise.baseDuration + (level - levelOffset) * 5) / 10) * 10;
  }

  return scaled;
}

function calculateRestPeriod(level, isCircuitRest) {
  if (isCircuitRest) {
    return level <= 10
      ? 180 // 3 minutes between circuits
      : level <= 20
      ? 150 // 2.5 minutes
      : 120; // 2 minutes
  }
  return level <= 10
    ? 60 // 1 minute between exercises
    : level <= 20
    ? 45 // 45 seconds
    : 30; // 30 seconds
}

function roundWeight(weight) {
    return Math.round(weight / 5) * 5;
  }


  function generateStrengthWorkout(level) { 
    // Initialize workout
    const workout = {
        type: "strength",
        level: level,
        description: level <= 10 
            ? "Foundation Strength Training"
            : level <= 20 
            ? "Basic Machine Circuit"
            : "Advanced Strength Program",
        formCues: [
            "Breathe steadily throughout each exercise",
            "Keep core engaged for stability",
            "Control both lifting and lowering phases",
            "Maintain proper posture",
            "Stop if you feel any sharp pain"
        ],
        notes: [
            "Start with a lighter weight to warm up",
            "Focus on form over weight",
            "Rest as needed between exercises",
            "Stay hydrated throughout workout",
            level <= 10 ? "Take time to learn each movement" :
            level <= 20 ? "Maintain form during circuits" :
                         "Challenge yourself while maintaining control"
        ],
        sets: []
    };

    // Get exercises for current level
    let exercises;
    if (level <= 10) {
        exercises = Object.values(EXERCISES.beginnerMoves).map(ex => ({
            ...ex,
            baseReps: ex.baseReps && Math.min(ex.baseReps + Math.floor(level / 2), ex.baseReps + 5),
            baseWeight: ex.baseWeight && ex.baseWeight + level * 2.5,
            baseDuration: ex.baseDuration && ex.baseDuration + level * 5
        }));
    } else if (level <= 20) {
        exercises = Object.values(EXERCISES.intermediateMoves).map(ex => ({
            ...ex,
            baseWeight: ex.baseWeight && ex.baseWeight + (level - 10) * 5,
            baseDuration: ex.baseDuration && ex.baseDuration + (level - 10) * 10
        }));
    } else {
        exercises = Object.values(EXERCISES.advancedMoves).map(ex => ({
            ...ex,
            baseWeight: ex.baseWeight && ex.baseWeight + (level - 20) * 
                (ex.name.includes("Leg Press") ? 7.5 : 
                 ex.name.includes("Triceps") ? 2.5 : 5),
            baseDuration: ex.baseDuration && ex.baseDuration + (level - 20) * 5
        }));
    }

    // Convert exercises to properly formatted intervals
    const exerciseIntervals = exercises.map(ex => {
        const interval = {
            activity: ex.name,
            description: ex.description,
            type: ex.type,
            intensity: "Focus on form",
            formCues: ex.formCues,
            sets: ex.baseSets
        };

        // For timed exercises (like planks)
        if (ex.baseDuration) {
            interval.duration = ex.baseDuration;
        } else {
            // For regular strength exercises
            interval.reps = ex.baseReps;
            if (ex.baseWeight) {
                interval.weight = roundWeight(ex.baseWeight);
            }
        }

        return interval;
    });

    // Add warm-up set
    workout.sets.push({
        repeat: 1,
        intervals: [{
            activity: "Dynamic Warm-up",
            duration: 300,
            type: "warmup",
            intensity: "Light movement",
            description: "Light cardio and mobility work"
        }]
    });

    // Create main workout set
    const mainSet = {
        repeat: level > 10 && level <= 20 ? 3 : 1, // 3 circuits for intermediate
        type: level > 10 && level <= 20 ? 'circuit' : 'regular',
        intervals: []
    };

    // Add exercises with rest periods
    exerciseIntervals.forEach((exercise, index) => {
        mainSet.intervals.push(exercise);

        // Add rest period after each exercise except the last one
        if (index < exerciseIntervals.length - 1) {
            mainSet.intervals.push({
                activity: "Rest",
                type: "rest",
                duration: calculateRestPeriod(level, false),
                intensity: "Active Recovery"
            });
        }
    });

    // Add circuit rest if it's a circuit workout
    if (level > 10 && level <= 20 && mainSet.intervals.length > 0) {
        mainSet.intervals.push({
            activity: "Circuit Rest",
            type: "circuit_rest",
            duration: calculateRestPeriod(level, true),
            intensity: "Recovery between circuits"
        });
    }

    workout.sets.push(mainSet);

    // Add cool-down set
    workout.sets.push({
        repeat: 1,
        intervals: [{
            activity: "Cool-down",
            type: "cooldown",
            duration: 300,
            intensity: "Light stretching"
        }]
    });

    // Calculate total duration
    workout.totalDuration = workout.sets.reduce((total, set) => {
        const setDuration = set.intervals.reduce((setTotal, interval) => {
            return setTotal + (interval.duration || 0);
        }, 0);
        return total + (setDuration * (set.repeat || 1));
    }, 0);

    return workout;
}




function generateStrengthWorkoutHTML(workout) {
  // Get main exercises (excluding warm-up/cooldown/rest)
  const exercises = workout.sets[1].intervals.filter(
    (interval) =>
      interval.activity !== "Rest" &&
      interval.activity !== "Dynamic Warm-up" &&
      interval.activity !== "Cool-down"
  );

  return `
        <div class="workout-header">
            <h4>${workout.description}</h4>
            <p class="workout-intro">Circuit-style workout with varied set counts:</p>
        </div>

        <div class="circuit-overview">
            <h5>Exercise Structure</h5>
            <ul>
                ${exercises
                  .map(
                    (ex) => `
                    <li>
                        ${ex.activity}: ${
                      ex.reps
                        ? `${ex.reps} reps`
                        : ex.duration
                        ? `${ex.duration} seconds`
                        : "Unknown duration/reps"
                    }
                        ${ex.weight ? ` @ ${ex.weight} lbs` : ""}
                    </li>
                `
                  )
                  .join("")}
            </ul>
            <p class="circuit-note">Exercises will rotate in a circuit pattern until all sets are completed</p>
            <p class="circuit-note">Rest ${
              calculateRestPeriod(workout.level, false) / 60
            } minutes between exercises</p>
            <p class="circuit-note">Rest ${
              calculateRestPeriod(workout.level, true) / 60
            } minutes between circuits</p>
        </div>

        ${workout.sets
          .map((set) =>
            set.intervals
              .map(
                (interval) => `
            <div class="exercise-card">
                <h5>${interval.activity}</h5>
                ${
                  interval.description
                    ? `<p class="exercise-description">${interval.description}</p>`
                    : ""
                }
                <div class="exercise-details">
                    ${
                      interval.duration
                        ? `
                        <p>Duration: ${Math.floor(
                          interval.duration / 60
                        )} minutes</p>
                    `
                        : interval.reps
                        ? `
                        <p>Reps: ${interval.reps}</p>
                        ${
                          interval.weight
                            ? `<p>Weight: ${interval.weight} lbs</p>`
                            : ""
                        }
                    `
                        : ""
                    }
                    <p>Intensity: ${interval.intensity}</p>
                    ${
                      interval.formCues
                        ? `
                        <div class="form-cues">
                            <h6>Form Cues:</h6>
                            <ul>
                                ${interval.formCues
                                  .map((cue) => `<li>${cue}</li>`)
                                  .join("")}
                            </ul>
                        </div>
                    `
                        : ""
                    }
                </div>
            </div>
        `
              )
              .join("")
          )
          .join("")}
        
        <button class="start-timer-btn" onclick="startWorkoutTimer()">
            Start Circuit Timer
        </button>`;
}
