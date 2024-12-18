// Base configurations for swimming workouts
const SWIM_CONFIGS = {
    beginner: {
        type: "technique",
        levelRange: [1, 10],
        // Rest after every X laps (decreases as level increases)
        restEvery: level => Math.max(1, 3 - Math.floor((level - 1) / 3)),
        // Total laps increases with level
        totalLaps: level => 4 + Math.floor((level - 1) / 2) * 2,
        // Rest duration between sets
        restDuration: 60  // 60 seconds rest
    },
    
    intervals: {
        type: "intervals",
        levelRange: [11, 20],
        // Start with 2 laps per set, increase every other level
        lapsPerSet: level => Math.floor(2 + (level - 11) / 2),
        // Rest duration decreases with level
        restDuration: level => Math.max(45, 90 - (level - 11) * 5),
        // Pace per lap improves with level (in seconds)
        targetPace: level => Math.max(60, 90 - (level - 11) * 3),
        sets: 3  // Always do 3 sets for consistency
    },
    
    endurance: {
        phases: {
            build: {
                levelRange: [21, 30],
                warmupLaps: 4,
                cooldownLaps: 4,
                baseLaps: 20,
                lapIncrease: 1,
                basePace: 60,
                paceReduction: 1
            },
            continuous: {
                levelRange: [31, 70],
                warmupLaps: 6,
                cooldownLaps: 4,
                baseLaps: 40,
                lapIncrease: 0.5,
                basePace: 45,
                paceReduction: 0.125
            },
            distance: {
                levelRange: [71, 100],
                warmupLaps: 8,
                cooldownLaps: 4,
                baseLaps: 60,
                lapIncrease: 0.5,
                basePace: 40,
                paceReduction: 0.167
            }
        }
    }
};

