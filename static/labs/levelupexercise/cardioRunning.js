// Base configurations for different running phases
const RUN_CONFIGS = {
    beginner: {
        type: "walk",
        levelRange: [1, 10],
        baseTime: 30,
        baseSpeed: 2.5,
        speedIncrease: 0.1,
        structure: level => ({
            warmup: 300,  // 5 minutes
            main: 1200,   // 20 minutes
            cooldown: 300 // 5 minutes
        })
    },
    
    walkRun: {
        type: "intervals",
        levelRange: [11, 20],
        patterns: [
            { run: 30, walk: 120, sets: 6 },   // Level 11
            { run: 30, walk: 90, sets: 7 },    // Level 12
            { run: 45, walk: 90, sets: 6 },    // Level 13
            { run: 60, walk: 90, sets: 6 },    // Level 14
            { run: 60, walk: 60, sets: 7 },    // Level 15
            { run: 90, walk: 60, sets: 5 },    // Level 16
            { run: 120, walk: 60, sets: 4 },   // Level 17
            { run: 180, walk: 60, sets: 3 },   // Level 18
            { run: 300, walk: 120, sets: 2 },  // Level 19
            { run: 480, walk: 120, sets: 1 }   // Level 20
        ]
    },
    
    continuous: {
        type: "continuous",
        phases: {
            build: {
                levelRange: [21, 30],
                time: 30,
                startPace: 12,
                paceReduction: 0.2,
                calories: '250-450'
            },
            endurance: {
                levelRange: [31, 70],
                time: 45,
                startPace: 10,
                paceReduction: 0.025,
                calories: '400-800'
            },
            long: {
                levelRange: [71, 100],
                time: 60,
                startPace: 9,
                paceReduction: 0.033,
                calories: '600-1200'
            }
        }
    }
};

