// Base configurations for cycling workouts
const BIKE_CONFIGS = {
    beginner: {
        type: "steady",
        levelRange: [1, 10],
        baseSpeed: 10,
        speedIncrease: 0.2,
        baseWatts: 60,
        wattsIncrease: 4,
        baseCadence: 60,
        cadenceIncrease: 1
    },
    
    intervals: {
        type: "intervals",
        levelRange: [11, 20],
        patterns: {
            beginner: {  // Level 11-15
                pushDurationStart: 60,
                pushDurationIncrease: 15,
                recoveryDurationStart: 120,
                recoveryDurationDecrease: 10,
                startingSets: 6,
                setsDecrease: 0.5,  // Decrease sets every 2 levels
                baseSpeed: 12,
                speedIncrease: 0.5,
                baseWatts: 75,
                wattsIncrease: 10
            },
            intermediate: {  // Level 16-20
                pushDurationStart: 180,
                pushDurationIncrease: 30,
                recoveryDuration: 60,
                startingSets: 4,
                setsDecrease: 0.5,
                baseSpeed: 15,
                speedIncrease: 0.5,
                baseWatts: 125,
                wattsIncrease: 15
            }
        }
    },
    
    endurance: {
        type: "endurance",
        levelRange: [21, 100],
        phases: {
            build: {
                levelRange: [21, 30],
                time: 30,
                baseSpeed: 14,
                speedIncrease: 0.3,
                baseWatts: 120,
                wattsIncrease: 5
            },
            sustained: {
                levelRange: [31, 70],
                time: 45,
                baseSpeed: 15,
                speedIncrease: 0.05,
                baseWatts: 150,
                wattsIncrease: 0.75
            },
            advanced: {
                levelRange: [71, 100],
                time: 60,
                baseSpeed: 16,
                speedIncrease: 0.067,
                baseWatts: 170,
                wattsIncrease: 1
            }
        }
    }
};

function generateBikeWorkout(level) {
    const workout = {
        type: 'bike',
        level: level
    };

    // Add form cues that apply to all cycling workouts
    workout.formCues = [
        'Keep shoulders relaxed and elbows slightly bent',
        'Maintain proper seat height - slight bend in knee at bottom',
        'Keep cadence smooth and consistent',
        'Engage core to support lower back',
        'Look ahead, not down at the console'
    ];

    if (level <= 10) {
        // Beginner phase - steady state riding
        const config = BIKE_CONFIGS.beginner;
        const speed = config.baseSpeed + (level - 1) * config.speedIncrease;
        const watts = config.baseWatts + (level - 1) * config.wattsIncrease;
        const cadence = config.baseCadence + (level - 1) * config.cadenceIncrease;

        workout.phase = 'basic';
        workout.description = 'Foundation Cycling';
        workout.notes = [
            'Focus on maintaining consistent cadence',
            'Stay relaxed in upper body',
            'Take breaks if needed',
            'Hydrate regularly',
            `Target cadence: ${cadence} RPM`
        ];

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up Spin",
                    duration: 300,
                    intensity: "Light resistance",
                    targetMetrics: {
                        speed: speed - 2,
                        cadence: cadence - 5,
                        watts: watts - 20
                    }
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Main Ride",
                    duration: 1200,
                    intensity: "Moderate resistance",
                    targetMetrics: {
                        speed: speed,
                        cadence: cadence,
                        watts: watts
                    }
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    duration: 300,
                    intensity: "Light resistance",
                    targetMetrics: {
                        speed: speed - 2,
                        cadence: cadence - 5,
                        watts: watts - 20
                    }
                }]
            }
        ];
        workout.totalDuration = 1800;  // 30 minutes
    }
    else if (level <= 20) {
        // Get the appropriate interval pattern
        const config = level <= 15 ? 
            BIKE_CONFIGS.intervals.patterns.beginner :
            BIKE_CONFIGS.intervals.patterns.intermediate;
        
        const levelOffset = level <= 15 ? 11 : 16;
        const adjustedLevel = level - levelOffset;

        // Calculate interval parameters
        const pushDuration = config.pushDurationStart + adjustedLevel * config.pushDurationIncrease;
        const recoveryDuration = config.recoveryDuration || 
            Math.max(60, config.recoveryDurationStart - adjustedLevel * config.recoveryDurationDecrease);
        const sets = Math.max(2, config.startingSets - Math.floor(adjustedLevel / 2) * config.setsDecrease);
        const pushSpeed = config.baseSpeed + adjustedLevel * config.speedIncrease;
        const pushWatts = config.baseWatts + adjustedLevel * config.wattsIncrease;

        workout.phase = 'intervals';
        workout.description = `Cycling Power Builder - Level ${level}`;
        workout.notes = [
            'Push hard during work intervals',
            'Maintain form even when tired',
            'Use recovery intervals to catch breath',
            'Focus on smooth transitions',
            'Adjust resistance to hit target watts'
        ];

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up Spin",
                    duration: 300,
                    intensity: "Progressive resistance build",
                    targetMetrics: {
                        speed: "8-10",
                        cadence: "60-70",
                        watts: "40-60"
                    }
                }]
            },
            {
                repeat: Math.floor(sets),
                intervals: [
                    {
                        activity: "Power Interval",
                        duration: pushDuration,
                        intensity: "High resistance",
                        targetMetrics: {
                            speed: pushSpeed,
                            cadence: 80,
                            watts: pushWatts
                        }
                    },
                    {
                        activity: "Recovery",
                        duration: recoveryDuration,
                        intensity: "Light resistance",
                        targetMetrics: {
                            speed: pushSpeed - 4,
                            cadence: 70,
                            watts: pushWatts * 0.6
                        }
                    }
                ]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    duration: 300,
                    intensity: "Decreasing resistance",
                    targetMetrics: {
                        speed: "10-8",
                        cadence: "70-60",
                        watts: "60-40"
                    }
                }]
            }
        ];
        workout.totalDuration = 300 + (pushDuration + recoveryDuration) * sets + 300;
    }
    else {
        // Find appropriate endurance phase
        const phase = Object.entries(BIKE_CONFIGS.endurance.phases)
            .find(([_, config]) => 
                level >= config.levelRange[0] && level <= config.levelRange[1]
            )[1];

        const levelOffset = phase.levelRange[0] - 1;
        const speed = phase.baseSpeed + (level - phase.levelRange[0]) * phase.speedIncrease;
        const watts = phase.baseWatts + (level - phase.levelRange[0]) * phase.wattsIncrease;

        workout.phase = 'endurance';
        workout.description = 'Endurance Cycling';
        workout.notes = [
            'Maintain steady effort throughout',
            'Focus on smooth pedaling technique',
            'Stay well hydrated',
            'Monitor heart rate if possible',
            'Keep upper body relaxed'
        ];

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up",
                    duration: 600,
                    intensity: "Progressive build",
                    targetMetrics: {
                        speed: speed - 3,
                        cadence: "70-80",
                        watts: watts * 0.7
                    }
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Main Set",
                    duration: (phase.time - 15) * 60,
                    intensity: "Steady effort",
                    targetMetrics: {
                        speed: speed,
                        cadence: 85,
                        watts: watts
                    }
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    duration: 300,
                    intensity: "Light resistance",
                    targetMetrics: {
                        speed: speed - 3,
                        cadence: "70-60",
                        watts: watts * 0.6
                    }
                }]
            }
        ];
        workout.totalDuration = phase.time * 60;
    }

    // Generate HTML display
    workout.html = generateBikeHTML(workout);
    
    return workout;
}

