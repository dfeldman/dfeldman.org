function updateDashboard() {
    // Get workout history from UserData
    const workouts = userData.getWorkoutHistory();
    
    // Transform the data to match the viewer's expected format
    const formattedWorkouts = workouts.map(workout => ({
        type: workout.activity,
        level: workout.level,
        description: `${workout.activity.charAt(0).toUpperCase() + workout.activity.slice(1)} Workout`,
        date: workout.timestamp,
        totalDuration: workout.duration,
        difficulty: workout.difficulty
    }));

    // Initialize the viewer with the workout history
    new WorkoutHistoryViewer('workout-history', formattedWorkouts);
}

class WorkoutHistoryViewer {
    constructor(containerId, workouts) {
        this.container = document.getElementById(containerId);
        this.workouts = workouts;
        this.render();
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
        }).format(date);
    }

    formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return remainingSeconds === 0 ? 
            `${minutes} min` : 
            `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    getActivityDescription(workout) {
        // If workout has a description, use it
        if (workout.description) return workout.description;
    
        // Use activity field instead of type
        const activity = workout.activity.charAt(0).toUpperCase() + workout.activity.slice(1);
        const difficulty = workout.difficulty ? 
            ` (${workout.difficulty.charAt(0).toUpperCase() + workout.difficulty.slice(1)})` : 
            '';
        return `${activity} Workout${difficulty}`;
    }

    getActivityColor(activity) {
        const colors = {
            run: '#2563eb',
            bike: '#059669',
            swim: '#0891b2',
            row: '#9333ea',
            strength: '#7c3aed',
            flexibility: '#db2777'
        };
        return colors[activity] || '#6b7280';
    }

    groupByMonth(workouts) {
        const grouped = workouts.reduce((acc, workout) => {
            const date = new Date(workout.date || workout.timestamp);
            const month = date.toLocaleString('en-US', { 
                month: 'long', 
                year: 'numeric' 
            });
            
            if (!acc[month]) acc[month] = [];
            acc[month].push(workout);
            return acc;
        }, {});

        // Sort workouts within each month by date (newest first)
        Object.values(grouped).forEach(monthWorkouts => {
            monthWorkouts.sort((a, b) => {
                const dateA = new Date(a.date || a.timestamp);
                const dateB = new Date(b.date || b.timestamp);
                return dateB - dateA;
            });
        });

        return grouped;
    }

    renderWorkoutCard(workout) {
        const backgroundColor = this.getActivityColor(workout.activity);
        
        return `
            <div class="workout-card" style="background-color: ${backgroundColor}">
                <div class="level-circle">
                    <span class="level-number">${workout.level}</span>
                    <span class="level-label">LEVEL</span>
                </div>
                ${workout.difficulty ? `
                    <div class="workout-difficulty">
                        ${workout.difficulty.toUpperCase()}
                    </div>
                ` : ''}
                <div class="workout-content">
                    <div class="workout-date">
                        ${this.formatDate(workout.date || workout.timestamp)}
                    </div>
                    <div class="workout-description">
                        ${this.getActivityDescription(workout)}
                    </div>
                    <div class="workout-duration">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" 
                             stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        ${this.formatDuration(workout.totalDuration || workout.duration)}
                    </div>
                </div>
            </div>
        `;
    }

    exportJSON() {
        const dataStr = JSON.stringify(this.workouts, null, 2);
        this.downloadFile(dataStr, 'workout-history.json', 'application/json');
    }

    exportCSV() {
        const headers = ['Date', 'Activity', 'Level', 'Duration', 'Difficulty'];
        const rows = [headers];
        
        this.workouts.forEach(workout => {
            rows.push([
                workout.date || workout.timestamp,
                workout.type,
                workout.level,
                workout.totalDuration || workout.duration,
                workout.difficulty || ''
            ]);
        });
        
        const csvContent = rows.map(row => 
            row.map(cell => 
                typeof cell === 'string' ? `"${cell}"` : cell
            ).join(',')
        ).join('\n');
        
        this.downloadFile(csvContent, 'workout-history.csv', 'text/csv');
    }

    downloadFile(content, fileName, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    render() {
        const groupedWorkouts = this.groupByMonth(this.workouts);
        let html = '';

        if (this.workouts.length === 0) {
            html = `
                <div class="empty-state">
                    <h2>No workouts yet</h2>
                    <p>Complete your first workout to see it here!</p>
                </div>
            `;
        } else {
            // Render workout groups
            Object.entries(groupedWorkouts).forEach(([month, workouts]) => {
                html += `
                <div class="container">
                    <div class="month-group">
                        <div class="month-header">
                            <h2 class="month-title">${month}</h2>
                            <span class="workout-count">
                                ${workouts.length} workout${workouts.length !== 1 ? 's' : ''}
                            </span>
                        </div>
                        <div class="workout-list">
                            ${workouts.map(workout => 
                                this.renderWorkoutCard(workout)
                            ).join('')}
                        </div>
                    </div>
                </div>
                `;
            });
        }

        // Add export buttons
        html += `
            <div class="export-bar">
                <button class="export-button" id="export-json">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" 
                         stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Export JSON
                </button>
                <button class="export-button" id="export-csv">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" 
                         stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    Export CSV
                </button>
            </div>
        `;

        this.container.innerHTML = html;

        // Add event listeners
        document.getElementById('export-json')?.addEventListener('click', () => this.exportJSON());
        document.getElementById('export-csv')?.addEventListener('click', () => this.exportCSV());
    }
}

