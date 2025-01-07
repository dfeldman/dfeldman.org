class PowerUpSystem {
    constructor() {
      this.messages = [
        { text: "Not bad!", emoji: "⭐️" },
        { text: "Run like the wind!", emoji: "💨" },
        { text: "Getting stronger!", emoji: "💪" },
        { text: "Keep it up!", emoji: "🔥" },
        { text: "You're crushing it!", emoji: "⚡️" }
      ];
    }
  
    getPowerUp(elapsedTime) {
      // Every 5 minutes, give a new power-up
      if (elapsedTime % 300 === 0) {
        return this.messages[Math.floor(Math.random() * this.messages.length)];
      }
      return null;
    }
  }
  