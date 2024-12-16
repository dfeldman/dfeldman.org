// Base configurations for rowing workouts
const ROW_CONFIGS = {
    beginner: {
        type: "technique",
        levelRange: [1, 10],
        time: level => 15 + Math.floor((level - 1) * 0.5) * 5,
        baseSPM: 18,
        spmIncrease: 0.5,
        activeMinutes: level => Math.min(3, 1 + Math.floor((level - 1) / 2)),
        restMinutes: level => Math.max(1, 3 - Math.floor((level - 1) / 3))
    },
    
    intervals: {
        type: "power",
        levelRange: [11, 20],
        basePace: 180,  // 3:00/500m
        paceImprovement: 3,
        baseSPM: 20,
        spmIncrease: 0.5,
        activeMinutes: level => Math.floor(2 + (level - 11) / 2),
        restSeconds: level => Math.max(60, 120 - (level - 11) * 6)
    },
    
    endurance: {
        type: "endurance",
        phases: {
            build: {
                levelRange: [21, 30],
                time: 30,
                basePace: 150,
                paceReduction: 3,
                baseSPM: 22,
                spmIncrease: 0.5,
                calories: '250-500'
            },
            endurance: {
                levelRange: [31, 70],
                time: 45,
                basePace: 120,
                paceReduction: 0.25,
                baseSPM: 24,
                spmIncrease: 0.2,
                calories: '350-700'
            },
            long: {
                levelRange: [71, 100],
                time: 60,
                basePace: 105,
                paceReduction: 0.33,
                baseSPM: 26,
                spmIncrease: 0.15,
                calories: '450-900'
            }
        }
    }
};