function generateSwimHTML(workout) {
    // Helper functions
    function formatPace(seconds) {
        if (!seconds) return '';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    // Generate header with key workout metrics
    const header = `
        <div class="workout-header">
            <h4>${workout.description}</h4>
            <div class="metrics-grid">
                <div class="metric">
                    <span class="metric-label">Total Distance</span>
                    <span class="metric-value">${workout.totalDistance} yards</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Laps</span>
                    <span class="metric-value">${workout.totalLaps} laps</span>
                </div>
                ${workout.targetPace ? `
                    <div class="metric">
                        <span class="metric-label">Target Pace</span>
                        <span class="metric-value">${formatPace(workout.targetPace)} per lap</span>
                    </div>
                ` : ''}
            </div>
        </div>`;

    // Generate simple, memorable workout structure
    const structure = `
        <div class="workout-structure">
            <h5>Workout Summary</h5>
            <div class="swim-sets">
                ${workout.sets.map(set => `
                    ${set.repeat > 1 ? `<div class="repeat-header">Repeat ${set.repeat} times:</div>` : ''}
                    ${set.intervals.map(interval => `
                        <div class="swim-interval">
                            <div class="interval-main">
                                ${interval.laps ? `
                                    <strong>${interval.activity}</strong>
                                    ${interval.targetPace ? 
                                        `<br>Target: ${formatPace(interval.targetPace)} per lap` : 
                                        ''}
                                ` : interval.duration ? `
                                    <strong>Rest ${Math.floor(interval.duration / 60)} minutes</strong>
                                ` : ''}
                            </div>
                            ${interval.intensity ? `
                                <div class="interval-intensity">${interval.intensity}</div>
                            ` : ''}
                            ${interval.description ? `
                                <div class="interval-description">${interval.description}</div>
                            ` : ''}
                        </div>
                    `).join('')}
                `).join('')}
            </div>
        </div>`;

    // Generate form cues section
    const formCues = workout.formCues ? `
        <div class="form-cues">
            <h5>Technique Focus</h5>
            <ul>
                ${workout.formCues.map(cue => `<li>${cue}</li>`).join('')}
            </ul>
        </div>` : '';

    // Generate notes section with key reminders
    const notes = workout.notes ? `
        <div class="workout-notes">
            <h5>Remember</h5>
            <ul>
                ${workout.notes.map(note => `<li>${note}</li>`).join('')}
            </ul>
        </div>` : '';

    // Combine all sections
    // no timer button for swimming
    return `
        ${styles}
        ${header}
        ${structure}
        ${formCues}
        ${notes}
    `;
}

function generateSwimWorkout(level) {
    const workout = {
        type: 'swim',
        level: level
    };

    // Add form cues that apply to all swimming workouts
    workout.formCues = [
        'Focus on steady breathing pattern',
        'Keep your head aligned with your spine',
        'Long, smooth strokes',
        'Kick from your hips, not knees',
        'Streamline position off every wall'
    ];

    if (level <= 10) {
        // Beginner phase - focus on technique
        const config = SWIM_CONFIGS.beginner;
        workout.phase = 'technique';
        workout.description = 'Swimming Fundamentals';
        
        const lapsPerSet = config.restEvery(level);
        const totalLaps = config.totalLaps(level);
        const sets = Math.floor(totalLaps / lapsPerSet);

        workout.notes = [
            `Swim ${lapsPerSet} lap(s) at a time`,
            'Rest 60 seconds between sets',
            'Focus on form over speed',
            'Take longer breaks if needed for proper form'
        ];

        // Simple set structure
        workout.sets = [
            {
                repeat: sets,
                intervals: [
                    {
                        activity: `Swim ${lapsPerSet} lap${lapsPerSet > 1 ? 's' : ''}`,
                        laps: lapsPerSet,
                        intensity: "Focus on technique",
                        description: "Count your strokes per lap"
                    },
                    {
                        activity: "Rest",
                        duration: config.restDuration,
                        intensity: "Full recovery"
                    }
                ]
            }
        ];

        workout.totalLaps = totalLaps;
        workout.lapDistance = 25;
        workout.totalDistance = totalLaps * 25;
        workout.totalDuration = totalLaps * 120;  // 90 seconds
    }
    else if (level <= 20) {
        // Interval phase
        const config = SWIM_CONFIGS.intervals;
        workout.phase = 'intervals';
        workout.description = 'Interval Swimming';
        
        const lapsPerSet = config.lapsPerSet(level);
        const restDuration = config.restDuration(level);
        const targetPace = config.targetPace(level);

        workout.notes = [
            `Target ${Math.floor(targetPace / 60)}:${(targetPace % 60).toString().padStart(2, '0')} per lap`,
            'Focus on consistent pace',
            'Use rest periods to check your times',
            'Maintain stroke count each lap'
        ];

        // Simple interval structure
        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up",
                    laps: 2,
                    intensity: "Easy pace",
                    description: "Focus on form"
                }]
            },
            {
                repeat: config.sets,
                intervals: [
                    {
                        activity: `Swim ${lapsPerSet} laps`,
                        laps: lapsPerSet,
                        intensity: "Target pace",
                        targetPace: targetPace,
                        description: `Aim for ${Math.floor(targetPace / 60)}:${(targetPace % 60).toString().padStart(2, '0')} per lap`
                    },
                    {
                        activity: "Rest",
                        duration: restDuration,
                        intensity: "Full recovery"
                    }
                ]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    laps: 2,
                    intensity: "Easy pace"
                }]
            }
        ];

        // Calculate totals
        const mainSetLaps = config.sets * lapsPerSet;
        workout.totalLaps = mainSetLaps + 4;  // Including warm-up and cool-down
        workout.lapDistance = 25;
        workout.totalDistance = workout.totalLaps * 25;
        workout.totalDuration = mainSetLaps * targetPace;
    }
    else {
        // Find appropriate endurance phase
        const phase = Object.entries(SWIM_CONFIGS.endurance.phases)
            .find(([_, config]) => 
                level >= config.levelRange[0] && level <= config.levelRange[1]
            )[1];

        workout.phase = 'endurance';
        workout.description = level > 70 ? 'Distance Swimming' : 'Endurance Swimming';

        // Calculate targets
        const levelOffset = phase.levelRange[0] - 1;
        const mainLaps = Math.floor(phase.baseLaps + 
            (level - phase.levelRange[0]) * phase.lapIncrease);
        const targetPace = Math.max(35, phase.basePace - 
            Math.floor((level - phase.levelRange[0]) * phase.paceReduction));

        workout.notes = [
            `Target ${Math.floor(targetPace / 60)}:${(targetPace % 60).toString().padStart(2, '0')} per lap`,
            'Count strokes per lap',
            'Breathe every 2-3 strokes as needed',
            'Focus on efficient turns'
        ];

        // Simple endurance structure
        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up",
                    laps: phase.warmupLaps,
                    intensity: "Easy pace",
                    description: "Gradually build pace"
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Main Set",
                    laps: mainLaps,
                    intensity: "Target pace",
                    targetPace: targetPace,
                    description: `Aim for ${Math.floor(targetPace / 60)}:${(targetPace % 60).toString().padStart(2, '0')} per lap`
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    laps: phase.cooldownLaps,
                    intensity: "Easy pace"
                }]
            }
        ];

        // Calculate totals
        workout.totalLaps = phase.warmupLaps + mainLaps + phase.cooldownLaps;
        workout.lapDistance = 25;
        workout.totalDistance = workout.totalLaps * 25;
        workout.totalDuration = workout.totalLaps * targetPace;
    }

    // Generate HTML display
    //workout.html = generateSwimHTML(workout);
    
    return workout;
}