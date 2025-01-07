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

        // Power-ups system
        this.powerUps = [];
        this.powerUpMessages = [
            { text: "Not bad!", emoji: "⭐️" },
            { text: "Run like the wind!", emoji: "💨" },
            { text: "Getting stronger!", emoji: "💪" },
            { text: "Keep it up!", emoji: "🔥" },
            { text: "You're crushing it!", emoji: "⚡️" }
        ];

        // DOM elements
  
this.timeDisplay = document.querySelector('#timer-view .timer-display');
console.log('Found timer display:', this.timeDisplay); // Debug

        this.intervalBadge = document.querySelector('.interval-badge-text');
        this.progressSection = document.querySelector('.progress-section');
        this.powerUpsGrid = document.querySelector('.powerups-grid');
        this.playPauseButton = document.querySelector('.btn-pause');
        this.skipButton = document.querySelector('.btn-skip');

        // Bind event listeners
        this.playPauseButton.addEventListener('click', () => this.togglePlayPause());
        this.skipButton.addEventListener('click', () => this.skipInterval());
    }

    updateDisplay() {
        if (this.currentSet >= this.totalSets) {
            this.complete();
            return;
        }
    
        const currentInterval = this.intervals[this.currentSet];
        console.log('Current interval:', currentInterval); // Debug
        console.log('Time remaining:', this.timeRemaining); // Debug
        
        // Update timer display
        if (currentInterval.duration) {
            const timeStr = this.formatTime(this.timeRemaining);
            console.log('Formatting time:', this.timeRemaining, 'as:', timeStr); // Debug
            this.timeDisplay.textContent = timeStr;
            this.playPauseButton.style.display = 'block';
        } else {
            this.timeDisplay.textContent = "--:--";
            this.playPauseButton.style.display = 'none';
        }

        // Update interval badge
        let badgeEmoji = '🏃';
        if (currentInterval.type === 'rest') badgeEmoji = '🚶';
        if (currentInterval.type === 'warmup') badgeEmoji = '⭐️';
        if (currentInterval.type === 'cooldown') badgeEmoji = '✨';

        this.intervalBadge.innerHTML = `
            <span class="text-3xl mr-2">${badgeEmoji}</span>
            ${currentInterval.activity} #${this.currentSet + 1}
        `;

        // Update progress tracks
        this.updateProgressTracks();

        // Maybe add a power-up
        if (this.elapsedDuration % 300 === 0 && this.elapsedDuration > 0) {
            this.addPowerUp();
        }
    }


    updateProgressTracks() {
        console.log('Updating progress tracks');
        let progressHTML = '';
    
        // Past intervals (show as complete)
        for (let i = 0; i < this.currentSet; i++) {
            console.log('Past interval:', this.intervals[i]);
            // ... rest of code
        }
    
        // Current interval
        const currentInterval = this.intervals[this.currentSet];
        const progress = currentInterval.duration ? 
            ((currentInterval.duration - this.timeRemaining) / currentInterval.duration) * 100 : 0;
        
        console.log('Current progress:', progress);
        
        progressHTML += `
            <div class="progress-item">
                <span class="progress-emoji">🏃</span>
                <div class="flex-1">
                    <div class="progress-bar">
                        <div class="progress-fill current" style="width: ${progress}%"></div>
                    </div>
                    <p class="text-blue-600 font-bold mt-1">${currentInterval.activity}</p>
                </div>
            </div>
        `;
    

        // Next interval (if exists)
        if (this.currentSet < this.totalSets - 1) {
            const nextInterval = this.intervals[this.currentSet + 1];
            progressHTML += `
                <div class="progress-item">
                    <span class="progress-emoji">${nextInterval.type === 'rest' ? '🚶' : '🏃'}</span>
                    <div class="flex-1">
                        <div class="progress-bar">
                            <div class="progress-fill upcoming"></div>
                        </div>
                        <p class="text-gray-600 font-bold mt-1">${nextInterval.activity} Coming Up</p>
                    </div>
                </div>
            `;
        }
        console.log('Setting progress HTML:', progressHTML);

        this.progressSection.innerHTML = `
            <h2 class="progress-title">QUEST PROGRESS</h2>
            <div class="space-y-4">
                ${progressHTML}
            </div>
        `;


    }

    addPowerUp() {
        const powerUp = this.powerUpMessages[Math.floor(Math.random() * this.powerUpMessages.length)];
        this.powerUps.push(powerUp);
        
        // Update power-ups display
        let powerUpsHTML = '';
        this.powerUps.slice(-2).forEach(pu => {
            powerUpsHTML += `
                <div class="powerup-card">
                    <span class="powerup-emoji">${pu.emoji}</span>
                    <p class="font-bold mt-1">${pu.text}</p>
                </div>
            `;
        });
        
        this.powerUpsGrid.innerHTML = powerUpsHTML;
    }

    complete() {
        console.log('Completing workout...');
        this.pause();
        
        const timerView = document.querySelector('#timer-view');
        const victoryView = document.querySelector('#victory-view');
        
        console.log('Timer view:', timerView);
        console.log('Victory view:', victoryView);
        
        if (timerView) timerView.style.display = 'none';
        if (victoryView) {
            console.log('Setting victory view display to block');
            victoryView.style.display = 'block';
            // testing
            victoryView.style.display = 'flex';  // Change to flex instead of block
            victoryView.style.visibility = 'visible';
            victoryView.style.zIndex = '1000';   // Ensure it's on top
     
            
            // Update stats
            const timeElement = document.querySelector('#total-time');
            const powerUpsElement = document.querySelector('#power-ups');
            const xpElement = document.querySelector('#xp-earned');
            
            console.log('Stat elements:', { timeElement, powerUpsElement, xpElement });
            
            if (timeElement) timeElement.textContent = this.formatTime(this.elapsedDuration);
            if (powerUpsElement) powerUpsElement.textContent = this.powerUps.length;
            
            // Calculate XP
            const xp = Math.floor(this.elapsedDuration / 60) * 100 + this.powerUps.length * 50;
            if (xpElement) xpElement.textContent = xp;
            
            document.querySelector('.victory-exit').onclick = () => {
                document.querySelector('#victory-view').style.display = 'none';
                document.querySelector('.container').style.display = 'block';
                this.reset();
            };
            console.log('Stats updated:', {
                time: this.formatTime(this.elapsedDuration),
                powerUps: this.powerUps.length,
                xp: xp
            });
        } else {
            console.error('Victory view not found in DOM!');
        }
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
        console.log('Tick! Time remaining:', this.timeRemaining);

        if (this.timeRemaining > 0) {
            this.timeRemaining--;
            this.elapsedDuration++;
            // Remove this line: this.updateProgress();
            this.updateDisplay(); // This already handles progress through updateProgressTracks
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
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    setWorkout(workout) {
        this.playPauseButton.textContent = 'PAUSE';

        this.intervals = workout;
        this.totalSets = workout.length;
        this.totalDuration = workout.reduce((total, interval) => 
            total + (interval.duration || 0), 0);
        
        // Initialize first interval properly
        const firstInterval = workout[0];
        if (firstInterval && typeof firstInterval.duration === 'number') {
            this.timeRemaining = firstInterval.duration;
            // Explicitly set initial display
            if (this.timeDisplay) {
                this.timeDisplay.textContent = this.formatTime(this.timeRemaining);
            } else {
                console.error('Time display element not found!');
            }
        }
        
        this.currentSet = 0;
        this.elapsedDuration = 0;
        this.powerUps = [];
        
        this.updateDisplay();
        this.start(); 

    }
    reset() {
        this.pause();
        this.currentSet = 0;
        this.elapsedDuration = 0;
        this.timeRemaining = this.intervals[0]?.duration || 0;
        this.playPauseButton.textContent = 'Start';
        // Remove this line: this.updateProgress();
        this.updateDisplay();
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
    const workoutDisplay = new WorkoutDisplay(null, currentWorkout, { unitSystem: 'imperial' });

    // First create and setup timer
    const timer = new IntervalTimer(workoutDisplay);
    
    // Then make timer view visible
    document.querySelector('.container').style.display = 'none';
    document.querySelector('#timer-view').style.display = 'flex';
    
    // Finally set the workout after the view is visible
    setTimeout(() => {
        timer.setWorkout(timerIntervals);
    }, 0);

    document.querySelector('.exit').onclick = () => {
        document.querySelector('#timer-view').style.display = 'none';
        document.querySelector('.container').style.display = 'block';
        timer.reset();
    };



}