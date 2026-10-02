const TABLE_WIDTH = 100;
const TABLE_HEIGHT = 50;
const POCKETS = [
  { x: 0, y: 0 }, { x: TABLE_WIDTH / 2, y: 0 }, { x: TABLE_WIDTH, y: 0 },
  { x: 0, y: TABLE_HEIGHT }, { x: TABLE_WIDTH / 2, y: TABLE_HEIGHT }, { x: TABLE_WIDTH, y: TABLE_HEIGHT },
];

const canvas = document.getElementById("table");
const ctx = canvas.getContext("2d");
const scale = canvas.width / TABLE_WIDTH;

// Each game mode keeps its own independent board (cue, balls, last solve
// result): switching tabs only changes which one is active, it never
// erases or shares data with the others.
function freshBoard() {
  return {
    cue: null,
    balls: [],
    solution: null,
    armedBallNumber: null,
    nextBallNumber: 1,
    lastResult: null,
    lastLayoutId: null,
  };
}

const boardsByMode = {
  freeform: freshBoard(),
  nine_ball: freshBoard(),
  eight_ball: freshBoard(),
};

let gameMode = "freeform";
let state = boardsByMode[gameMode];

const EIGHT_BALL_NUMBER = 8;
const NINE_BALL_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9];
const EIGHT_BALL_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];

const GAME_MODE_LABELS = {
  freeform: "Freeform",
  nine_ball: "9-Ball",
  eight_ball: "8-Ball",
};

function resetBoard() {
  const fresh = freshBoard();
  boardsByMode[gameMode] = fresh;
  state = fresh;
  document.getElementById("result").innerHTML = "";
  updateBallPalette();
  updateInstructions();
}

function showBoardForMode(mode) {
  gameMode = mode;
  state = boardsByMode[mode];
  if (state.lastResult) {
    renderResult(state.lastResult, state.lastLayoutId);
  } else {
    document.getElementById("result").innerHTML = "";
  }
  updateBallPalette();
  updateInstructions();
  draw();
}

function toLogical(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: ((clientX - rect.left) / rect.width) * TABLE_WIDTH,
    y: ((clientY - rect.top) / rect.height) * TABLE_HEIGHT,
  };
}

const GRID_STEP = 5;

function drawGrid() {
  ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
  ctx.lineWidth = 1;
  ctx.font = "10px sans-serif";
  ctx.fillStyle = "rgba(255, 255, 255, 0.6)";

  for (let x = 0; x <= TABLE_WIDTH; x += GRID_STEP) {
    ctx.beginPath();
    ctx.moveTo(x * scale, 0);
    ctx.lineTo(x * scale, canvas.height);
    ctx.stroke();

    ctx.textAlign = x === 0 ? "left" : x === TABLE_WIDTH ? "right" : "center";
    ctx.textBaseline = "top";
    ctx.fillText(String(x), x * scale, 2);
  }

  for (let y = 0; y <= TABLE_HEIGHT; y += GRID_STEP) {
    ctx.beginPath();
    ctx.moveTo(0, y * scale);
    ctx.lineTo(canvas.width, y * scale);
    ctx.stroke();

    ctx.textAlign = "left";
    ctx.textBaseline = y === 0 ? "top" : y === TABLE_HEIGHT ? "bottom" : "middle";
    ctx.fillText(String(y), 2, y * scale);
  }
}

const BALL_COLORS = [
  "#D4A017", // 1 / 9 yellow
  "#1E5AA8", // 2 / 10 blue
  "#C62828", // 3 / 11 red
  "#7B1FA2", // 4 / 12 purple
  "#EF6C00", // 5 / 13 orange
  "#2E7D32", // 6 / 14 green
  "#6D2932", // 7 / 15 maroon
];
const EIGHT_BALL_COLOR = "#111111";

function isStripeNumber(number) {
  return number >= 9 && number <= 15;
}

function shouldDrawAsStripe(number) {
  // solids/stripes is an 8-ball concept; 9-ball reuses ball 9's color but
  // doesn't care about the stripe pattern, so only show it in 8-ball mode
  return gameMode === "eight_ball" && isStripeNumber(number);
}

function ballColor(number) {
  if (number === EIGHT_BALL_NUMBER) return EIGHT_BALL_COLOR;
  if (isStripeNumber(number)) return BALL_COLORS[(number - 9) % BALL_COLORS.length];
  return BALL_COLORS[(number - 1) % BALL_COLORS.length];
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();

  ctx.fillStyle = "#111";
  for (const pocket of POCKETS) {
    ctx.beginPath();
    ctx.arc(pocket.x * scale, pocket.y * scale, 10, 0, Math.PI * 2);
    ctx.fill();
  }

  if (state.cue) {
    drawCueBall(state.cue);
  }
  for (const ball of state.balls) {
    drawBall(ball, ball.number);
  }

  if (state.solution) {
    drawSolution(state.solution);
  }
}

