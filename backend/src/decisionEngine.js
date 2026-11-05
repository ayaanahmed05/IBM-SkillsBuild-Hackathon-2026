const tripEstimates = {
  food: { walkMinutes: 2, queueMinutes: 3, distanceMeters: 120 },
  restroom: { walkMinutes: 2, queueMinutes: 2, distanceMeters: 95 },
  shop: { walkMinutes: 3, queueMinutes: 4, distanceMeters: 180 }
};

export function makeState(scenario = "critical", need = "food") {
  const common = {
    scenario,
    need,
    venue: "Northstar Arena",
    dataMode: "SIMULATED",
    trip: tripEstimates[need] ?? tripEstimates.food
  };

  if (scenario === "timeout") {
    return {
      ...common, scoreA: 106, scoreB: 105, clock: "TIMEOUT · 0:48",
      gameState: "PLAY PAUSED", momentIntensity: 28, availableWindowMinutes: 5
    };
  }
  if (scenario === "resumed") {
    return {
      ...common, scoreA: 108, scoreB: 107, clock: "Q4 · 0:41",
      gameState: "PLAY RESUMED", momentIntensity: 91, availableWindowMinutes: 0,
      fanAwayFromSeat: true
    };
  }
  return {
    ...common, scenario: "critical", scoreA: 106, scoreB: 105, clock: "Q4 · 1:42",
    gameState: "CLOSE GAME", momentIntensity: 96, availableWindowMinutes: 0
  };
}

export function decide(state) {
  const trip = state.trip;
  const roundTripMinutes = (trip?.walkMinutes ?? 2) * 2 + (trip?.queueMinutes ?? 0);
  let action, confidence, title, explanation, reason;

  if (state.fanAwayFromSeat || state.scenario === "resumed") {
    action = "RETURN"; confidence = 93;
    title = "Game resumed — return now";
    explanation = "Play has resumed. Follow the fastest route back to your seat.";
    reason = "The game-state signal changed, so the return action takes priority.";
  } else if (state.gameState === "PLAY PAUSED" &&
             roundTripMinutes <= (state.availableWindowMinutes ?? 0)) {
    action = "GO"; confidence = 88;
    title = "A short trip may fit this pause";
    explanation = "The game is paused. Check the estimated round trip and leave time to return.";
    reason = `Estimated round trip is ${roundTripMinutes} minutes; the simulated window is ${state.availableWindowMinutes} minutes.`;
  } else if ((state.momentIntensity ?? 0) >= 75) {
    action = state.need === "food" ? "STAY" : "WAIT"; confidence = 96;
    title = action === "STAY" ? "Stay for the big moment" : "Wait for a safer window";
    explanation = action === "STAY"
      ? "The game is close and moment intensity is high. Consider in-seat delivery if available."
      : "This is a high-impact game window. Save the trip for a pause.";
    reason = "A short trip could overlap with a decisive possession.";
  } else {
    action = roundTripMinutes <= (state.availableWindowMinutes ?? 0) ? "GO" : "WAIT";
    confidence = 78;
    title = action === "GO" ? "Trip fits the current window" : "Wait for a better window";
    explanation = action === "GO"
      ? "The estimated trip fits the available window."
      : "The available window is shorter than the estimated round trip.";
    reason = `Estimated round trip: ${roundTripMinutes} minutes.`;
  }

  return {
    action, confidence, title, explanation, reason, roundTripMinutes,
    tripEstimate: trip,
    metrics: {
      queueMinutesAvoided: state.scenario === "critical" && state.need === "food" ? 8 : 4,
      walkingMetersReduced: state.scenario === "resumed" ? 115 : 180,
      momentsProtected: state.scenario === "resumed" ? 4 : 3
    }
  };
}
