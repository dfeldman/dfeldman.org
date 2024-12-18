class WorkoutRating {
    constructor() {
        // Create modal container
        this.modal = document.createElement('div');
        this.modal.className = 'rating-modal';
        
        // Create modal content
        this.modal.innerHTML = `
            <div class="rating-bold-gradient">
                <h2>How was your workout?</h2>
                <div class="gradient-options">
                    <div class="gradient-option" data-rating="easy">
                        <div class="emoji">😊</div>
                        <div class="rating-label">Easy</div>
                    </div>
                    <div class="gradient-option" data-rating="medium">
                        <div class="emoji">💪</div>
                        <div class="rating-label">Medium</div>
                    </div>
                    <div class="gradient-option" data-rating="hard">
                        <div class="emoji">🥵</div>
                        <div class="rating-label">Hard</div>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners
        this.modal.querySelectorAll('.gradient-option').forEach(option => {
            option.addEventListener('click', () => this.handleRating(option.dataset.rating));
        });
    }

    show() {
        document.body.appendChild(this.modal);
    }

    handleRating(rating) {
        // TODO: Store the rating
        console.log('Workout rated as:', rating);
        userData.recordWorkout({
            activity: currentWorkout.type,
            level: currentWorkout.level,
            duration: currentWorkout.totalDuration,
            difficulty: rating,
            timestamp: new Date().toISOString()
        });
        // Hide rating screen and return to main view
        this.modal.remove();
        document.querySelector('.container').style.display = 'block';
    }
}

function markWorkoutCompleted() {
    const ratingModal = new WorkoutRating();
    ratingModal.show();
}