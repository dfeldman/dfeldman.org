class IntervalTimer {
    constructor(workoutDisplay) {
        this.workoutDisplay = workoutDisplay;

        this.intervals = [];
        this.currentInterval = 0;
        this.currentSet = 0;
        this.timeRemaining = 0;
        this.isRunning = false;
        this.timer = null;
        this.totalSets = 0;

        // DOM elements
        this.timeDisplay = document.querySelector('.time-display');
        this.currentActivityDisplay = document.querySelector('.current-activity');
        this.nextUpDisplay = document.querySelector('.next-up');
        this.progressBar = document.querySelector('.progress-fill');
        this.workoutProgress = document.querySelector('.workout-progress');
        this.playPauseButton = document.querySelector('.play-pause');
        this.skipButton = document.querySelector('.skip');
        this.resetButton = document.querySelector('.reset');
        this.exitButton = document.querySelector('.exit');

        // Bind event listeners
        this.playPauseButton.addEventListener('click', () => this.togglePlayPause());
        this.skipButton.addEventListener('click', () => this.skipInterval());
        this.resetButton.addEventListener('click', () => this.reset());
        this.exitButton.addEventListener('click', () => this.exit());
    }

    setWorkout(workout) {
        // Workout should be an array of interval objects
        this.intervals = workout;
        this.totalSets = workout.length;
        this.reset();
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    // updateDisplay() {
    //     if (this.currentSet >= this.totalSets) {
    //         this.complete();
    //         return;
    //     }

    //     const currentInterval = this.intervals[this.currentSet];

    //     // Handle display differently for timed vs untimed intervals
    //     if (currentInterval.duration) {
    //         // Timed interval
    //         this.timeDisplay.textContent = this.formatTime(this.timeRemaining);
    //         const totalIntervalTime = currentInterval.duration;
    //         const progress = ((totalIntervalTime - this.timeRemaining) / totalIntervalTime) * 100;
    //         this.progressBar.style.width = `${progress}%`;
    //         this.playPauseButton.style.display = 'block';
    //     } else {
    //         // Untimed interval (e.g., strength exercise or static stretch)
    //         this.timeDisplay.textContent = ""; // Clear the time display
    //         this.progressBar.style.width = '100%';
    //         this.playPauseButton.style.display = 'none';
    //     }

    //     // Show current activity details
    //     let activityText = currentInterval.activity;
    //     if (currentInterval.sets && currentInterval.reps) {
    //         activityText += ` (${currentInterval.sets} × ${currentInterval.reps})`;
    //     }
    //     if (currentInterval.weight) {
    //         activityText += ` @ ${currentInterval.weight}lbs`;
    //     }
    //     if (currentInterval.holdTime) {
    //         activityText += ` - Hold ${currentInterval.holdTime}`;
    //     }
    //     this.currentActivityDisplay.textContent = activityText;

    //     // Show next activity preview
    //     const nextSet = this.currentSet + 1;
    //     if (nextSet < this.totalSets) {
    //         const nextInterval = this.intervals[nextSet];
    //         let nextText = `Next: ${nextInterval.activity}`;
    //         if (nextInterval.sets && nextInterval.reps) {
    //             nextText += ` (${nextInterval.sets} × ${nextInterval.reps})`;
    //         }
    //         this.nextUpDisplay.textContent = nextText;
    //     } else {
    //         this.nextUpDisplay.textContent = 'Final exercise!';
    //     }

    //     this.workoutProgress.textContent = `Exercise ${this.currentSet + 1} of ${this.totalSets}`;
    // }

    updateDisplay() {
        if (this.currentSet >= this.totalSets) {
            this.complete();
            return;
        }

        const currentInterval = this.intervals[this.currentSet];
        
        // Update the timer display
        if (currentInterval.duration) {
            this.timeDisplay.textContent = this.formatTime(this.timeRemaining);
            const totalIntervalTime = currentInterval.duration;
            const progress = ((totalIntervalTime - this.timeRemaining) / totalIntervalTime) * 100;
            this.progressBar.style.width = `${progress}%`;
        }

        // Use the new workout display render method
        const intervalDisplay = document.querySelector('.interval-info');
        intervalDisplay.innerHTML = this.workoutDisplay.renderTimerInterval(currentInterval);

        // Update progress text
        this.workoutProgress.textContent = `Exercise ${this.currentSet + 1} of ${this.totalSets}`;
    }

    start() {
        const currentInterval = this.intervals[this.currentSet];
        if (currentInterval.duration && !this.isRunning) {
            this.isRunning = true;
            this.playPauseButton.textContent = 'Pause';
            this.timer = setInterval(() => this.tick(), 1000);
        }
    }

    pause() {
        if (this.isRunning) {
            this.isRunning = false;
            this.playPauseButton.textContent = 'Resume';
            clearInterval(this.timer);
        }
    }

    togglePlayPause() {
        if (this.isRunning) {
            this.pause();
        } else {
            this.start();
        }
    }

    skipInterval() {
        if (this.currentSet >= this.totalSets) {
            return;
        }

        // Move to next interval
        this.currentSet++;
        if (this.currentSet < this.totalSets) {
            const nextInterval = this.intervals[this.currentSet];
            this.timeRemaining = nextInterval.duration || 0;

            // If we were paused, stay paused
            if (!this.isRunning) {
                this.updateDisplay();
            }
        } else {
            this.complete();
        }
    }

    tick() {
        if (this.timeRemaining > 0) {
            this.timeRemaining--;
            this.updateDisplay();
        } else {
            this.currentSet++;
            if (this.currentSet < this.totalSets) {
                const nextInterval = this.intervals[this.currentSet];
                this.timeRemaining = nextInterval.duration || 0;
                this.updateDisplay();
            } else {
                this.complete();
            }
        }
    }

    reset() {
        this.pause();
        this.currentSet = 0;
        this.timeRemaining = this.intervals[0]?.duration || 0;
        this.playPauseButton.textContent = 'Start';
        this.updateDisplay();
    }

    complete() {
        this.pause();
        this.currentActivityDisplay.textContent = 'Workout Complete!';
        this.nextUpDisplay.textContent = 'Great job!';
        this.timeDisplay.textContent = '';
        this.progressBar.style.width = '100%';
    }

    exit() {
        document.querySelector('.timer-view').style.display = 'none';
        document.querySelector('.container').style.display = 'block';
        this.reset();
    }
}

function workoutToTimerIntervals(workout) {
    if (workout.sets) {
        let timerIntervals = [];

        workout.sets.forEach(set => {
            for (let i = 0; i < (set.repeat || 1); i++) {
                set.intervals.forEach(interval => {
                    // Create a complete copy of the interval with all its properties
                    const timerInterval = {
                        ...interval,
                        activity: interval.activity,
                        duration: interval.duration,
                        intensity: interval.intensity,
                        description: interval.description,
                        // Preserve targetMetrics for cardio workouts
                        targetMetrics: interval.targetMetrics,
                        // Preserve strength metrics
                        sets: interval.sets,
                        reps: interval.reps,
                        weight: interval.weight,
                        // Preserve type for proper metric display
                        type: interval.type
                    };
                    timerIntervals.push(timerInterval);
                });
            }
        });

        return timerIntervals;
    }
    return [];
}


// Old version HANDLES STRETCHES (which wasn't actually used)
// function workoutToTimerIntervals(workout) {
//     // Check what type of workout we have
//     if (workout.sets) {
//         // Handle strength/cardio workouts 
//         let timerIntervals = [];

//         workout.sets.forEach(set => {
//             for (let i = 0; i < (set.repeat || 1); i++) {
//                 set.intervals.forEach(interval => {
//                     if (interval.duration) {
//                         timerIntervals.push({
//                             activity: interval.activity,
//                             duration: interval.duration,
//                             intensity: interval.intensity,
//                             description: interval.description
//                         });
//                     } else if (interval.reps) {
//                         timerIntervals.push({
//                             activity: `${interval.activity}${interval.setNumber ?
//                                 ` (Set ${interval.setNumber}/${interval.totalSets})` :
//                                 ''}`,
//                             sets: interval.sets,
//                             reps: interval.reps,
//                             weight: interval.weight,
//                             intensity: interval.intensity,
//                             description: interval.description,
//                             formCues: interval.formCues,
//                             type: interval.type
//                         });
//                     }
//                 });
//             }
//         });

//         return timerIntervals;
//     }
//     // Stretches don't currently have a Start Timer button so this is never invoked
//     else if (workout.stretches) {
//         // Handle flexibility workouts
//         let timerIntervals = [];

//         // Add a warm-up period
//         timerIntervals.push({
//             activity: "Warm-up",
//             duration: 300,  // 5 minutes
//             intensity: "Light movement",
//             description: "Gentle movement to prepare for stretching"
//         });

//         // Convert stretches to intervals
//         workout.stretches.forEach(stretch => {
//             // Parse duration string to seconds
//             let durationInSeconds;
//             if (typeof stretch.duration === 'string') {
//                 if (stretch.duration.includes('seconds')) {
//                     durationInSeconds = parseInt(stretch.duration);
//                 } else if (stretch.duration.includes('minutes')) {
//                     durationInSeconds = parseInt(stretch.duration) * 60;
//                 } else {
//                     // Default to 30 seconds if we can't parse
//                     durationInSeconds = 30;
//                 }
//             }

//             timerIntervals.push({
//                 activity: stretch.name,
//                 duration: durationInSeconds,
//                 intensity: "Gentle stretch",
//                 description: stretch.description,
//                 target: stretch.target,
//                 goal: stretch.goal
//             });

//             // Add a short transition period between stretches
//             if (stretch.duration.includes('each side')) {
//                 // For stretches that need to be done on both sides
//                 timerIntervals.push({
//                     activity: `${stretch.name} (Second Side)`,
//                     duration: durationInSeconds,
//                     intensity: "Gentle stretch",
//                     description: stretch.description,
//                     target: stretch.target,
//                     goal: stretch.goal
//                 });
//             }

//             // Add transition time between stretches
//             timerIntervals.push({
//                 activity: "Transition",
//                 duration: 10,  // 10 seconds to transition
//                 intensity: "Rest",
//                 description: "Move to next position"
//             });
//         });

//         // Add a cool-down period
//         timerIntervals.push({
//             activity: "Cool-down",
//             duration: 120,  // 2 minutes
//             intensity: "Light stretching",
//             description: "Gentle movement to finish session"
//         });

//         return timerIntervals;
//     }

//     console.error('Unknown workout format:', workout);
//     return [];
// }

// function startWorkoutTimer() {
//     console.log('Current workout:', currentWorkout); // Add this debug line

//     if (!currentWorkout) {
//         console.error('No workout selected');
//         return;
//     }

//     // Add validation for the workout structure
//     if (!currentWorkout.sets || !Array.isArray(currentWorkout.sets)) {
//         console.error('Invalid workout format - missing sets array:', currentWorkout);
//         return;
//     }

//     const timerIntervals = workoutToTimerIntervals(currentWorkout);

//     // Hide main app and show timer
//     document.querySelector('.container').style.display = 'none';
//     document.querySelector('.timer-view').style.display = 'flex';

//     // Initialize and start timer
//     const timer = new IntervalTimer();
//     timer.setWorkout(timerIntervals);

//     // Set up exit handler
//     document.querySelector('.exit').onclick = () => {
//         // Hide timer and show main app
//         document.querySelector('.timer-view').style.display = 'none';
//         document.querySelector('.container').style.display = 'block';

//         // Reset timer
//         timer.reset();
//     };
// }

function startWorkoutTimer() {
    if (!currentWorkout) {
        console.error('No workout selected');
        return;
    }

    const timerIntervals = workoutToTimerIntervals(currentWorkout);
    
    // Create workout display instance for the timer
    const workoutDisplay = new WorkoutDisplay(null, currentWorkout, { unitSystem: 'imperial' });

    // Hide main app and show timer
    document.querySelector('.container').style.display = 'none';
    document.querySelector('.timer-view').style.display = 'flex';

    // Initialize and start timer with workout display
    const timer = new IntervalTimer(workoutDisplay);
    timer.setWorkout(timerIntervals);

        // Set up exit handler
        document.querySelector('.exit').onclick = () => {
            // Hide timer and show main app
            document.querySelector('.timer-view').style.display = 'none';
            document.querySelector('.container').style.display = 'block';
    
            // Reset timer
            timer.reset();
        };
}