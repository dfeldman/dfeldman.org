class UserData {
    constructor() {
        this.VALID_ACTIVITIES = ['bike', 'run', 'swim', 'row', 'strength', 'flexibility'];
        this.loadData();
    }

    // Initialize or load existing data
    loadData() {
        // Load or initialize levels
        const storedLevels = localStorage.getItem('activityLevels');
        this.activityLevels = storedLevels ? 
            JSON.parse(storedLevels) : 
            this.VALID_ACTIVITIES.reduce((acc, activity) => {
                acc[activity] = 0;
                return acc;
            }, {});

        // Load or initialize workout history
        this.workoutHistory = JSON.parse(localStorage.getItem('workoutHistory') || '[]');

        // Load or initialize preferences
        const storedPreferences = localStorage.getItem('userPreferences');
        this.preferences = storedPreferences ? 
            JSON.parse(storedPreferences) : 
            {
                units: 'imperial',
                sound: true
            };
    }

    // Activity level getters and setters
    getLevel(activity) {
        if (!this.VALID_ACTIVITIES.includes(activity)) {
            throw new Error(`Invalid activity: ${activity}`);
        }
        return this.activityLevels[activity];
    }

    getWorkoutsAtCurrentLevel(activity) {
        if (!this.VALID_ACTIVITIES.includes(activity)) {
            throw new Error(`Invalid activity: ${activity}`);
        }
    
        const currentLevel = this.getLevel(activity);
        
        // Filter workouts by activity and level, and ensure they were completed (100%)
        return this.workoutHistory.filter(workout => 
            workout.activity === activity && 
            workout.level === currentLevel &&
            workout.percentCompleted === 100
        ).length;
    }

    setLevel(activity, level) {
        if (!this.VALID_ACTIVITIES.includes(activity)) {
            throw new Error(`Invalid activity: ${activity}`);
        }
        if (level < 0 || level > 100 || !Number.isInteger(level)) {
            throw new Error('Level must be an integer between 0 and 100');
        }
        
        this.activityLevels[activity] = level;
        localStorage.setItem('activityLevels', JSON.stringify(this.activityLevels));
    }

    // Record a completed workout
    recordWorkout(workout) {
        const workoutRecord = {
            activity: workout.activity,
            level: workout.level,
            duration: workout.duration,
            difficulty: workout.difficulty,
            percentCompleted: 100,
            timestamp: new Date().toISOString()
        };

        this.workoutHistory.push(workoutRecord);
        localStorage.setItem('workoutHistory', JSON.stringify(this.workoutHistory));
    }

    // Preference getters and setters
    getPreference(key) {
        return this.preferences[key];
    }

    setPreference(key, value) {
        this.preferences[key] = value;
        localStorage.setItem('userPreferences', JSON.stringify(this.preferences));
    }

    // Get all workout history
    getWorkoutHistory() {
        return [...this.workoutHistory];
    }

    // Export functions
    exportAsJSON() {
        const data = {
            activityLevels: this.activityLevels,
            workoutHistory: this.workoutHistory,
            preferences: this.preferences
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        this._downloadFile(blob, 'workout_data.json');
    }

    exportAsCSV() {
        // Create header row
        const headers = ['timestamp', 'activity', 'level', 'duration', 'difficulty', 'percentCompleted'];
        
        // Convert workout history to CSV rows
        const rows = [
            headers.join(','),
            ...this.workoutHistory.map(workout => 
                headers.map(header => {
                    // Wrap string values in quotes
                    const value = workout[header];
                    return typeof value === 'string' ? `"${value}"` : value;
                }).join(',')
            )
        ];

        const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
        this._downloadFile(blob, 'workout_data.csv');
    }

    // Helper function for file downloads
    _downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }
}