const TABLE_WIDTH = 100;
const TABLE_HEIGHT = 50;
const POCKETS = [
  { x: 0, y: 0 }, { x: TABLE_WIDTH / 2, y: 0 }, { x: TABLE_WIDTH, y: 0 },
  { x: 0, y: TABLE_HEIGHT }, { x: TABLE_WIDTH / 2, y: TABLE_HEIGHT }, { x: TABLE_WIDTH, y: TABLE_HEIGHT },
];

const canvas = document.getElementById("table");
const ctx = canvas.getContext("2d");
const scale = canvas.width / TABLE_WIDTH;

let state = { cue: null, balls: [], solution: null };
let nextBallNumber = 1;

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
    drawBall(state.cue, "#fff", null);
  }
  for (const ball of state.balls) {
    drawBall(ball, "#d62828", ball.number);
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

function drawBall(pos, color, label) {
  ctx.beginPath();
  ctx.arc(pos.x * scale, pos.y * scale, 12, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
  ctx.strokeStyle = "#000";
  ctx.stroke();
  if (label !== null && label !== undefined) {
    ctx.fillStyle = "#fff";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(label), pos.x * scale, pos.y * scale);
  }
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

function renderResult(result, layoutId) {
  const resultBox = document.getElementById("result");
  resultBox.innerHTML = "";

  if (result.possible) {
    const heading = document.createElement("p");
    heading.className = "solution-heading";
    const shotWord = result.order.length === 1 ? "shot" : "shots";
    heading.textContent = `Run-out possible — ${result.order.length} ${shotWord} (numbers match the blue markers on the table)`;
    resultBox.appendChild(heading);

    const list = document.createElement("ol");
    list.className = "shot-list";

    result.order.forEach((step) => {
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

      detail.appendChild(summary);

      const technical = document.createElement("div");
      technical.className = "shot-technical";
      const rest = step.cue_rest_position;
      technical.innerHTML =
        `<p>Cut angle: ${step.cut_angle.toFixed(1)}°</p>` +
        `<p>Pocket coordinates: (${step.pocket.x}, ${step.pocket.y})</p>` +
        `<p>Cue ball rests at: (${rest.x.toFixed(1)}, ${rest.y.toFixed(1)})</p>`;
      detail.appendChild(technical);

      item.appendChild(ballBadge);
      item.appendChild(detail);
      list.appendChild(item);
    });

    resultBox.appendChild(list);
    resultBox.appendChild(renderAttemptControls(layoutId));
  } else {
    const heading = document.createElement("p");
    heading.className = "solution-heading impossible";
    heading.textContent = "No run-out possible";
    resultBox.appendChild(heading);

    const note = document.createElement("p");
    note.className = "blocked-note";
    note.textContent =
      result.failed_at !== null && result.failed_at !== undefined
        ? `Blocked at ball ${result.failed_at}.`
        : "No order works for this layout.";
    resultBox.appendChild(note);
  }
}

canvas.addEventListener("click", (event) => {
  const pos = toLogical(event.clientX, event.clientY);
  if (!state.cue) {
    state.cue = pos;
  } else {
    state.balls.push({ number: nextBallNumber++, x: pos.x, y: pos.y });
  }
  draw();
});

document.getElementById("reset").addEventListener("click", () => {
  state = { cue: null, balls: [], solution: null };
  nextBallNumber = 1;
  document.getElementById("result").textContent = "";
  draw();
});

document.getElementById("solve").addEventListener("click", async () => {
  const resultBox = document.getElementById("result");
  if (!state.cue || state.balls.length === 0) {
    resultBox.textContent = "Place the cue ball and at least one object ball.";
    return;
  }

  resultBox.textContent = "Solving...";
  const createResponse = await fetch("/api/layouts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cue: state.cue, balls: state.balls }),
  });
  const { id } = await createResponse.json();

  const solveResponse = await fetch(`/api/layouts/${id}/solve`, { method: "POST" });
  const result = await solveResponse.json();

  state.solution = result.possible ? result.order : null;
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
    summary.textContent = `Layout #${layout.id} — ${layout.balls.length} ${ballWord}`;
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
    if (layout.solution.possible) {
      const shotList = document.createElement("ol");
      shotList.className = "history-shot-list";
      layout.solution.order.forEach((step) => {
        const shotItem = document.createElement("li");
        const diff = shotDifficulty(step.cut_angle);
        shotItem.textContent = `Ball ${step.ball} → ${pocketName(step.pocket)} (${diff.label})`;
        shotList.appendChild(shotItem);
      });
      solutionBox.appendChild(shotList);
    } else {
      const note = document.createElement("p");
      note.className = "blocked-note";
      note.textContent =
        layout.solution.failed_at !== null && layout.solution.failed_at !== undefined
          ? `No run-out possible — blocked at ball ${layout.solution.failed_at}.`
          : "No run-out possible with any order.";
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

draw();