function drawSolution(order) {
  order.forEach((step, i) => {
    const pos = step.cue_rest_position;
    ctx.beginPath();
    ctx.arc(pos.x * scale, pos.y * scale, 7, 0, Math.PI * 2);
    ctx.strokeStyle = "#1d4ed8";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = "#1d4ed8";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(i + 1), pos.x * scale, pos.y * scale);
  });
}

function drawCueBall(pos) {
  const x = pos.x * scale;
  const y = pos.y * scale;
  ctx.beginPath();
  ctx.arc(x, y, 12, 0, Math.PI * 2);
  ctx.fillStyle = "#fff";
  ctx.fill();
  ctx.strokeStyle = "#000";
  ctx.stroke();
}

function drawBall(pos, number) {
  const x = pos.x * scale;
  const y = pos.y * scale;
  const r = 12;

  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.clip();

  if (shouldDrawAsStripe(number)) {
    ctx.fillStyle = "#fff";
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
    ctx.fillStyle = ballColor(number);
    ctx.fillRect(x - r, y - r * 0.55, r * 2, r * 1.1);
  } else {
    ctx.fillStyle = ballColor(number);
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }
  ctx.restore();

  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.strokeStyle = "#000";
  ctx.stroke();

  ctx.fillStyle = shouldDrawAsStripe(number) ? "#111" : "#fff";
  ctx.font = "12px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(String(number), x, y);
}

const POCKET_NAMES = {
  "0,0": "top-left corner",
  "50,0": "top side pocket",
  "100,0": "top-right corner",
  "0,50": "bottom-left corner",
  "50,50": "bottom side pocket",
  "100,50": "bottom-right corner",
};

function pocketName(pocket) {
  return POCKET_NAMES[`${pocket.x},${pocket.y}`] || `pocket (${pocket.x}, ${pocket.y})`;
}

function shotDifficulty(cutAngle) {
  if (cutAngle < 15) return { label: "straight shot", cls: "difficulty-easy" };
  if (cutAngle < 40) return { label: "slight angle", cls: "difficulty-easy" };
  if (cutAngle < 65) return { label: "medium cut", cls: "difficulty-medium" };
  return { label: "thin cut", cls: "difficulty-hard" };
}

function renderHistoryShotList(order) {
  const shotList = document.createElement("ol");
  shotList.className = "history-shot-list";
  order.forEach((step) => {
    const shotItem = document.createElement("li");
    const diff = shotDifficulty(step.cut_angle);
    const shotTypeNote = step.shot_type ? `, ${step.shot_type}` : "";
    shotItem.textContent = `Ball ${step.ball} → ${pocketName(step.pocket)} (${diff.label}${shotTypeNote})`;
    shotList.appendChild(shotItem);
  });
  return shotList;
}