function generateRunHTML(workout) {
    // Helper function for formatting metrics
    function formatMetric(value, type) {
        if (type === 'pace') {
            const minutes = Math.floor(value);
            const seconds = Math.round((value - minutes) * 60);
            return `${minutes}:${seconds.toString().padStart(2, '0')}/mile (${(60 / value).toFixed(1)} mph)`;
        }
        return value;
    }

    // Generate header section with workout basics
    const header = `
        <div class="workout-header">
            <h4>${workout.phase === 'basic' ? 'Walking Workout' :
                 workout.phase === 'intervals' ? 'Run/Walk Intervals' :
                 workout.phase === 'continuous' ? 'Continuous Run' : 'Running Workout'}</h4>
            <div class="metrics-grid">
                ${workout.totalDuration ? `
                    <div class="metric">
                        <span class="metric-label">Total Time</span>
                        <span class="metric-value">${Math.round(workout.totalDuration / 60)} minutes</span>
                    </div>
                ` : ''}
                ${workout.distance ? `
                    <div class="metric">
                        <span class="metric-label">Distance</span>
                        <span class="metric-value">${workout.distance} miles</span>
                    </div>
                ` : ''}
                ${workout.pace ? `
                    <div class="metric">
                        <span class="metric-label">Target Pace</span>
                        <span class="metric-value">${formatMetric(workout.pace, 'pace')}</span>
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
                                ${interval.duration ? 
                                    `${Math.floor(interval.duration / 60)}:${(interval.duration % 60)
                                        .toString().padStart(2, '0')} minutes: ` : 
                                    ''}
                                ${interval.activity}
                                ${interval.intensity ? ` - ${interval.intensity}` : ''}
                                ${interval.targetPace ? 
                                    ` at ${formatMetric(interval.targetPace, 'pace')}` : 
                                    ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `).join('')}
        </div>`;

    // Generate form cues section if they exist
    const formCues = workout.formCues ? `
        <div class="form-cues">
            <h5>Form Cues</h5>
            <ul>
                ${workout.formCues.map(cue => `<li>${cue}</li>`).join('')}
            </ul>
        </div>` : '';

    // Generate notes section if they exist
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

function generateRunWorkout(level, workout) {
    if (level <= 10) {
        // Basic walking phase
        const baseSpeed = 2.5 + (level - 1) * 0.1;
        const pace = 60 / baseSpeed;
        
        workout.totalDuration = 1800;  // 30 minutes
        workout.distance = +(workout.time * baseSpeed / 60).toFixed(2);
        workout.pace = pace;
        workout.phase = 'basic';
        workout.formCues = [
            'Stand tall with shoulders relaxed',
            'Look ahead, not down',
            'Arms swing naturally at your sides',
            'Push off with your toes',
            'Land heel-to-toe'
        ];
        workout.notes = [
            'Focus on maintaining good posture throughout',
            'Breathe naturally and steadily',
            'Start slow and build up speed gradually',
            'Stay well hydrated during your walk'
        ];

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up Walk",
                    duration: 300,
                    intensity: "Easy pace to warm up",
                    targetPace: pace + 1
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Brisk Walk",
                    duration: 1200,
                    intensity: "Steady, brisk pace",
                    targetPace: pace
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down Walk",
                    duration: 300,
                    intensity: "Easy pace",
                    targetPace: pace + 1
                }]
            }
        ];
    } 
    else if (level <= 20) {
        // Run/Walk Intervals phase
        const runPace = 12 - (level - 10) * 0.2;  // Starts at 12:00/mile, improves by 0.2 min/mile per level
        workout.phase = 'intervals';
        workout.formCues = [
            'Keep your head level and look forward',
            'Land midfoot, not heel',
            'Elbows at 90 degrees',
            'Hands relaxed, not clenched',
            'Shoulders relaxed and down'
        ];
        workout.notes = [
            'Maintain conversational pace during run intervals',
            'Use walk intervals for active recovery',
            'Focus on breathing rhythm',
            'Stay relaxed even when tired',
            'It\'s okay to extend walk intervals if needed'
        ];

        const pattern = RUN_CONFIGS.walkRun.patterns[level - 11];
        workout.totalDuration = pattern.sets * (pattern.run + pattern.walk) + 600; // Including warm-up/cool-down
        workout.estimatedDistance = +(workout.totalDuration / 60 * (1/runPace)).toFixed(2);
        workout.targetRunPace = runPace;

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up Walk",
                    duration: 300,
                    intensity: "Easy pace",
                    targetPace: 18  // 18:00/mile pace for warm-up
                }]
            },
            {
                repeat: pattern.sets,
                intervals: [
                    {
                        activity: "Run",
                        duration: pattern.run,
                        intensity: "Conversational pace",
                        targetPace: runPace
                    },
                    {
                        activity: "Walk",
                        duration: pattern.walk,
                        intensity: "Recovery",
                        targetPace: 16  // 16:00/mile pace for walking
                    }
                ]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down Walk",
                    duration: 300,
                    intensity: "Easy pace",
                    targetPace: 18
                }]
            }
        ];
    } 
    else {
        // Continuous running phases
        const phase = Object.entries(RUN_CONFIGS.continuous.phases)
            .find(([_, config]) => 
                level >= config.levelRange[0] && level <= config.levelRange[1]
            )[1];
        
        const targetPace = phase.startPace - (level - phase.levelRange[0]) * phase.paceReduction;
        
        workout.phase = 'continuous';
        workout.totalDuration = phase.time * 60;  // Convert minutes to seconds
        workout.targetPace = targetPace;
        workout.estimatedDistance = +(phase.time / targetPace).toFixed(2);
        workout.formCues = [
            'Maintain steady arm swing',
            'Keep cadence quick and light',
            'Stay tall with slight forward lean',
            'Breathe rhythmically',
            'Relax shoulders and hands'
        ];
        
        const phaseSpecificNotes = workout.phase === 'long' ? [
            'Take walking breaks if needed',
            'Focus on steady effort, not pace',
            'Stay well hydrated throughout',
            'Consider fueling during run',
            'Maintain form even when tired'
        ] : [
            'Maintain steady effort throughout',
            'Focus on consistent pacing',
            'Stay relaxed as you fatigue',
            'Keep breathing controlled',
            'Monitor your effort level'
        ];

        workout.notes = phaseSpecificNotes;

        workout.sets = [
            {
                repeat: 1,
                intervals: [{
                    activity: "Warm-up Walk/Jog",
                    duration: 600,  // 10 minute warm-up
                    intensity: "Easy pace building to light jog",
                    targetPace: targetPace + 2
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Main Run",
                    duration: (phase.time - 15) * 60,  // Main portion minus warm-up/cooldown
                    intensity: "Steady pace",
                    targetPace: targetPace
                }]
            },
            {
                repeat: 1,
                intervals: [{
                    activity: "Cool-down Walk",
                    duration: 300,
                    intensity: "Easy pace",
                    targetPace: targetPace + 2
                }]
            }
        ];
    }

    workout.html = generateRunHTML(workout);
    return workout;
}