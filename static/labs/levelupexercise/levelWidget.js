// Class to manage the level widget functionality
class LevelWidget {
    constructor(container, activityType) {
        this.container = container;
        this.activityType = activityType;
        this.isSliderVisible = false;
        this.workoutsNeededToLevelUp = 3; // Constant for now
        
        // Create the widget elements
        this.createWidget();
        this.attachEventListeners();
        this.render();
    }

    // Dummy functions to be implemented
    getCurrentLevel() {
        // TODO: Implement this to get level from userData
        return userData.getLevel(this.activityType);
    }

    getWorkoutsAtCurrentLevel() {
        return userData.getWorkoutsAtCurrentLevel(this.activityType);
    }

    canLevelUp() {
        return this.getWorkoutsAtCurrentLevel() >= this.workoutsNeededToLevelUp;
    }

    createWidget() {
        this.element = this.container;
        this.element.className = 'level-widget fun-widget';
        console.log("SLIDER", this.isSliderVisible);
        console.log("Current level: " + this.getCurrentLevel());
        console.log(this.getWorkoutsAtCurrentLevel());
        this.element.innerHTML = `
            <div class="content">
                <div class="level-circle">${this.getCurrentLevel()}</div>
                <div class="progress-container">
                    <div class="progress-text"></div>
                    <div class="progress-dots">
                        ${Array(this.workoutsNeededToLevelUp).fill(0).map(() => 
                            `<div class="dot"></div>`
                        ).join('')}
                    </div>
                </div>
                <button class="more-btn">•••</button>
            </div>
            <div class="level-slider-panel" style="display: none">
                <div class="slider-controls">
                    <button class="level-btn">-</button>
                    <input type="range" min="1" max="100" value="${this.getCurrentLevel()}">
                    <button class="level-btn">+</button>
                </div>
            </div>
        `;

        // Add to container
        //this.container.appendChild(this.element);

        // Store references to elements we'll need to update
        this.levelCircle = this.element.querySelector('.level-circle');
        this.progressText = this.element.querySelector('.progress-text');
        this.dots = this.element.querySelectorAll('.dot');
        this.sliderPanel = this.element.querySelector('.level-slider-panel');
        this.slider = this.element.querySelector('input[type="range"]');
    }

    attachEventListeners() {
        // More button toggles slider
        this.element.querySelector('.more-btn').addEventListener('click', () => {
            this.toggleSlider();
        });

        // Level adjustment buttons
        const decrementBtn = this.element.querySelector('.level-btn:first-child');
        const incrementBtn = this.element.querySelector('.level-btn:last-child');

        decrementBtn.textContent = '-';
        incrementBtn.textContent = '+';

        decrementBtn.addEventListener('click', () => this.adjustLevel(-1));
        incrementBtn.addEventListener('click', () => this.adjustLevel(1));

        // Slider change
        this.slider.addEventListener('input', (e) => {
            this.setLevel(parseInt(e.target.value));
        });

        // Level up functionality when clicking level circle
        this.levelCircle.addEventListener('click', () => {
            if (this.canLevelUp()) {
                this.levelUp();
            }
        });
    }

    toggleSlider() {
        this.isSliderVisible = !this.isSliderVisible;
        this.sliderPanel.style.display = this.isSliderVisible ? 'block' : 'none';
    }

    adjustLevel(delta) {
        const currentLevel = this.getCurrentLevel();
        const newLevel = Math.max(1, Math.min(100, currentLevel + delta));
        this.setLevel(newLevel);
    }

    setLevel(level) {
        // TODO: Implement this to update level in userData
        console.log(`Setting level to ${level}`);
        userData.setLevel(this.activityType, level);
        this.render();
    }

    levelUp() {
        if (!this.canLevelUp()) return;
        
        // TODO: Implement level up logic
        const nextLevel = this.getCurrentLevel() + 1;
        this.setLevel(nextLevel);
        
        // Create celebration effect
        this.celebrate();
    }

    celebrate() {
        const rect = this.levelCircle.getBoundingClientRect();
        this.createCelebration(rect.left + rect.width/2, rect.top + rect.height/2);
    }

    createCelebration(x, y) {
        const emoji = document.createElement('div');
        emoji.className = 'celebration-emoji';
        emoji.textContent = '🎉';
        emoji.style.left = `${x}px`;
        emoji.style.top = `${y}px`;
        document.body.appendChild(emoji);
        
        emoji.addEventListener('animationend', () => {
            emoji.remove();
        });
    }

    render() {
        const currentLevel = this.getCurrentLevel();
        const workoutsCompleted = this.getWorkoutsAtCurrentLevel();
        const workoutsRemaining = this.workoutsNeededToLevelUp - workoutsCompleted;
    
        // Debug logging
        console.log('Rendering level widget:', {
            currentLevel,
            workoutsCompleted,
            workoutsRemaining
        });
    
        // Update level display
        if (this.levelCircle) {
            this.levelCircle.textContent = currentLevel;
        }
    
        // Update progress text
        if (this.progressText) {
            if (this.canLevelUp()) {
                this.progressText.textContent = 'Ready to Level Up! 🎉';
                this.element.classList.add('can-level-up');
            } else {
                this.progressText.textContent = `${workoutsRemaining} more workout${workoutsRemaining !== 1 ? 's' : ''} to level up!`;
                this.element.classList.remove('can-level-up');
            }
        }
    
        // Update dots
        if (this.dots) {
            this.dots.forEach((dot, index) => {
                dot.classList.toggle('filled', index < workoutsCompleted);
            });
        }
    
        // Update slider value
        if (this.slider) {
            this.slider.value = currentLevel;
        }
    }
}