function renderAttemptControls(layoutId) {
  const container = document.createElement("div");
  container.className = "attempt-controls";

  const label = document.createElement("p");
  label.className = "attempt-label";
  label.textContent = "Did you actually run out with this?";
  container.appendChild(label);

  const notesInput = document.createElement("input");
  notesInput.type = "text";
  notesInput.placeholder = "Optional notes";
  notesInput.className = "attempt-notes";
  container.appendChild(notesInput);

  const buttons = document.createElement("div");
  buttons.className = "attempt-buttons";

  async function logAttempt(succeeded) {
    await fetch(`/api/layouts/${layoutId}/attempts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ succeeded, notes: notesInput.value }),
    });
    container.innerHTML = "";
    const confirmMsg = document.createElement("p");
    confirmMsg.className = "attempt-confirm";
    confirmMsg.textContent = "Attempt logged, thanks!";
    container.appendChild(confirmMsg);
  }

  const yesBtn = document.createElement("button");
  yesBtn.type = "button";
  yesBtn.className = "attempt-yes";
  yesBtn.textContent = "Yes, it worked";
  yesBtn.addEventListener("click", () => logAttempt(true));

  const noBtn = document.createElement("button");
  noBtn.type = "button";
  noBtn.className = "attempt-no";
  noBtn.textContent = "No, it didn't";
  noBtn.addEventListener("click", () => logAttempt(false));

  buttons.appendChild(yesBtn);
  buttons.appendChild(noBtn);
  container.appendChild(buttons);

  return container;
}

function renderShotList(order) {
  const list = document.createElement("ol");
  list.className = "shot-list";

  order.forEach((step) => {
    const item = document.createElement("li");
    item.className = "shot";

    const ballBadge = document.createElement("span");
    ballBadge.className = "shot-ball";
    ballBadge.textContent = String(step.ball);

    const detail = document.createElement("details");
    detail.className = "shot-detail";

    const summary = document.createElement("summary");

    const target = document.createElement("span");
    target.className = "shot-target";
    target.textContent = `Ball ${step.ball} → ${pocketName(step.pocket)}`;
    summary.appendChild(target);

    const diff = shotDifficulty(step.cut_angle);
    const badge = document.createElement("span");
    badge.className = `difficulty ${diff.cls}`;
    badge.textContent = diff.label;
    summary.appendChild(badge);

    const shotTypeBadge = document.createElement("span");
    shotTypeBadge.className = "shot-type-badge";
    shotTypeBadge.textContent = step.shot_type;
    summary.appendChild(shotTypeBadge);

    detail.appendChild(summary);

    const technical = document.createElement("div");
    technical.className = "shot-technical";
    const rest = step.cue_rest_position;
    technical.innerHTML =
      `<p>Shot type: ${step.shot_type}</p>` +
      `<p>Cut angle: ${step.cut_angle.toFixed(1)}°</p>` +
      `<p>Pocket coordinates: (${step.pocket.x}, ${step.pocket.y})</p>` +
      `<p>Cue ball rests at: (${rest.x.toFixed(1)}, ${rest.y.toFixed(1)})</p>`;
    detail.appendChild(technical);

    item.appendChild(ballBadge);
    item.appendChild(detail);
    list.appendChild(item);
  });

  return list;
}

function renderResult(result, layoutId) {
  const resultBox = document.getElementById("result");
  resultBox.innerHTML = "";

  if (result.possible) {
    const heading = document.createElement("p");
    heading.className = "solution-heading";
    const shotWord = result.order.length === 1 ? "shot" : "shots";
    heading.textContent = `Run-out possible — ${result.order.length} ${shotWord} (numbers match the blue markers on the table)`;
    resultBox.appendChild(heading);
    resultBox.appendChild(renderShotList(result.order));
    resultBox.appendChild(renderAttemptControls(layoutId));
  } else {
    const heading = document.createElement("p");
    heading.className = "solution-heading impossible";
    heading.textContent = "No full run-out possible";
    resultBox.appendChild(heading);

    const note = document.createElement("p");
    note.className = "blocked-note";
    note.textContent =
      result.failed_at !== null && result.failed_at !== undefined
        ? `Blocked at ball ${result.failed_at}.`
        : "No order clears the rest of the balls from here.";
    resultBox.appendChild(note);
  }
}

function updateInstructions() {
  const instructions = document.getElementById("instructions");
  if (gameMode === "nine_ball" || gameMode === "eight_ball") {
    instructions.textContent =
      "Click the cue ball onto the table first, then pick a ball number below and click where it sits.";
  } else {
    instructions.textContent = "Click to place the cue ball (first click), then the object balls, in any order.";
  }
}

function paletteNumbersForMode() {
  if (gameMode === "nine_ball") return NINE_BALL_NUMBERS;
  if (gameMode === "eight_ball") return EIGHT_BALL_NUMBERS;
  return [];
}

function updateBallPalette() {
  const palette = document.getElementById("ball-palette");
  const numbers = paletteNumbersForMode();
  if (numbers.length === 0) {
    palette.hidden = true;
    return;
  }
  palette.hidden = false;
  palette.innerHTML = "";

  const label = document.createElement("span");
  label.className = "ball-palette-label";
  label.textContent = "Next ball:";
  palette.appendChild(label);

  const usedNumbers = new Set(state.balls.map((b) => b.number));
  numbers.forEach((number) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "palette-number";
    btn.textContent = String(number);
    if (shouldDrawAsStripe(number)) {
      const color = ballColor(number);
      btn.style.background = `repeating-linear-gradient(45deg, ${color}, ${color} 4px, #fff 4px, #fff 8px)`;
      btn.style.color = "#111";
    } else {
      btn.style.background = ballColor(number);
      btn.style.color = "#fff";
    }
    btn.disabled = usedNumbers.has(number);
    if (state.armedBallNumber === number) btn.classList.add("armed");
    btn.addEventListener("click", () => {
      state.armedBallNumber = number;
      updateBallPalette();
    });
    palette.appendChild(btn);
  });
}

document.querySelectorAll(".mode-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".mode-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    // each mode keeps its own board; switching tabs just shows whichever one
    // belongs to the newly selected mode, including its last solve result
    showBoardForMode(tab.dataset.mode);
  });
});

