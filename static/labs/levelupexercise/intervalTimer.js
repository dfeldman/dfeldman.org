class IntervalTimer {
    constructor(workoutDisplay) {
        this.workoutDisplay = workoutDisplay;    
        this.totalDuration = 0;
        this.elapsedDuration = 0;
        
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


    // Calculate total duration of timed intervals
    this.totalDuration = workout.reduce((total, interval) => 
        total + (interval.duration || 0), 0);
        
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
    
    // Handle timed vs untimed intervals
    if (currentInterval.duration) {
        this.timeDisplay.style.display = 'block';
        this.playPauseButton.style.display = 'block';
        this.timeDisplay.textContent = this.formatTime(this.timeRemaining);
        const totalIntervalTime = currentInterval.duration;
        const progress = ((totalIntervalTime - this.timeRemaining) / totalIntervalTime) * 100;
        this.progressBar.style.width = `${progress}%`;
        this.skipButton.textContent = 'Skip';
        this.skipButton.className = 'skip';
    } else {
        this.timeDisplay.style.display = 'none';
        this.playPauseButton.style.display = 'none';
        this.progressBar.style.width = '0%';
        this.skipButton.textContent = 'Next';
        this.skipButton.className = 'skip next-style'; // Add CSS for this
    }

    // Use the workout display render method
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
            this.elapsedDuration++;
            this.updateProgress();
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
    

    updateProgress() {
        if (this.totalDuration > 0) {
            const progress = (this.elapsedDuration / this.totalDuration) * 100;
            this.progressBar.style.width = `${progress}%`;
        }
    }

    reset() {
        this.pause();
        this.currentSet = 0;
        this.elapsedDuration = 0;
        this.timeRemaining = this.intervals[0]?.duration || 0;
        this.playPauseButton.textContent = 'Start';
        this.updateProgress();
        this.updateDisplay();
    }

    complete() {
        // Ideally there should be a congratulations screen and fill the progress bar. 
        // TODO 
        this.pause();
        // Exit timer view
        document.querySelector('#timer-view').style.display = 'none';
        
        // Show rating modal
        const ratingModal = new WorkoutRating();
        ratingModal.show();
    }

    exit() {
        document.querySelector('#timer-view').style.display = 'none';
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
    document.querySelector('#timer-view').style.display = 'flex';

    // Initialize and start timer with workout display
    const timer = new IntervalTimer(workoutDisplay);
    timer.setWorkout(timerIntervals);

        // Set up exit handler
        document.querySelector('.exit').onclick = () => {
            // Hide timer and show main app
            document.querySelector('#timer-view').style.display = 'none';
           document.querySelector('.container').style.display = 'block';
    
            // Reset timer
            timer.reset();
        };
}