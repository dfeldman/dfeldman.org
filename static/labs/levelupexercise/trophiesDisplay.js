function updateTrophiesDisplay() {
    const content = document.getElementById('trophies');
    const existingHeader = content.querySelector('.timer-header');
    
    // Clear content but preserve the header
    content.innerHTML = '';
    content.appendChild(existingHeader);

    // Add placeholder content using the new style
    const html = `
        <div class="card">
            <div class="card__header">Recent Achievements</div>
            <div class="card__content">
                <div class="exercise-item">
                    <div class="exercise-item__emoji">🌟</div>
                    <div class="exercise-item__content">
                        <div class="exercise-item__title">First Mile</div>
                        <div class="exercise-item__subtitle">Complete your first mile run</div>
                    </div>
                </div>
                <div class="exercise-item">
                    <div class="exercise-item__emoji">💪</div>
                    <div class="exercise-item__content">
                        <div class="exercise-item__title">Strength Master</div>
                        <div class="exercise-item__subtitle">Complete 10 strength workouts</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card__header">Progress Milestones</div>
            <div class="card__content">
                <div class="exercise-item">
                    <div class="exercise-item__emoji">🎯</div>
                    <div class="exercise-item__content">
                        <div class="exercise-item__title">5K Training</div>
                        <div class="exercise-item__subtitle">Progress: 2/10 runs completed</div>
                        <div class="progress-item">
                            <div class="progress-item__bar">
                                <div class="progress">
                                    <div class="progress__bar" style="width: 20%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    content.insertAdjacentHTML('beforeend', html);
}
