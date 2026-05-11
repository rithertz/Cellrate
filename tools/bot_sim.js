class Rect {
  constructor(x, y, w, h) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
  }

  copy() {
    return new Rect(this.x, this.y, this.w, this.h);
  }

  get left() { return this.x; }
  get right() { return this.x + this.w; }
  get top() { return this.y; }
  get bottom() { return this.y + this.h; }
  get centerx() { return this.x + this.w / 2; }
  get centery() { return this.y + this.h / 2; }

  colliderect(other) {
    return this.x < other.x + other.w &&
      this.x + this.w > other.x &&
      this.y < other.y + other.h &&
      this.y + this.h > other.y;
  }
}

function clampRect(rect, width, height) {
  rect.x = Math.max(0, Math.min(rect.x, width - rect.w));
  rect.y = Math.max(0, Math.min(rect.y, height - rect.h));
}

function centerDistance(a, b) {
  return Math.hypot(a.centerx - b.centerx, a.centery - b.centery);
}

function edgeDistance(a, b) {
  const dx = Math.max(a.left - b.right, b.left - a.right, 0);
  const dy = Math.max(a.top - b.bottom, b.top - a.bottom, 0);
  if (dx === 0 && dy === 0) {
    return -1;
  }
  return Math.hypot(dx, dy);
}

function stepEnemy(enemyRect, playerRect, speed) {
  const dx = playerRect.centerx - enemyRect.centerx;
  const dy = playerRect.centery - enemyRect.centery;
  const distance = Math.hypot(dx, dy);
  if (distance > 0) {
    enemyRect.x += Math.round(speed * dx / distance);
    enemyRect.y += Math.round(speed * dy / distance);
  }
}

function candidateMoves(speed) {
  const magnitude = Math.max(1, speed);
  const dirs = [[0, 0, "Holding line"]];
  const labels = [
    "Pressing east",
    "Cutting southeast",
    "Dropping south",
    "Cutting southwest",
    "Pressing west",
    "Climbing northwest",
    "Climbing north",
    "Cutting northeast",
  ];
  for (let i = 0; i < 8; i++) {
    const angle = i * (Math.PI / 4);
    dirs.push([Math.cos(angle) * magnitude, Math.sin(angle) * magnitude, labels[i]]);
  }

  const unique = new Map();
  for (const [dx, dy, label] of dirs) {
    const options = [
      [Math.round(dx), Math.round(dy), label],
      [Math.round(dx * 0.6), Math.round(dy * 0.6), `${label} carefully`],
    ];
    for (const option of options) {
      unique.set(`${option[0]},${option[1]}`, option);
    }
  }
  return [...unique.values()];
}

function emergencyEscape(playerRect, coinRect, enemyRects, width, height, speed) {
  let awayX = 0;
  let awayY = 0;
  for (const enemyRect of enemyRects) {
    const dx = playerRect.centerx - enemyRect.centerx;
    const dy = playerRect.centery - enemyRect.centery;
    const distance = Math.max(1, Math.hypot(dx, dy));
    const weight = 1 / distance;
    awayX += dx * weight;
    awayY += dy * weight;
  }

  awayX += (width / 2 - playerRect.centerx) * 0.08;
  awayY += (height / 2 - playerRect.centery) * 0.08;
  awayX += (coinRect.centerx - playerRect.centerx) * 0.02;
  awayY += (coinRect.centery - playerRect.centery) * 0.02;

  const magnitude = Math.hypot(awayX, awayY);
  if (magnitude === 0) {
    return [0, 0];
  }
  const scale = Math.max(1, speed) / magnitude;
  return [Math.round(awayX * scale), Math.round(awayY * scale)];
}

function scoreMove(playerRect, coinRect, enemyRects, width, height, enemySpeed, moveX, moveY) {
  const simulatedPlayer = playerRect.copy();
  const simulatedEnemies = enemyRects.map((rect) => rect.copy());
  const initialCoinDistance = centerDistance(playerRect, coinRect);
  let minGap = Number.POSITIVE_INFINITY;
  let totalGap = 0;
  let caughtFrame = null;
  let coinFrame = null;

  for (let frame = 1; frame <= 12; frame++) {
    simulatedPlayer.x += moveX;
    simulatedPlayer.y += moveY;
    clampRect(simulatedPlayer, width, height);

    for (const enemyRect of simulatedEnemies) {
      stepEnemy(enemyRect, simulatedPlayer, enemySpeed);
    }

    const frameGap = Math.min(...simulatedEnemies.map((enemyRect) => edgeDistance(simulatedPlayer, enemyRect)));
    minGap = Math.min(minGap, frameGap);
    totalGap += frameGap;

    if (frameGap < 0) {
      caughtFrame = frame;
      break;
    }
    if (coinFrame === null && simulatedPlayer.colliderect(coinRect)) {
      coinFrame = frame;
    }
  }

  if (caughtFrame !== null) {
    return -1000000 + caughtFrame * 100;
  }

  const finalCoinDistance = centerDistance(simulatedPlayer, coinRect);
  const coinProgress = initialCoinDistance - finalCoinDistance;
  const averageGap = totalGap / 12;
  const wallMargin = Math.min(
    simulatedPlayer.left,
    simulatedPlayer.top,
    width - simulatedPlayer.right,
    height - simulatedPlayer.bottom
  );
  const enemyDensity = simulatedEnemies.reduce(
    (sum, enemyRect) => sum + 1 / Math.max(20, centerDistance(simulatedPlayer, enemyRect)),
    0
  );

  let score = 0;
  score += Math.min(minGap, 220) * 6.5;
  score += averageGap * 1.0;
  score += coinProgress * 56;
  score -= finalCoinDistance * 1.45;
  score -= enemyDensity * 8250;
  score -= Math.max(0, 35 - wallMargin) * 40;

  if (coinFrame !== null) {
    score += 46000 - coinFrame * 460;
  }
  if (minGap < 22) {
    score -= (22 - minGap) * 2200;
  } else if (minGap < 40) {
    score -= (40 - minGap) * 300;
  }
  if (minGap > 120) {
    score += 800;
  }

  return score;
}

