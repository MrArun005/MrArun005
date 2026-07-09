/**
 * Level authoring tool. Paints levels onto a char grid, converts them to
 * LDtk-schema JSON (IntGrid collision layer + Entities layer) and writes them
 * to src/game/level/data/*.json. The game imports ONLY the JSON output —
 * exactly as if the levels came from a real LDtk project export.
 *
 * Regenerate with:  node scripts/generate-levels.mjs
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const TILE = 16;

// Keep in sync with src/game/level/ldtk.ts
const TILE_CHARS = { "#": 1, B: 2, "?": 3, M: 4, S: 6, "^": 7, P: 8, I: 9 };
const ENTITY_CHARS = {
  p: "PlayerStart", w: "Walker", W: "Walker2", v: "Walker3",
  f: "Flyer", F: "Flyer2", k: "ShellKicker", K: "ShellKicker2",
  c: "Coin", h: "Heart", C: "Checkpoint", m: "PlatformH", n: "PlatformV",
  X: "Boss", G: "Goal", D: "PipeWarp", L: "Torch",
};

function toFieldInstances(obj) {
  return Object.entries(obj).map(([k, v]) => ({
    __identifier: k,
    __type: typeof v === "number" ? "Int" : typeof v === "boolean" ? "Bool" : "String",
    __value: v,
  }));
}

let iid = 0;
function buildLDtkLevel({ identifier, theme, rows, fields = {} }) {
  const cHei = rows.length;
  const cWid = Math.max(...rows.map((r) => r.length));
  const intGridCsv = new Array(cWid * cHei).fill(0);
  const entities = [];
  const cursor = {};
  for (let y = 0; y < cHei; y++) {
    for (let x = 0; x < cWid; x++) {
      const ch = rows[y][x] ?? " ";
      if (TILE_CHARS[ch] !== undefined) {
        intGridCsv[y * cWid + x] = TILE_CHARS[ch];
      } else if (ENTITY_CHARS[ch]) {
        const idx = (cursor[ch] = (cursor[ch] ?? -1) + 1);
        entities.push({
          __identifier: ENTITY_CHARS[ch],
          __grid: [x, y],
          px: [x * TILE, y * TILE],
          width: TILE,
          height: TILE,
          fieldInstances: toFieldInstances(fields[ch]?.[idx] ?? {}),
        });
      }
    }
  }
  return {
    identifier,
    iid: `level-${iid++}`,
    pxWid: cWid * TILE,
    pxHei: cHei * TILE,
    fieldInstances: toFieldInstances({ theme }),
    layerInstances: [
      { __identifier: "Entities", __type: "Entities", __cWid: cWid, __cHei: cHei, __gridSize: TILE, intGridCsv: [], entityInstances: entities },
      { __identifier: "Collision", __type: "IntGrid", __cWid: cWid, __cHei: cHei, __gridSize: TILE, intGridCsv, entityInstances: [] },
    ],
  };
}

// ---------------------------------------------------------------------------
// Painter
// ---------------------------------------------------------------------------
function painter(w, h) {
  const g = Array.from({ length: h }, () => Array(w).fill(" "));
  const set = (x, y, ch) => {
    if (x >= 0 && x < w && y >= 0 && y < h) g[y][x] = ch;
  };
  return {
    set,
    rect(x0, y0, x1, y1, ch) {
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) set(x, y, ch);
    },
    /** Solid floor spanning [x0, x1] on rows 15-16. */
    ground(x0, x1, ch = "#") {
      this.rect(x0, 15, x1, 16, ch);
    },
    /** Spike pit: spikes on row 15, solid base row 16. */
    spikePit(x0, x1, base = "S") {
      this.rect(x0, 15, x1, 15, "^");
      this.rect(x0, 16, x1, 16, base);
    },
    /** 2-wide pipe of `height` tiles standing on the floor (rows up from 14). */
    pipe(x, height) {
      this.rect(x, 15 - height, x + 1, 14, "P");
    },
    /** Ascending stairs: step i is a column of height i+1, footprint [x, x+steps). */
    stairs(x, steps, ch = "#") {
      for (let i = 0; i < steps; i++) this.rect(x + i, 14 - i, x + i, 14, ch);
    },
    coinArc(x0, y, count) {
      for (let i = 0; i < count; i++) set(x0 + i, y - (i > 0 && i < count - 1 ? 1 : 0), "c");
    },
    coinRow(x0, y, count) {
      for (let i = 0; i < count; i++) set(x0 + i, y, "c");
    },
    rows: () => g.map((r) => r.join("")),
  };
}

// ---------------------------------------------------------------------------
// Level 1 — Green Hills (overworld)
// ---------------------------------------------------------------------------
function level1() {
  const p = painter(130, 17);
  p.ground(0, 33);
  p.ground(38, 59);
  p.ground(64, 95);
  p.ground(100, 129);

  p.set(3, 14, "p");

  // question-block row (bump from below at row 11)
  p.set(12, 11, "?");
  p.set(13, 11, "B");
  p.set(14, 11, "M");
  p.set(15, 11, "B");
  p.set(16, 11, "?");

  p.pipe(26, 2); // decorative pipe
  p.set(20, 14, "w");
  p.set(30, 14, "w");

  p.coinArc(34, 10, 4); // over the first gap

  p.rect(40, 12, 43, 12, "B");
  p.set(46, 14, "w");

  // warp pipe → Crystal Cave (level index 1)
  p.pipe(50, 3);
  p.set(50, 11, "D");

  p.rect(60, 12, 63, 12, "B"); // bridge over gap 2
  p.coinRow(60, 10, 4);

  p.set(67, 14, "C"); // checkpoint
  p.set(70, 14, "w");
  p.coinRow(72, 13, 4);
  p.set(76, 14, "k");
  p.set(79, 11, "B");
  p.set(80, 11, "M");
  p.set(81, 11, "B");
  p.set(84, 8, "f");
  p.set(90, 14, "W");

  p.set(96, 13, "m"); // moving platform over gap 3
  p.coinRow(96, 10, 4);

  p.stairs(105, 4);
  p.coinRow(106, 9, 4);
  p.set(117, 14, "w");
  p.set(124, 14, "G");

  return buildLDtkLevel({
    identifier: "Green_Hills",
    theme: "overworld",
    rows: p.rows(),
    fields: {
      D: [{ target: 1 }],
      m: [{ axis: "x", range: 56, speed: 40 }],
    },
  });
}