function generateBikeHTML(workout) {
    // Helper function to format metrics
    function formatMetrics(metrics) {
        if (!metrics) return '';
        
        const parts = [];
        if (metrics.speed) parts.push(`${metrics.speed} mph`);
        if (metrics.cadence) parts.push(`${metrics.cadence} RPM`);
        if (metrics.watts) parts.push(`${metrics.watts}W`);
        
        return parts.join(' / ');
    }

    // Generate header section
    const header = `
        <div class="workout-header">
            <h4>${workout.description}</h4>
            <div class="metrics-grid">
                <div class="metric">
                    <span class="metric-label">Total Time</span>
                    <span class="metric-value">${Math.round(workout.totalDuration / 60)} minutes</span>
                </div>
                ${workout.averageWatts ? `
                    <div class="metric">
                        <span class="metric-label">Target Power</span>
                        <span class="metric-value">${workout.averageWatts} watts</span>
                    </div>
                ` : ''}
            </div>
        </div>`;

    // Generate workout structure
    const structure = `
        <div class="workout-structure">
            <h5>Workout Structure</h5>
            ${workout.sets.map(set => `
                <div class="interval-set">
                    ${set.repeat > 1 ? `<p class="set-header">Repeat ${set.repeat} times:</p>` : ''}
                    <ul class="interval-list">
                        ${set.intervals.map(interval => `
                            <li>
                                ${Math.floor(interval.duration / 60)}:${(interval.duration % 60)
                                    .toString().padStart(2, '0')} minutes: 
                                ${interval.activity}
                                ${interval.intensity ? ` - ${interval.intensity}` : ''}
                                ${interval.targetMetrics ? 
                                    `<br>Targets: ${formatMetrics(interval.targetMetrics)}` : 
                                    ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `).join('')}
        </div>`;

    // Generate form cues section
    const formCues = workout.formCues ? `
        <div class="form-cues">
            <h5>Form Cues</h5>
            <ul>
                ${workout.formCues.map(cue => `<li>${cue}</li>`).join('')}
            </ul>
        </div>` : '';

    // Generate notes section
    const notes = workout.notes ? `
        <div class="workout-notes">
            <h5>Important Notes</h5>
            <ul>
                ${workout.notes.map(note => `<li>${note}</li>`).join('')}
            </ul>
        </div>` : '';

    // Add timer button
    const timerButton = `
        <button class="start-timer-btn" onclick="startWorkoutTimer()">
            Start Timer
        </button>`;

    // Combine all sections
    return `
        ${header}
        ${structure}
        ${formCues}
        ${notes}
        ${timerButton}
    `;
}
