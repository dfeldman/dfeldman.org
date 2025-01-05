function updateWorkoutsList() {
    const content = document.getElementById('workouts');
    const existingHeader = content.querySelector('.timer-header');
    
    // Clear content but preserve the header
    content.innerHTML = '';
    content.appendChild(existingHeader);

    // Create our quest selection interface
    const html = `
        <div class="quest-category">
            <div class="quest-header">Cardio Quests</div>
            <div class="quest-grid">
                <div class="quest-item" onclick="selectWorkout('run')">
                    <div class="quest-item__emoji">🏃‍♂️</div>
                    <div class="quest-item__title">Running</div>
                    <div class="quest-item__subtitle">All levels welcome</div>
                    <div class="quest-item__badge">Popular</div>
                </div>
                <div class="quest-item" onclick="selectWorkout('bike')">
                    <div class="quest-item__emoji">🚴‍♂️</div>
                    <div class="quest-item__title">Biking</div>
                    <div class="quest-item__subtitle">Road & trail</div>
                </div>
                <div class="quest-item" onclick="selectWorkout('row')">
                    <div class="quest-item__emoji">🚣‍♂️</div>
                    <div class="quest-item__title">Rowing</div>
                    <div class="quest-item__subtitle">Full body cardio</div>
                </div>
                <div class="quest-item" onclick="selectWorkout('swim')">
                    <div class="quest-item__emoji">🏊‍♂️</div>
                    <div class="quest-item__title">Swimming</div>
                    <div class="quest-item__subtitle">Pool workouts</div>
                </div>
            </div>
        </div>

        <div class="quest-category">
            <div class="quest-header">Strength Quests</div>
            <div class="quest-grid">
                <div class="quest-item" onclick="selectWorkout('strength')">
                    <div class="quest-item__emoji">💪</div>
                    <div class="quest-item__title">Weight Machines</div>
                    <div class="quest-item__subtitle">Guided progression</div>
                </div>
                <div class="quest-item quest-item--soon">
                    <div class="quest-item__emoji">🏋️‍♂️</div>
                    <div class="quest-item__title">Free Weights</div>
                    <div class="quest-item__subtitle">Coming soon</div>
                </div>
            </div>
        </div>

        <div class="quest-category">
            <div class="quest-header">Flexibility Quests</div>
            <div class="quest-grid">
                <div class="quest-item" onclick="selectWorkout('flexibility')">
                    <div class="quest-item__emoji">🧘‍♂️</div>
                    <div class="quest-item__title">Basic Flexibility</div>
                    <div class="quest-item__subtitle">Start your journey</div>
                </div>
                <div class="quest-item quest-item--soon">
                    <div class="quest-item__emoji">🤸‍♂️</div>
                    <div class="quest-item__title">Advanced Moves</div>
                    <div class="quest-item__subtitle">Coming soon</div>
                </div>
            </div>
        </div>
    `;
    
    content.insertAdjacentHTML('beforeend', html);
}

// Handle workout selection and tab switching
function selectWorkout(type) {
    // First switch to the overview tab
    switchTab('overview');
    
    // Then select the workout type
    switchCardio(type);
    
    // Add a small delay before the animation starts
    setTimeout(() => {
        // Find and flash the selected workout type in the overview tab
        const selectedBox = Array.from(document.querySelectorAll('.stats-grid .stat-box'))
            .find(box => box.querySelector('.stat-box__label')
                .textContent.toLowerCase() === type);
        
        if (selectedBox) {
            selectedBox.style.transform = 'scale(1.1)';
            setTimeout(() => {
                selectedBox.style.transform = '';
            }, 200);
        }
    }, 100);
}