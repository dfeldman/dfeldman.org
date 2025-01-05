class WorkoutDisplay {
  constructor(targetElement, workout, options = {}) {
    this.target = targetElement;
    this.workout = workout;
    this.options = {
      unitSystem: options.unitSystem || "imperial",
      ...options,
    };
  }

  validateWorkout() {
    const required = ["type", "level", "description", "totalDuration", "sets"];
    const missing = required.filter((prop) => !currentWorkout[prop]);

    if (missing.length > 0) {
      console.error("Missing required workout properties:", missing);
      return false;
    }

    if (!Array.isArray(this.workout.sets)) {
      console.error("Workout sets must be an array");
      return false;
    }

    return true;
  }

  renderMetricPill(metric) {
    return `<div class="stat-box">
      <div class="stat-box__label">${metric.label}</div>
      <div class="stat-box__value">${metric.value}</div>
    </div>`;
  }

  renderInterval(interval) {
    return `<div class="exercise-item">
      <div class="exercise-item__emoji">🏃‍♂️</div>
      <div class="exercise-item__content">
        <div class="exercise-item__title">${interval.activity}</div>
        ${
          interval.intensity
            ? `<div class="exercise-item__subtitle">${interval.intensity}</div>`
            : ""
        }
        <div class="progress-item">
          <div class="progress-item__bar">
            <div class="progress">
              <div class="progress__bar" style="width: 100%"></div>
            </div>
            <div class="progress__label">
              ${this.formatMetrics(interval)}
            </div>
          </div>
        </div>
      </div>
    </div>`;
  }

  formatMetrics(interval) {
    const metrics = [];

    if (interval.duration) {
      metrics.push(`${this.formatTime(interval.duration)}`);
    }
    if (interval.distance) {
      metrics.push(`${this.formatDistance(interval.distance)} miles`);
    }
    if (interval.pace) {
      metrics.push(`${this.formatPace(interval.pace)}/mile`);
    }
    if (interval.reps) {
      metrics.push(`${interval.reps} reps`);
    }
    if (interval.weight) {
      metrics.push(`${interval.weight} lbs`);
    }

    return metrics.join(" • ");
  }

  renderSet(set, index) {
    const setContent = set.intervals
      .map((interval) => this.renderInterval(interval))
      .join("");

    if (set.repeat && set.repeat > 1) {
      return `<div class="card">
        <div class="card__header">
          ${set.type === "circuit" ? "Circuit" : "Repeat"} ${set.repeat} times
        </div>
        <div class="card__content">
          ${setContent}
        </div>
      </div>`;
    }

    return `<div class="card">
      <div class="card__content">
        ${setContent}
      </div>
    </div>`;
  }

  render() {
    if (!this.validateWorkout()) {
      this.target.innerHTML = '<div class="error">Invalid workout data</div>';
      return;
    }

    // Summary stats
    const statsHtml = `<div class="stats-bar">
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-box__label">Duration</div>
                <div class="stat-box__value">${this.formatTime(
                  this.workout.totalDuration
                )}</div>
            </div>
            <div class="stat-box">
                <div class="stat-box__label">Type</div>
                <div class="stat-box__value">${this.workout.type}</div>
            </div>
            <div class="stat-box">
                <div class="stat-box__label">Level</div>
                <div class="stat-box__value">${this.workout.level}</div>
            </div>
        </div>
    </div>`;

    // Workout title
    const headerHtml = `<div class="timer-header">
        <div class="timer-display">${this.workout.description}</div>
        <div class="timer-label">
            <span class="timer-label__emoji">💪</span>
            Let's get started!
        </div>
    </div>`;

    // Start button - positioned right after the header
    const startButtonHtml = `
        <button onclick="startWorkoutTimer()" class="button button--primary" style="width: calc(100% - 2rem); margin: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem">▶️</span> Start Timer
        </button>
    `;

    // Main content
    const setsHtml = this.workout.sets
      .map((set, index) => this.renderSet(set, index))
      .join("");

    // Notes if they exist
    const notesHtml = this.workout.notes
      ? `<div class="card">
        <div class="card__header">Notes</div>
        <div class="card__content">
            ${this.workout.notes
              .map(
                (note) =>
                  `<div class="exercise-item">
                    <div class="exercise-item__emoji">📝</div>
                    <div class="exercise-item__content">
                        <div class="exercise-item__title">${note}</div>
                    </div>
                </div>`
              )
              .join("")}
        </div>
    </div>`
      : "";

    // Combine all sections, with the start button positioned after the header
    this.target.innerHTML = `
        ${headerHtml}
        ${startButtonHtml}
        ${statsHtml}
        ${setsHtml}
        ${notesHtml}`;
  }

  // Helper methods
  formatTime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs ? `${mins}:${secs.toString().padStart(2, "0")}` : `${mins}m`;
  }

  formatDistance(miles) {
    return miles.toFixed(1);
  }

  formatPace(minutesPerMile) {
    const mins = Math.floor(minutesPerMile);
    const secs = Math.round((minutesPerMile - mins) * 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }


  renderTimerInterval(interval) {
    // Add debug logging to help us understand what data we're receiving
    console.log('Timer interval data:', interval);
    
    // Early return if no interval
    if (!interval) {
        return `
            <div class="current-activity">Workout Complete!</div>
            <div class="next-up">Great job!</div>
        `;
    }

    // Start building the HTML content
    let html = '';

    // Main activity title
    html += `<div class="current-activity">${interval.activity}</div>`;

    // For strength exercises, show sets/reps/weight
    if (interval.reps) {
        html += `
            <div class="next-up">
                ${interval.sets || 1} × ${interval.reps} reps
                ${interval.weight ? `@ ${interval.weight}lbs` : ''}
            </div>
        `;
    } 
    // For cardio exercises, show pace/speed/intensity
    else {
        const metrics = [];
        
        // Check both direct properties and targetMetrics
        const pace = interval.targetMetrics?.pace || interval.pace || interval.targetPace;
        const speed = interval.targetMetrics?.speed || interval.speed;
        const watts = interval.targetMetrics?.watts || interval.watts;
        const spm = interval.targetMetrics?.spm || interval.spm;
        const rpm = interval.targetMetrics?.rpm || interval.rpm;
        const distance = interval.targetMetrics?.distance || interval.distance;

        // Add each metric if it exists
        if (pace) {
            metrics.push(`Pace: ${this.formatPace(pace)}/mi`);
        }
        if (speed) {
            metrics.push(`Speed: ${speed} mph`);
        }
        if (watts) {
            metrics.push(`Power: ${watts}w`);
        }
        if (spm) {
            metrics.push(`${spm} spm`);
        }
        if (rpm) {
            metrics.push(`${rpm} rpm`);
        }
        if (distance) {
            metrics.push(`${this.formatDistance(distance)} miles`);
        }

        // Add metrics to display if we found any
        if (metrics.length > 0) {
            html += `<div class="next-up">${metrics.join(' • ')}</div>`;
        }
    }

    // Show intensity if available
    if (interval.intensity) {
        html += `<div class="next-up">${interval.intensity}</div>`;
    }

    // Show description if available
    if (interval.description) {
        html += `<div class="interval-description">${interval.description}</div>`;
    }

    return html;
}

}