function generateRowWorkout(level) {
    const workout = {
        type: 'row',
        level: level
    };

    // Add form cues that apply to all rowing workouts
    workout.formCues = [
        'Drive: legs-back-arms, Recovery: arms-back-legs',
        'Keep arms straight during the initial drive',
        'Core engaged throughout the stroke',
        'Control the recovery phase - it should take twice as long as the drive',
        'Keep shoulders relaxed and low'
    ];

    if (level <= 10) {
        // Beginner phase - technique focus
        const config = ROW_CONFIGS.beginner;
        workout.phase = 'technique';
        workout.description = 'Rowing Technique Foundation';
        workout.spm = config.baseSPM + Math.floor((level - 1) * config.spmIncrease);
        
        const activeMinutes = config.activeMinutes(level);
        const restMinutes = config.restMinutes(level);
        const totalRounds = Math.floor(config.time(level) / (activeMinutes + restMinutes));

        workout.notes = [
            'Focus on perfect form over power',
            'Watch the force curve on the monitor',
            'Quick catch, patient finish',
            'Take extra rest if form deteriorates',
            `Target ${workout.spm} strokes per minute`
        ];

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Technique Warm-up",
                    duration: 180,
                    intensity: "Light effort, focus on form",
                    targetMetrics: {
                        spm: workout.spm - 2
                    }
                }]
            },
            {
                repeat: totalRounds,
                intervals: [
                    {
                        activity: "Technical Row",
                        duration: activeMinutes * 60,
                        intensity: "Focus on form",
                        targetMetrics: {
                            spm: workout.spm
                        }
                    },
                    {
                        activity: "Rest and Reset",
                        duration: restMinutes * 60,
                        intensity: "Full recovery",
                        description: "Stand up, stretch, reset posture"
                    }
                ]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    duration: 120,
                    intensity: "Very light",
                    targetMetrics: {
                        spm: workout.spm - 2
                    }
                }]
            }
        ];
        workout.totalDuration = config.time(level) * 60;
    }
    else if (level <= 20) {
        // Interval phase
        const config = ROW_CONFIGS.intervals;
        workout.phase = 'intervals';
        workout.description = 'Power Development Intervals';
        
        // Calculate targets
        workout.pace = Math.max(150, config.basePace - (level - 11) * config.paceImprovement);
        workout.spm = config.baseSPM + Math.floor((level - 11) * config.spmIncrease);
        const activeMinutes = config.activeMinutes(level);
        const restSeconds = config.restSeconds(level);
        const totalRounds = 4;  // Fixed number of rounds for consistency

        workout.notes = [
            'Focus on power application during drive',
            'Use rest periods for light stretching',
            'Monitor split time consistency',
            'Quick catch, powerful drive',
            `Target ${workout.spm} SPM during work intervals`
        ];

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up",
                    duration: 300,
                    intensity: "Progressive build",
                    targetMetrics: {
                        spm: workout.spm - 2,
                        split: workout.pace + 20
                    }
                }]
            },
            {
                repeat: totalRounds,
                intervals: [
                    {
                        activity: "Power Interval",
                        duration: activeMinutes * 60,
                        intensity: "Strong effort",
                        targetMetrics: {
                            spm: workout.spm,
                            split: workout.pace
                        }
                    },
                    {
                        activity: "Active Recovery",
                        duration: restSeconds,
                        intensity: "Light rowing",
                        targetMetrics: {
                            spm: workout.spm - 4,
                            split: workout.pace + 30
                        }
                    }
                ]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down",
                    duration: 300,
                    intensity: "Easy effort",
                    targetMetrics: {
                        spm: workout.spm - 4,
                        split: workout.pace + 30
                    }
                }]
            }
        ];
        workout.totalDuration = 300 + totalRounds * (activeMinutes * 60 + restSeconds) + 300;
    }
    else {
        // Find appropriate endurance phase
        const phase = Object.entries(ROW_CONFIGS.endurance.phases)
            .find(([_, config]) => 
                level >= config.levelRange[0] && level <= config.levelRange[1]
            )[1];

        const levelOffset = phase.levelRange[0] - 1;
        const baseSplit = phase.basePace - Math.floor((level - phase.levelRange[0]) * phase.paceReduction);
        const hardSplit = Math.max(baseSplit - 10, baseSplit * 0.9);
        const easySplit = baseSplit + 15;
        const targetSPM = Math.min(32, Math.floor(phase.baseSPM + 
            (level - phase.levelRange[0]) * phase.spmIncrease));

        workout.phase = 'endurance';
        workout.description = workout.phase === 'long' ? 'Long Distance Row' : 'Endurance Development';
        workout.spm = targetSPM;
        workout.calories = phase.calories;

        workout.notes = [
            `Maintain ${targetSPM} SPM during main sets`,
            'Focus on efficiency at higher rates',
            'Stay relaxed through the upper body',
            'Monitor heart rate and adjust intensity if needed',
            'Consistent power application'
        ];

        // Different structures based on phase type
        if (phase.levelRange[0] <= 30) {  // Build phase
            workout.sets = [
                {
                    repeat: 1,
                    intervals: [{
                        activity: "Warm-up",
                        duration: 300,
                        intensity: "Progressive build",
                        targetMetrics: {
                            spm: targetSPM - 2,
                            split: easySplit
                        }
                    }]
                },
                {
                    repeat: 1,
                    intervals: [{
                        activity: "Main Set",
                        duration: (phase.time - 10) * 60,
                        intensity: "Steady effort",
                        targetMetrics: {
                            spm: targetSPM,
                            split: baseSplit
                        }
                    }]
                },
                {
                    repeat: 1,
                    intervals: [{
                        activity: "Cool-down",
                        duration: 300,
                        intensity: "Easy effort",
                        targetMetrics: {
                            spm: targetSPM - 2,
                            split: easySplit
                        }
                    }]
                }
            ];
        } else {  // Endurance and long phases
            const mainSetDuration = 600;  // 10 minutes
            const hardSetDuration = phase.levelRange[0] <= 70 ? 300 : 180;  // 5 or 3 minutes
            const sets = phase.levelRange[0] <= 70 ? 3 : 4;  // 3 or 4 sets

            workout.sets = [
                {
                    repeat: 1,
                    intervals: [{
                        activity: "Warm-up",
                        duration: 300,
                        intensity: "Progressive build",
                        targetMetrics: {
                            spm: targetSPM - 2,
                            split: easySplit
                        }
                    }]
                },
                {
                    repeat: sets,
                    intervals: [{
                        activity: "Steady State",
                        duration: mainSetDuration,
                        intensity: "Moderate effort",
                        targetMetrics: {
                            spm: targetSPM,
                            split: baseSplit
                        }
                    }]
                },
                {
                    repeat: sets - 1,
                    intervals: [
                        {
                            activity: "Power Piece",
                            duration: hardSetDuration,
                            intensity: "Hard effort",
                            targetMetrics: {
                                spm: targetSPM + 2,
                                split: hardSplit
                            }
                        },
                        {
                            activity: "Recovery",
                            duration: 60,
                            intensity: "Very light",
                            targetMetrics: {
                                spm: targetSPM - 4,
                                split: easySplit + 10
                            }
                        }
                    ]
                },
                {
                    repeat: 1,
                    intervals: [{
                        activity: "Cool-down",
                        duration: 300,
                        intensity: "Easy effort",
                        targetMetrics: {
                            spm: targetSPM - 2,
                            split: easySplit
                        }
                    }]
                }
            ];
        }
        workout.totalDuration = phase.time * 60;
    }

    // Generate HTML display
    workout.html = generateRowHTML(workout);
    
    return workout;
}

