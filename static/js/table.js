const TABLE_WIDTH = 100;
const TABLE_HEIGHT = 50;
const POCKETS = [
  { x: 0, y: 0 }, { x: TABLE_WIDTH / 2, y: 0 }, { x: TABLE_WIDTH, y: 0 },
  { x: 0, y: TABLE_HEIGHT }, { x: TABLE_WIDTH / 2, y: TABLE_HEIGHT }, { x: TABLE_WIDTH, y: TABLE_HEIGHT },
];

const canvas = document.getElementById("table");
const ctx = canvas.getContext("2d");
const scale = canvas.width / TABLE_WIDTH;

let state = { cue: null, balls: [] };
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
  state = { cue: null, balls: [] };
  nextBallNumber = 1;
  document.getElementById("result").textContent = "";
  draw();
});

document.getElementById("solve").addEventListener("click", async () => {
  const resultBox = document.getElementById("result");
  if (!state.cue || state.balls.length === 0) {
    resultBox.textContent = "Coloca la bola blanca y al menos una bola objetivo.";
    return;
  }

  resultBox.textContent = "Resolviendo...";
  const createResponse = await fetch("/api/layouts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
  const { id } = await createResponse.json();

  const solveResponse = await fetch(`/api/layouts/${id}/solve`, { method: "POST" });
  const result = await solveResponse.json();

  if (result.possible) {
    const lines = result.order.map(
      (step, i) => `${i + 1}. Bola ${step.ball} -> tronera (${step.pocket.x}, ${step.pocket.y}) - corte ${step.cut_angle.toFixed(1)}°`
    );
    resultBox.textContent = "Run-out posible:\n" + lines.join("\n");
  } else if (result.failed_at !== null && result.failed_at !== undefined) {
    resultBox.textContent = `No hay run-out posible. Se bloquea en la bola ${result.failed_at}.`;
  } else {
    resultBox.textContent = "No hay run-out posible con ningún orden.";
  }
});

draw();
