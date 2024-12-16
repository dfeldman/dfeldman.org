
function getSpecialNotes(level) {
    // Create groups of notes that make sense together
    const noteGroups = [
        // Absolute Beginner Notes (Levels 1-5)
        [
            "Your muscles' natural tension in the morning differs from evening - notice these patterns to understand your body's rhythms.",
            "A proper stretch feels like a gentle pulling sensation, never sharp pain. Think of slowly stretching a rubber band.",
            "The exhale phase of your breath naturally allows for slightly deeper stretches - try focusing on this connection."
        ],
        // Early Form Notes (Levels 6-10)
        [
            "Imagine creating length through your spine as you stretch - this helps maintain proper alignment.",
            "Your body may feel different each day. This natural variation is perfectly normal and guides how deeply to stretch.",
            "Focus on relaxing the muscles you're stretching - tension often comes from muscles trying to protect themselves."
        ],
        // Body Awareness Notes (Levels 11-15)
        [
            "Notice which side of your body feels tighter - this awareness helps prevent overcompensating.",
            "The sensation of a stretch should remain steady - if it lessens while holding, you can carefully deepen the position.",
            "Pay attention to your jaw and shoulders - we often hold tension here without realizing it."
        ],
        // Intermediate Foundation (Levels 16-20)
        [
            "Try to identify which specific muscles feel tight during each stretch - this body awareness aids progress.",
            "Quality of movement matters more than depth - focus on smooth, controlled transitions.",
            "Your flexibility naturally fluctuates throughout the day - morning stiffness is completely normal."
        ],
        // Intermediate Progress (Levels 21-30)
        [
            "Balanced flexibility requires both stretching and strengthening - the two work together.",
            "Notice how your breathing pattern affects the depth of your stretches.",
            "Rather than pushing harder, try relaxing deeper into each position."
        ],
        // Intermediate Mastery (Levels 31-40)
        [
            "Small adjustments in alignment can dramatically change which muscles you feel stretching.",
            "Consider how your daily activities affect your flexibility patterns.",
            "Focus on maintaining relaxed breathing even in challenging positions."
        ],
        // Advanced Foundation (Levels 41-60)
        [
            "Flexibility gains come from consistent practice, not from forcing extreme positions.",
            "Pay attention to the quality of the stretch sensation - sharp or burning feelings indicate too much intensity.",
            "Your nervous system needs time to adapt - patience leads to lasting progress."
        ],
        // Advanced Development (Levels 61-80)
        [
            "Notice how proper alignment allows for deeper stretches with less effort.",
            "Even at advanced levels, never force a stretch - control and awareness remain crucial.",
            "Regular gentle stretching often yields better results than occasional intense sessions."
        ],
        // Advanced Mastery (Levels 81-100)
        [
            "Maintain awareness of your entire body even while focusing on specific stretches.",
            "Your flexibility journey is unique - avoid comparing yourself to others.",
            "Listen to subtle feedback from your body - it guides optimal stretch intensity."
        ]
    ];

    // Determine which group of notes to use based on level
    let groupIndex = Math.floor((level - 1) / 5);
    groupIndex = Math.min(groupIndex, noteGroups.length - 1);

    // Within each group, rotate through different combinations of notes
    // based on level to keep the advice fresh
    const currentGroup = noteGroups[groupIndex];
    const rotationIndex = level % 3; // Cycle through different combinations

    // Select three notes using different rotation patterns
    let selectedNotes;
    switch (rotationIndex) {
        case 0:
            selectedNotes = [currentGroup[0], currentGroup[1], currentGroup[2]];
            break;
        case 1:
            selectedNotes = [currentGroup[2], currentGroup[0], currentGroup[1]];
            break;
        case 2:
            selectedNotes = [currentGroup[1], currentGroup[2], currentGroup[0]];
            break;
        default:
            selectedNotes = currentGroup.slice(0, 3);
    }

    return selectedNotes;
}

