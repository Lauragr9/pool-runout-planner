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

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

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

function renderResult(result) {
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
  renderResult(result);
  draw();
});

draw();