function generateRowHTML(workout) {
    // Helper function to format rowing-specific metrics
    function formatMetrics(metrics) {
        if (!metrics) return '';
        
        const parts = [];
        if (metrics.split) {
            const minutes = Math.floor(metrics.split / 60);
            const seconds = metrics.split % 60;
            parts.push(`${minutes}:${seconds.toString().padStart(2, '0')}/500m`);
        }
        if (metrics.spm) {
            if (typeof metrics.spm === 'string') {
                parts.push(`${metrics.spm} SPM`);  // For ranges like "22-24 SPM"
            } else {
                parts.push(`${metrics.spm} SPM`);
            }
        }
        
        return parts.join(' / ');
    }

    // Generate header section with workout basics
    const header = `
        <div class="workout-header">
            <h4>${workout.description}</h4>
            <div class="metrics-grid">
                <div class="metric">
                    <span class="metric-label">Total Time</span>
                    <span class="metric-value">${Math.round(workout.totalDuration / 60)} minutes</span>
                </div>
                ${workout.distance ? `
                    <div class="metric">
                        <span class="metric-label">Target Distance</span>
                        <span class="metric-value">${workout.distance}m</span>
                    </div>
                ` : ''}
                ${workout.spm ? `
                    <div class="metric">
                        <span class="metric-label">Target SPM</span>
                        <span class="metric-value">${workout.spm} strokes/min</span>
                    </div>
                ` : ''}
                ${workout.pace ? `
                    <div class="metric">
                        <span class="metric-label">Target Split</span>
                        <span class="metric-value">${Math.floor(workout.pace / 60)}:${(workout.pace % 60).toString().padStart(2, '0')}/500m</span>
                    </div>
                ` : ''}
            </div>
        </div>`;

    // Generate workout structure section
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
                                ${interval.targetMetrics ? `
                                    <br><span class="target-metrics">Targets: ${formatMetrics(interval.targetMetrics)}</span>
                                ` : ''}
                                ${interval.description ? `<br><span class="description">${interval.description}</span>` : ''}
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

    // Add calories if available
    const calories = workout.calories ? `
        <div class="calorie-estimate">
            <span class="label">Estimated Calories:</span>
            <span class="value">${workout.calories}</span>
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
        ${calories}
        ${timerButton}
    `;
}