function generateFlexWorkout(level) {
    const workout = {
        title: level <= 20 ? 'Basic Flexibility Training' :
            level <= 50 ? 'Intermediate Stretching' :
                'Advanced Flexibility Work',
        description: "Hold each stretch until you feel a gentle pull - never stretch to the point of pain. Breathe slowly and deeply while stretching.",
        stretches: []
    };

    // Define the current goal based on level
    function getCurrentGoal(level) {
        const goals = [
            { level: 5, description: "Touch your knees while standing with straight legs" },
            { level: 10, description: "Touch your shins while standing with straight legs" },
            { level: 15, description: "Hold a toe touch with bent knees for 30 seconds" },
            { level: 20, description: "Touch your toes while standing with slightly bent knees" },
            { level: 30, description: "Touch your toes while standing with straight legs" },
            { level: 40, description: "Place palms flat on floor with bent knees" },
            { level: 50, description: "Hold a seated forward fold, touching toes, for 60 seconds" },
            { level: 60, description: "Place palms flat on floor with straight legs" },
            { level: 70, description: "Achieve a runner's lunge with back knee on ground" },
            { level: 80, description: "Hold a front split with support (blocks or cushions)" },
            { level: 90, description: "Achieve a full front split on one side" },
            { level: 100, description: "Achieve full front splits on both sides" }
        ];

        // Find the next goal to work toward
        let nextGoal = goals.find(goal => goal.level > level) || goals[goals.length - 1];
        let currentGoal = goals.find(goal => goal.level <= level);

        // For display purposes, show the last achieved goal and the next goal
        return {
            current: currentGoal ? currentGoal.description : goals[0].description,
            next: nextGoal.description,
            progress: currentGoal ? `Level ${currentGoal.level} goal achieved!` : "Working toward first goal"
        };
    }

    // Basic stretches that everyone starts with
    // Beginner level (1-20) with highly detailed progression and guidance
    if (level <= 20) {
        workout.stretches = [
            {
                name: "Standing Forward Reach",
                description: "Stand with feet hip-width apart. Keeping your legs mostly straight but not locked, slowly bend forward and reach down toward your feet. Only go as far as comfortable - you might only reach your thighs at first, and that's perfectly fine.",
                duration: level <= 5 ? "15 seconds" :
                    level <= 10 ? "20 seconds" : "30 seconds",
                target: "Back of legs (hamstrings) and lower back",
                goal: level <= 5 ? "Reach fingertips to mid-thigh while keeping back straight - focus on feeling a gentle stretch in the backs of your legs" :
                    level <= 8 ? "Reach fingertips past mid-thigh. Your back can round slightly, but you should still be able to breathe comfortably" :
                        level <= 12 ? "Touch your fingertips to your kneecaps. Try to keep your legs as straight as possible, but a slight bend is fine" :
                            level <= 15 ? "Reach your fingertips to the top of your shins. Notice how your breathing affects the stretch" :
                                level <= 18 ? "Touch your fingers to the middle of your shins. Focus on relaxing your neck and shoulders" :
                                    "Reach for your ankles. Remember - it's not about touching them yet, just reaching toward them with control"
            },
            {
                name: "Gentle Seated Twist",
                description: "Sit in a chair with feet flat on floor. Keep your back straight and shoulders relaxed. Slowly turn to look over one shoulder, using the chair back or your hands on your legs to help.",
                duration: level <= 7 ? "10 seconds each side" :
                    level <= 15 ? "15 seconds each side" :
                        "20 seconds each side",
                target: "Upper back and spine mobility",
                goal: level <= 5 ? "Turn just until you feel the first hint of stretch - notice where you feel it in your back" :
                    level <= 10 ? "Turn far enough to look past your shoulder, keeping your head level" :
                        level <= 15 ? "Turn far enough to see the wall behind you while keeping hips facing forward" :
                            "Turn far enough to grasp the chair back with both hands, keeping your spine tall"
            },
            {
                name: "Wall Calf Stretch",
                description: "Stand facing a wall, place hands flat on wall at shoulder height. Step one foot back and press heel down. Keep back leg straight but not locked. If this is too intense, bend your back leg slightly.",
                duration: level <= 8 ? "15 seconds each leg" :
                    level <= 15 ? "20 seconds each leg" :
                        "30 seconds each leg",
                target: "Lower leg muscles (calves)",
                goal: level <= 5 ? "Focus on feeling the stretch with your back heel just barely touching the ground" :
                    level <= 10 ? "Press your heel fully into the ground, even if you need to move closer to the wall" :
                        level <= 15 ? "Keep heel down while gradually moving foot farther from wall" :
                            "Hold with foot farther from wall while keeping heel flat and leg straight"
            },
            {
                name: "Assisted Knee Hug",
                description: "Lie on your back with legs extended. Bend one knee and bring it toward your chest, using your hands clasped behind your thigh to help. Keep your other leg straight on the ground.",
                duration: level <= 6 ? "15 seconds each leg" :
                    level <= 12 ? "20 seconds each leg" :
                        "30 seconds each leg",
                target: "Lower back and hip mobility",
                goal: level <= 4 ? "Lift knee enough to feel gentle stretch while keeping head and shoulders relaxed on floor" :
                    level <= 8 ? "Draw knee closer to chest while keeping other leg straight on ground" :
                        level <= 12 ? "Pull knee toward chest until thigh touches belly, if comfortable" :
                            level <= 16 ? "Keep lower back pressed against floor while hugging knee" :
                                "Hold knee to chest while completely relaxing hip muscles"
            },
            {
                name: "Shoulder Circles",
                description: "Stand or sit tall. Slowly roll shoulders forward, up, back, and down in a circular motion. Then reverse the direction. Keep the movements slow and controlled.",
                duration: level <= 10 ? "5 circles each direction" :
                    level <= 15 ? "8 circles each direction" :
                        "10 circles each direction",
                target: "Shoulder mobility and tension relief",
                goal: level <= 5 ? "Focus on making the circles as smooth as possible, even if they're small" :
                    level <= 10 ? "Make the circles larger while keeping shoulders relaxed" :
                        level <= 15 ? "Feel shoulder blades moving through their full range" :
                            "Make large circles while keeping neck relaxed and spine straight"
            }
        ];

    }

    // Intermediate level (21-50) now has more targeted goals
    else if (level <= 50) {
        workout.stretches = [
            {
                name: "Seated Forward Reach",
                description: "Sit on floor with legs straight out front. Keeping back straight, reach forward toward your toes. Let your head hang relaxed. Again, reaching your toes isn't necessary - go only as far as comfortable.",
                duration: "45 seconds",
                target: "Back of legs and lower back",
                goal: "Hold position without rounding your lower back"
            },
            {
                name: "Floor Twist",
                description: "Sit on floor with one leg straight, other leg bent with foot flat on floor outside opposite knee. Twist torso toward bent knee, using arm to help hold the twist. Keep back straight.",
                duration: "30 seconds each side",
                target: "Back and hips",
                goal: "Look completely behind you while keeping hips grounded"
            },
            {
                name: "Extended Kneeling Hip Stretch",
                description: "Kneel on one knee (put a cushion under knee if needed). Push hips forward slightly while keeping torso upright. For more stretch, raise arm on same side as back leg.",
                duration: "30 seconds each side",
                target: "Hip flexors, quads, and shoulders",
                goal: "Maintain upright posture without leaning forward"
            },
            {
                name: "Wide-Legged Seated Forward Fold",
                description: "Sit with legs spread wide. Keeping legs straight but not locked, walk hands forward between legs. Let head hang relaxed.",
                duration: "45 seconds",
                target: "Inner thighs and hamstrings",
                goal: level <= 35 ? "Keep back flat while reaching forward" :
                    level <= 45 ? "Touch elbows to ground" :
                        "Bring chest closer to ground"
            },
            {
                name: "Figure-Four Hip Stretch",
                description: "Lie on back, cross right ankle over left thigh. Thread hands behind left thigh and gently pull leg toward chest. Keep head and shoulders relaxed on floor.",
                duration: "40 seconds each side",
                target: "Deep hip muscles and glutes",
                goal: "Keep bottom foot flexed and hips relaxed"
            }
        ];
    }
    // Advanced level (51-100) with progressive goals
    else {
        workout.stretches = [
            {
                name: "Advanced Forward Fold",
                description: "Stand with feet hip-width apart. Bend forward, reaching for the ground. Bend knees only if needed for comfort.",
                duration: "60 seconds",
                target: "Entire back of body",
                goal: level <= 70 ? "Place full palms on floor beside feet" :
                    level <= 85 ? "Hold palms flat while straightening legs" :
                        "Bring forehead toward knees with straight legs"
            },
            {
                name: "Front Split Preparation",
                description: "Starting in a low lunge, gradually slide front leg forward and back leg back. Use yoga blocks or cushions under hands for support if needed.",
                duration: "60 seconds each side",
                target: "Hip flexors and hamstrings",
                goal: level <= 65 ? "Lower hips with both legs straight" :
                    level <= 80 ? "Get hips 6 inches from ground with support" :
                        level <= 90 ? "Achieve full split with light support" :
                            "Hold full split without support"
            },
            {
                name: "Middle Split Preparation",
                description: "Stand with feet wide, toes pointing forward. Gradually lower hips while sliding feet wider. Keep hands on floor in front for support.",
                duration: "45 seconds",
                target: "Inner thighs and hips",
                goal: level <= 60 ? "Keep pelvis tucked while lowering" :
                    level <= 75 ? "Thighs parallel to ground" :
                        level <= 85 ? "Hips 8 inches from ground" :
                            "Work toward full middle split"
            },
            {
                name: "Bridge Position",
                description: "Lie on back, bend knees with feet flat on floor. Press hips up, then bring hands by ears and press up into a backbend if comfortable.",
                duration: "45 seconds",
                target: "Spine, shoulders, and hip flexors",
                goal: level <= 70 ? "Lift hips with straight arms" :
                    level <= 85 ? "Straighten arms in bridge" :
                        "Work on walking hands closer to feet"
            },
            {
                name: "Advanced Hip Opener",
                description: "From seated position, bend knees and bring soles of feet together. Let knees fall out to sides. Slowly fold forward while keeping back straight.",
                duration: "60 seconds",
                target: "Inner thighs and hips",
                goal: level <= 65 ? "Keep back straight while folding" :
                    level <= 80 ? "Bring forehead toward feet" :
                        "Press knees closer to ground"
            }
        ];
    }

    workout.specialNotes = getSpecialNotes(level);
    const goal = getCurrentGoal(level);

    workout.html = `
<div class="workout-header">
    <h4>${workout.title}</h4>
    <p class="workout-intro">${workout.description}</p>
</div>

<div class="exercise-card goal-card">
    <h5>Your Flexibility Journey</h5>
    <div class="goal-progress">
        <div class="current-goal">
            <span class="goal-label">Current Achievement:</span>
            <span class="goal-text">${goal.current}</span>
        </div>
        <div class="next-goal">
            <span class="goal-label">Working Toward:</span>
            <span class="goal-text">${goal.next}</span>
        </div>
        <div class="progress-marker">
            <span class="progress-text">${goal.progress}</span>
        </div>
    </div>
</div>


${workout.specialNotes ? `
<div class="exercise-card special-notes">
    <h5>Today's Focus Points</h5>
    <ul class="notes-list">
        ${workout.specialNotes.map(note => `
            <li class="note-item">${note}</li>
        `).join('')}
    </ul>
</div>
` : ''}

${workout.stretches.map(stretch => `
    <div class="exercise-card stretch-card">
        <h5>${stretch.name}</h5>
        <div class="stretch-description">
            <p>${stretch.description}</p>
        </div>
        <div class="stretch-details">
            <p class="target-area">Target Area: ${stretch.target}</p>
            <p class="duration">Hold for: ${stretch.duration}</p>
            ${stretch.goal ? `<p class="stretch-goal">Today's Goal: ${stretch.goal}</p>` : ''}
        </div>
    </div>
`).join('')}


<div class="workout-notes">
    <h5>Important Reminders</h5>
    <ul>
        <li>Never bounce or force a stretch</li>
        <li>Stretch only to the point of mild tension, never pain</li>
        <li>Breathe slowly and steadily throughout each stretch</li>
        <li>If you have any injuries or medical conditions, consult your doctor first</li>
    </ul>
</div>`;

    return workout;
}