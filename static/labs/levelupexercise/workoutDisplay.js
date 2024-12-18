// Unit and formatting utilities
const formatUnits = {
  // Weight formatting
  formatWeight: (value, unit = "imperial") => {
    if (typeof value !== "number") {
      console.error("Invalid weight value:", value);
      return "0 lbs";
    }
    if (unit === "metric") {
      return `${Math.round(value * 0.453592)} kg`;
    }
    return `${value} lbs`;
  },

  // Distance formatting
  formatDistance: (value, unit = "imperial") => {
    if (typeof value !== "number") {
      console.error("Invalid distance value:", value);
      return "0 mi";
    }
    if (unit === "metric") {
      return `${(value * 1.60934).toFixed(2)} km`;
    }
    return `${value.toFixed(2)} mi`;
  },

  formatPace: (minutesPerMile, unit = "imperial") => {
    console.log("Raw pace value received:", minutesPerMile);

    if (typeof minutesPerMile !== "number") {
      console.error("Invalid pace value:", minutesPerMile);
      return "--:--/mi";
    }

    // Log the intermediate calculations
    const totalMinutes =
      unit === "metric" ? minutesPerMile / 1.60934 : minutesPerMile;
    console.log("Total minutes:", totalMinutes);

    const minutes = Math.floor(totalMinutes);
    console.log("Minutes part:", minutes);

    const seconds = Math.round((totalMinutes - minutes) * 60);
    console.log("Seconds part:", seconds);

    const unit_label = unit === "metric" ? "/km" : "/mi";

    // If it's a round minute
    if (seconds === 0) {
      const result = `${minutes} min${unit_label}`;
      console.log("Final result (round minutes):", result);
      return result;
    }

    // Otherwise show MM:SS format
    const result = `${minutes}:${seconds
      .toString()
      .padStart(2, "0")}${unit_label}`;
    console.log("Final result (with seconds):", result);
    return result;
  },

  // Time formatting with smart display
  formatTime: (seconds) => {
    if (typeof seconds !== "number") {
      console.error("Invalid time value:", seconds);
      return "0s";
    }

    // Under 90 seconds: show as XXs
    if (seconds <= 90) {
      return `${seconds}s`;
    }

    // Round number of minutes: show as X min
    if (seconds % 60 === 0) {
      return `${seconds / 60} min`;
    }

    // Otherwise show as MM:SS
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`;
  },

  getExerciseMetrics: (interval, workoutType, unit = 'imperial') => {
    const metrics = [];
    const targets = interval.targetMetrics || {};

    // Always show duration if present
    if (interval.duration) {
        metrics.push({
            type: 'time',
            value: formatUnits.formatTime(interval.duration)
        });
    }

      if (workoutType === 'strength') {
          // For strength exercises
          if (interval.reps) {
              metrics.push({
                  type: 'reps',
                  value: `${interval.reps} reps`
              });
          }

          if (interval.weight) {
              const weight = unit === 'metric' 
                  ? Math.round(interval.weight * 0.453592)
                  : interval.weight;
              const unit_label = unit === 'metric' ? 'kg' : 'lbs';
              metrics.push({
                  type: 'weight',
                  value: `${weight} ${unit_label}`
              });
          }

          if (interval.sets) {
              metrics.push({
                  type: 'sets',
                  value: `${interval.sets} sets`
              });
          }

          // For rest periods in between exercises
          if (interval.type === 'rest' || interval.type === 'circuit_rest') {
              metrics.length = 0; // Clear other metrics for rest periods
              metrics.push({
                  type: 'rest',
                  value: formatUnits.formatTime(interval.duration)
              });
          }

          return metrics;
      }

    switch (workoutType) {
        case 'bike':
            // Handle both direct properties and targetMetrics
            const speed = targets.speed || interval.speed;
            const watts = targets.watts || interval.watts;
            const rpm = targets.cadence || interval.cadence || targets.rpm || interval.rpm;

            // Convert string metrics to numbers if needed
            if (speed && !isNaN(parseFloat(speed))) {
                metrics.push({
                    type: 'speed',
                    value: unit === 'metric'
                        ? `${(parseFloat(speed) * 1.60934).toFixed(1)} kph`
                        : `${parseFloat(speed).toFixed(1)} mph`
                });
            }
            if (watts && !isNaN(parseFloat(watts))) {
                metrics.push({
                    type: 'power',
                    value: `${Math.round(parseFloat(watts))}w`
                });
            }
            if (rpm && !isNaN(parseFloat(rpm))) {
                metrics.push({
                    type: 'rate',
                    value: `${Math.round(parseFloat(rpm))} rpm`
                });
            }
            break;

        case 'run':
            // Handle both targetMetrics and direct properties
            const pace = targets.pace || interval.pace || interval.targetPace;
            const distance = targets.distance || interval.distance;

            if (pace) {
                metrics.push({
                    type: 'pace',
                    value: formatUnits.formatPace(pace, unit)
                });
            }
            if (distance) {
                metrics.push({
                    type: 'distance',
                    value: unit === 'metric'
                        ? `${(distance * 1.60934).toFixed(2)} km`
                        : `${distance.toFixed(2)} mi`
                });
            }
            break;

        case 'swim':
            // Handle both lap-based and time-based metrics
            if (interval.laps) {
                metrics.push({
                    type: 'distance',
                    value: `${interval.laps} ${interval.laps === 1 ? 'lap' : 'laps'}`
                });
            }
            const swimPace = targets.pace || interval.targetPace;
            if (swimPace) {
                const paceValue = unit === 'metric' ? swimPace * 1.0936 : swimPace;
                metrics.push({
                    type: 'pace',
                    value: `${Math.floor(paceValue)}:${Math.round((paceValue % 1) * 60).toString().padStart(2, '0')}/100${unit === 'metric' ? 'm' : 'yd'}`
                });
            }
            break;

        case 'row':
            // Rowing metrics are already properly structured in targetMetrics
            if (targets.spm) {
                metrics.push({
                    type: 'rate',
                    value: `${targets.spm} spm`
                });
            }
            if (targets.split) {
              const minutes = Math.floor(targets.split / 60);
              const seconds = targets.split % 60;
              metrics.push({
                  type: 'pace',
                  value: `${minutes}:${seconds.toString().padStart(2, '0')}/500m`
              });
          }
            if (targets.watts) {
                metrics.push({
                    type: 'power',
                    value: `${targets.watts}w`
                });
            }
            break;
    }

    return metrics;
},
};

// Workout display component
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
    const missing = required.filter((prop) => !this.workout[prop]);

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

  renderNotes() {
    if (!this.workout.notes?.length && !this.workout.formCues?.length) {
      return "";
    }

    return `
        <div class="notes-section">
          ${
            this.workout.notes?.length
              ? `
            <div class="notes-block">
              <h2 class="notes-title">Notes</h2>
              <ul class="notes-list">
                ${this.workout.notes
                  .map(
                    (note) => `
                  <li class="note-item">
                    <div class="note-bullet"></div>
                    <span>${note}</span>
                  </li>
                `
                  )
                  .join("")}
              </ul>
            </div>
          `
              : ""
          }
  
          ${
            this.workout.formCues?.length
              ? `
            <div class="notes-block">
              <h2 class="notes-title">Form Cues</h2>
              <ul class="notes-list">
                ${this.workout.formCues
                  .map(
                    (cue) => `
                  <li class="note-item">
                    <div class="note-bullet"></div>
                    <span>${cue}</span>
                  </li>
                `
                  )
                  .join("")}
              </ul>
            </div>
          `
              : ""
          }
        </div>
      `;
  }

  renderMetricPills(interval) {
    const metrics = formatUnits.getExerciseMetrics(
        interval, 
        this.workout.type, 
        this.options.unitSystem
    );

    return metrics
        .map(metric => 
            `<span class="metric-pill metric-${metric.type}">${metric.value}</span>`
        )
        .join('');
}


  // renderMetricPills(interval) {
  //   const pills = [];
  //   const {
  //     formatTime,
  //     formatWeight,
  //     formatDistance,
  //     formatPace,
  //     formatRunningMetrics,
  //     formatCyclingMetrics,
  //     formatSwimmingMetrics,
  //   } = formatUnits;

  //   // Duration/Time
  //   if (interval.duration) {
  //     pills.push(
  //       `<span class="metric-pill metric-time">${formatTime(
  //         interval.duration
  //       )}</span>`
  //     );
  //   }

  //   // Weight training metrics
  //   if (interval.sets && interval.reps) {
  //     pills.push(
  //       `<span class="metric-pill metric-reps">${interval.reps} reps</span>`
  //     );
  //     if (interval.weight) {
  //       pills.push(
  //         `<span class="metric-pill metric-weight">${formatWeight(
  //           interval.weight,
  //           this.options.unitSystem
  //         )}</span>`
  //       );
  //     }
  //   }

  //   // Distance and pace
  //   if (interval.distance) {
  //     pills.push(
  //       `<span class="metric-pill metric-distance">${formatDistance(
  //         interval.distance,
  //         this.options.unitSystem
  //       )}</span>`
  //     );
  //   }
  //   if (interval.pace) {
  //     pills.push(
  //       `<span class="metric-pill metric-pace">${formatPace(
  //         interval.pace,
  //         this.options.unitSystem
  //       )}</span>`
  //     );
  //   }

  //   // Power metrics
  //   if (interval.watts) {
  //     pills.push(
  //       `<span class="metric-pill metric-power">${interval.watts}w</span>`
  //     );
  //   }
  //   if (interval.spm) {
  //     pills.push(
  //       `<span class="metric-pill metric-rate">${interval.spm} spm</span>`
  //     );
  //   }
  //   if (interval.rpm) {
  //     pills.push(
  //       `<span class="metric-pill metric-rate">${interval.rpm} rpm</span>`
  //     );
  //   }

  //   return pills.join("");
  // }

  renderInterval(interval) {
    if (!interval.activity) {
      console.error("Interval missing activity:", interval);
      return "";
    }

    return `
        <div class="interval-card">
          <h3 class="interval-title">${interval.activity}</h3>
          ${
            interval.type
              ? `<div class="machine-type">${interval.type}</div>`
              : ""
          }
          ${
            interval.intensity
              ? `<div class="interval-intensity">${interval.intensity}</div>`
              : ""
          }
          <div class="interval-metrics">
            ${this.renderMetricPills(interval)}
          </div>
        </div>
      `;
  }

  renderSet(set, index) {
    if (!set.intervals || !Array.isArray(set.intervals)) {
      console.error("Invalid set structure:", set);
      return "";
    }

    const isRepeated = set.repeat && set.repeat > 1;
    const content = set.intervals
      .map((interval) => this.renderInterval(interval))
      .join("");

    if (isRepeated) {
      return `
          <div class="repeat-container">
            <div class="repeat-header">
              ${set.type === "circuit" ? "Circuit" : "Repeat"} ${
        set.repeat
      } times
            </div>
            ${content}
          </div>
        `;
    }

    return `
        <div class="set-container">
          ${content}
        </div>
      `;
  }

  render() {
    if (!this.validateWorkout()) {
      this.target.innerHTML = '<div class="error">Invalid workout data</div>';
      return;
    }

    const headerColor =
      {
        strength: "#DC2626",
        run: "#4338CA",
        bike: "#059669",
        row: "#B45309",
      }[this.workout.type] || "#4338CA";

    const html = `
        <div class="workout-overview">
          <div class="overview-header" style="background-color: ${headerColor}">
            <h1 class="workout-title">${this.workout.description}</h1>
            <div class="workout-meta">
              ${formatUnits.formatTime(this.workout.totalDuration)} • 
              ${
                this.workout.type.charAt(0).toUpperCase() +
                this.workout.type.slice(1)
              } • 
              Level ${this.workout.level}
            </div>
          </div>
          <button onclick="startWorkoutTimer()" class="go-button">Go!</button>

          ${this.workout.sets
            .map((set, index) => this.renderSet(set, index))
            .join("")}

          ${this.renderNotes()}

        </div>
      `;

    this.target.innerHTML = html;
  }

  renderTimerInterval(interval) {
    const metrics = formatUnits.getExerciseMetrics(
        interval, 
        this.workout.type, 
        this.options.unitSystem
    );

    return `
        <div class="timer-interval">
            <h1 class="timer-activity">${interval.activity}</h1>
            ${interval.intensity ? 
                `<div class="timer-intensity">${interval.intensity}</div>` : 
                ''}
            <div class="timer-metrics">
                ${metrics.map(metric => 
                    `<div class="timer-metric timer-metric-${metric.type}">
                        ${metric.value}
                    </div>`
                ).join('')}
            </div>
            ${interval.description ? 
                `<div class="timer-description">${interval.description}</div>` : 
                ''}
        </div>
    `;
}
}