function chooseMove(playerRect, coinRect, enemyRects, width, height, playerSpeed, enemySpeed) {
  const nearestGap = Math.min(...enemyRects.map((enemyRect) => edgeDistance(playerRect, enemyRect)));
  if (nearestGap < Math.max(28, playerSpeed * 2.5)) {
    return emergencyEscape(playerRect, coinRect, enemyRects, width, height, playerSpeed);
  }

  let bestScore = -Infinity;
  let bestMove = [0, 0];
  for (const [dx, dy] of candidateMoves(playerSpeed)) {
    const score = scoreMove(playerRect, coinRect, enemyRects, width, height, enemySpeed, dx, dy);
    if (score > bestScore) {
      bestScore = score;
      bestMove = [dx, dy];
    }
  }
  return bestMove;
}

function makeRng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function randomInt(rng, min, max) {
  return min + Math.floor(rng() * (max - min + 1));
}

function spawnCoin(rng, width, height) {
  return new Rect(randomInt(rng, 0, width - 20), randomInt(rng, 0, height - 20), 20, 20);
}

function spawnEnemy(rng, width, height) {
  return new Rect(randomInt(rng, 0, width - 30), randomInt(rng, 0, height - 30), 30, 30);
}

function runEpisode(seed) {
  const rng = makeRng(seed);
  const width = 900;
  const height = 600;
  const player = { rect: new Rect(100, 100, 50, 50), speed: 5, baseSpeed: 5 };
  let coin = spawnCoin(rng, width, height);
  let enemies = [new Rect(300, 200, 30, 30)];
  let score = 0;
  let level = 1;

  for (let frame = 0; frame < 6000; frame++) {
    level = 1 + Math.floor(score / 10);
    if (level % 2 === 0 && enemies.length < 10 && enemies.length < 1 + Math.floor(level / 2)) {
      enemies.push(spawnEnemy(rng, width, height));
    }

    const enemySpeed = Math.min(1 + level * 0.2 + score * 0.05, 10);
    const [dx, dy] = chooseMove(player.rect.copy(), coin.copy(), enemies.map((enemy) => enemy.copy()), width, height, player.speed, enemySpeed);
    player.rect.x += dx;
    player.rect.y += dy;
    clampRect(player.rect, width, height);

    if (player.rect.colliderect(coin)) {
      score += level;
      player.speed += 0.2 + 0.1 * level;
      coin = spawnCoin(rng, width, height);
    }

    for (const enemy of enemies) {
      stepEnemy(enemy, player.rect, enemySpeed);
      if (player.rect.colliderect(enemy)) {
        return { seed, score, frame, level, coins: Math.floor(score / Math.max(1, level)) };
      }
    }
  }

  return { seed, score, frame: 6000, level, coins: "timeout" };
}

function main() {
  const episodes = Number(process.argv[2] || 200);
  const results = [];
  for (let i = 1; i <= episodes; i++) {
    results.push(runEpisode(i));
  }

  const scores = results.map((result) => result.score).sort((a, b) => a - b);
  const total = scores.reduce((sum, value) => sum + value, 0);
  const average = total / episodes;
  const median = scores[Math.floor(scores.length / 2)];
  const best = scores[scores.length - 1];
  const worst = scores[0];
  const over50 = scores.filter((score) => score >= 50).length;
  const over100 = scores.filter((score) => score >= 100).length;

  console.log(JSON.stringify({
    episodes,
    average,
    median,
    best,
    worst,
    over50,
    over100,
    sampleWorst: results.sort((a, b) => a.score - b.score).slice(0, 5),
    sampleBest: results.sort((a, b) => b.score - a.score).slice(0, 5),
  }, null, 2));
}

main();