// ---------------------------------------------------------------------------
// Level 2 — Crystal Cave (dynamic 2D lighting)
// ---------------------------------------------------------------------------
function level2() {
  const p = painter(120, 17);
  p.rect(0, 0, 119, 0, "S"); // ceiling
  p.rect(0, 1, 0, 16, "S"); // left wall
  p.rect(119, 1, 119, 16, "S"); // right wall
  p.ground(0, 27, "S");
  p.spikePit(28, 31);
  p.ground(32, 51, "S");
  p.spikePit(52, 56);
  p.ground(57, 81, "S");
  p.spikePit(82, 85);
  p.ground(86, 119, "S");

  // stalactites
  for (const x of [10, 26, 42, 58, 74, 90, 106]) p.rect(x, 1, x, 1, "S");

  p.set(3, 14, "p");

  // torches light the way
  for (const x of [8, 24, 40, 56, 72, 88, 104]) p.set(x, 11, "L");

  p.set(20, 8, "f");
  p.coinArc(28, 12, 4);

  p.rect(36, 11, 39, 11, "S"); // floating ledge
  p.coinRow(36, 9, 4);
  p.set(34, 9, "f");

  p.rect(44, 9, 47, 9, "S"); // higher ledge
  p.set(44, 5, "B");
  p.set(45, 5, "M");
  p.set(46, 5, "B");

  p.set(52, 12, "m"); // platform ferries across the long spike pit
  p.set(60, 8, "F");
  p.set(60, 14, "C"); // checkpoint
  p.set(64, 14, "K");
  p.coinRow(68, 13, 4);

  p.set(83, 8, "n"); // vertical platform over pit 3
  p.set(90, 7, "F");
  p.coinArc(86, 11, 4);

  p.rect(96, 11, 99, 11, "S");
  p.coinRow(96, 9, 4);
  p.set(96, 14, "k");
  p.set(102, 14, "w");

  p.stairs(106, 3, "S");
  p.set(114, 14, "G");

  return buildLDtkLevel({
    identifier: "Crystal_Cave",
    theme: "cave",
    rows: p.rows(),
    fields: {
      m: [{ axis: "x", range: 72, speed: 45 }],
      n: [{ axis: "y", range: 44, speed: 32 }],
    },
  });
}

// ---------------------------------------------------------------------------
// Level 3 — Castle Keep (3-phase boss)
// ---------------------------------------------------------------------------
function level3() {
  const p = painter(110, 17);
  p.rect(0, 0, 109, 0, "S");
  p.rect(0, 1, 0, 16, "S");
  p.rect(108, 1, 109, 16, "S"); // right wall (arena edge)
  p.ground(0, 19, "S");
  p.spikePit(20, 22);
  p.ground(23, 39, "S");
  p.spikePit(40, 43);
  p.ground(44, 109, "S");

  p.set(3, 14, "p");
  p.set(9, 11, "?");
  p.set(10, 11, "B");
  p.set(11, 11, "?");
  p.set(14, 14, "W");
  p.coinArc(20, 12, 3);

  p.rect(26, 11, 28, 11, "S");
  p.coinRow(26, 9, 3);
  p.set(30, 14, "v"); // tier-3 walker
  p.set(36, 8, "F");

  p.set(41, 12, "n"); // vertical platform over the wide pit
  p.coinArc(40, 9, 4);

  p.set(48, 14, "K");
  p.set(52, 10, "h"); // floating heart
  p.set(56, 11, "M");
  p.set(60, 14, "C"); // checkpoint before the arena

  // arena entrance: stairs up, high wall, drop in — no way back
  p.stairs(64, 4, "S");
  p.rect(70, 10, 71, 14, "S");

  // arena decor torches
  for (const x of [78, 90, 102]) p.set(x, 10, "L");
  p.coinRow(80, 13, 3);

  p.set(92, 12, "X"); // the boss

  return buildLDtkLevel({
    identifier: "Castle_Keep",
    theme: "castle",
    rows: p.rows(),
    fields: {
      n: [{ axis: "y", range: 48, speed: 36 }],
    },
  });
}

// ---------------------------------------------------------------------------
const outDir = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "game", "level", "data");
mkdirSync(outDir, { recursive: true });
const levels = [level1(), level2(), level3()];
levels.forEach((lvl, i) => {
  const file = join(outDir, `level-${i + 1}.json`);
  writeFileSync(file, JSON.stringify(lvl, null, 1) + "\n");
  console.log(`wrote ${file} (${lvl.identifier}, ${lvl.pxWid}x${lvl.pxHei}px)`);
});