canvas.addEventListener("click", (event) => {
  const pos = toLogical(event.clientX, event.clientY);

  if (!state.cue) {
    state.cue = pos;
    draw();
    return;
  }

  if (gameMode === "nine_ball" || gameMode === "eight_ball") {
    if (state.armedBallNumber === null) return;
    state.balls.push({ number: state.armedBallNumber, x: pos.x, y: pos.y });
    state.armedBallNumber = null;
    updateBallPalette();
  } else {
    state.balls.push({ number: state.nextBallNumber++, x: pos.x, y: pos.y });
  }
  draw();
});

document.getElementById("reset").addEventListener("click", () => {
  resetBoard();
  draw();
});

document.getElementById("solve").addEventListener("click", async () => {
  const resultBox = document.getElementById("result");
  if (!state.cue || state.balls.length === 0) {
    resultBox.textContent = "Place the cue ball and at least one object ball.";
    return;
  }
  if (gameMode === "eight_ball" && !state.balls.some((b) => b.number === EIGHT_BALL_NUMBER)) {
    resultBox.textContent = "Place the 8-ball before solving.";
    return;
  }

  resultBox.textContent = "Solving...";
  const createResponse = await fetch("/api/layouts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cue: state.cue, balls: state.balls }),
  });
  const { id } = await createResponse.json();

  const solveResponse = await fetch(`/api/layouts/${id}/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ game_mode: gameMode }),
  });
  const result = await solveResponse.json();

  if (result.error) {
    resultBox.textContent = `Could not solve: ${result.error}`;
    return;
  }

  state.solution = result.possible ? result.order : null;
  state.lastResult = result;
  state.lastLayoutId = id;
  renderResult(result, id);
  draw();
});

const historyBox = document.getElementById("history");

document.getElementById("toggle-history").addEventListener("click", async () => {
  if (!historyBox.hidden) {
    historyBox.hidden = true;
    return;
  }
  historyBox.hidden = false;
  await loadHistory();
});

async function loadHistory() {
  historyBox.innerHTML = '<p class="placeholder">Loading...</p>';
  const response = await fetch("/api/history");
  const layouts = await response.json();

  historyBox.innerHTML = "";

  if (layouts.length === 0) {
    const empty = document.createElement("p");
    empty.className = "placeholder";
    empty.textContent = "No layouts saved yet.";
    historyBox.appendChild(empty);
    return;
  }

  const heading = document.createElement("p");
  heading.className = "solution-heading";
  heading.textContent = "Recent layouts";
  historyBox.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "history-list";

  layouts.forEach((layout) => {
    const item = document.createElement("li");
    item.className = "history-item";

    const summary = document.createElement("p");
    summary.className = "history-summary";
    const ballWord = layout.balls.length === 1 ? "ball" : "balls";
    const modeLabel = layout.solution ? GAME_MODE_LABELS[layout.solution.game_mode] : null;
    summary.textContent = modeLabel
      ? `Layout #${layout.id}: ${layout.balls.length} ${ballWord} (${modeLabel})`
      : `Layout #${layout.id}: ${layout.balls.length} ${ballWord}`;
    item.appendChild(summary);

    const positions = document.createElement("p");
    positions.className = "history-positions";
    const cueText = `Cue (${layout.cue.x.toFixed(1)}, ${layout.cue.y.toFixed(1)})`;
    const ballsText = layout.balls
      .map((b) => `Ball ${b.number} (${b.x.toFixed(1)}, ${b.y.toFixed(1)})`)
      .join(", ");
    positions.textContent = ballsText ? `${cueText}, ${ballsText}` : cueText;
    item.appendChild(positions);

    const solutionBox = document.createElement("div");
    solutionBox.className = "history-solution";
    if (layout.solution === null) {
      const note = document.createElement("p");
      note.className = "placeholder";
      note.textContent = "Not solved yet.";
      solutionBox.appendChild(note);
    } else if (layout.solution.possible) {
      solutionBox.appendChild(renderHistoryShotList(layout.solution.order));
    } else {
      const note = document.createElement("p");
      note.className = "blocked-note";
      note.textContent =
        layout.solution.failed_at !== null && layout.solution.failed_at !== undefined
          ? `No full run-out — blocked at ball ${layout.solution.failed_at}.`
          : "No order clears the rest of the balls from here.";
      solutionBox.appendChild(note);
    }
    item.appendChild(solutionBox);

    if (layout.attempts.length === 0) {
      const none = document.createElement("p");
      none.className = "history-attempt";
      none.textContent = "No attempts logged yet.";
      item.appendChild(none);
    } else {
      layout.attempts.forEach((attempt) => {
        const line = document.createElement("p");
        line.className = "history-attempt";
        const icon = attempt.succeeded ? "✓" : "✗";
        line.textContent = attempt.notes ? `${icon} ${attempt.notes}` : icon;
        item.appendChild(line);
      });
    }

    list.appendChild(item);
  });

  historyBox.appendChild(list);
}

updateInstructions();
updateBallPalette();
draw();
