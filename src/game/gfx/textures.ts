import { Texture } from "pixi.js";

/**
 * All art is generated at boot: tiny pixel grids rendered to canvases and
 * wrapped in nearest-neighbour Pixi textures. No binary assets in the repo.
 */

function makeCanvas(w: number, h: number): [HTMLCanvasElement, CanvasRenderingContext2D] {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  ctx.imageSmoothingEnabled = false;
  return [c, ctx];
}

function toTexture(canvas: HTMLCanvasElement): Texture {
  const tex = Texture.from(canvas);
  tex.source.scaleMode = "nearest";
  return tex;
}

/** Render a pixel grid (one char = one pixel, "." = transparent) to a texture. */
function grid(rows: string[], legend: Record<string, string>): Texture {
  const h = rows.length;
  const w = rows[0]!.length;
  const [c, ctx] = makeCanvas(w, h);
  for (let y = 0; y < h; y++) {
    const row = rows[y]!;
    for (let x = 0; x < w; x++) {
      const ch = row[x]!;
      if (ch === ".") continue;
      const color = legend[ch];
      if (!color) continue;
      ctx.fillStyle = color;
      ctx.fillRect(x, y, 1, 1);
    }
  }
  return toTexture(c);
}

/** Duplicate rows [from, to) `times` extra times — used to build the "big" player. */
function stretchRows(rows: string[], from: number, to: number, times: number): string[] {
  const out: string[] = rows.slice(0, to);
  for (let i = 0; i < times; i++) out.push(...rows.slice(from, to));
  out.push(...rows.slice(to));
  return out;
}

// ---------------------------------------------------------------------------
// Palettes
// ---------------------------------------------------------------------------
const P = {
  red: "#e43b44",
  darkRed: "#a22633",
  skin: "#f0b482",
  brown: "#6f4223",
  darkBrown: "#4a2d16",
  blue: "#2c6ff2",
  darkBlue: "#1a3fa0",
  yellow: "#fee761",
  orange: "#f77622",
  white: "#ffffff",
  black: "#181425",
  green: "#3e8948",
  lightGreen: "#63c74d",
  darkGreen: "#265c42",
  gray: "#8b9bb4",
  darkGray: "#5a6988",
  purple: "#b55088",
  pink: "#f6757a",
  cyan: "#2ce8f5",
};

const playerLegend = {
  r: P.red, R: P.darkRed, s: P.skin, b: P.blue, B: P.darkBlue,
  k: P.black, w: P.white, h: P.brown,
};

// 14 x 16 — cap, face, blue overalls, boots.
const PLAYER_IDLE = [
  "....rrrrrr....",
  "...rrrrrrrr...",
  "...hhsskss....",
  "..hshssksss...",
  "..hshhssss....",
  "..hssssss.....",
  "....ssssss....",
  "...rrbrrb.....",
  "..rrrbrrbrr...",
  ".rrrrbbbbrrr..",
  ".ssrbwbbwbrss.",
  ".ssbbbbbbbbss.",
  ".sbbbbbbbbbbs.",
  "...bbb..bbb...",
  "..hhh....hhh..",
  ".hhhh....hhhh.",
];

const PLAYER_RUN1 = [
  "....rrrrrr....",
  "...rrrrrrrr...",
  "...hhsskss....",
  "..hshssksss...",
  "..hshhssss....",
  "..hssssss.....",
  "....ssssss....",
  "...rrbrrb.....",
  "..rrrbrrbrr...",
  ".rrrrbbbbrrs..",
  "..srbwbbwbss..",
  "..sbbbbbbbb...",
  "..bbbbbbbbb...",
  "...bbbbbb.....",
  "..hhh..bbb....",
  ".hhhh...hhh...",
];

const PLAYER_RUN2 = [
  "....rrrrrr....",
  "...rrrrrrrr...",
  "...hhsskss....",
  "..hshssksss...",
  "..hshhssss....",
  "..hssssss.....",
  "....ssssss....",
  "...rrbrrb.....",
  "..rrrbrrbrr...",
  "..rrrbbbbrr...",
  "..srbwbbwbs...",
  "...bbbbbbb....",
  "...bbbbbb.....",
  "....bbbb......",
  "...hhhhhh.....",
  "..hhh..hhh....",
];

const PLAYER_JUMP = [
  "....rrrrrr..s.",
  "...rrrrrrrrss.",
  "...hhsskss.ss.",
  "..hshssksss...",
  "..hshhssssr...",
  "..hssssssrr...",
  "..s.ssssssr...",
  "..ssrrbrrb....",
  "..srrrbrrbr...",
  "...rrbbbbrr...",
  "...rbwbbwbr...",
  "...bbbbbbbb...",
  "..bbbbbbbbb...",
  "..bbb...bbb...",
  ".hhh....hhh...",
  ".hhhh...hhhh..",
];

const walkerLegend = { o: P.orange, O: "#c2461e", k: P.black, w: P.white, f: "#8a5a2b" };
// 16 x 14 goomba-ish walker
const WALKER = [
  ".....oooooo.....",
  "...oooooooooo...",
  "..oooooooooooo..",
  ".oooowkooowkooo.",
  ".ooookkooookkoo.",
  "oooowkkoowkkooo.",
  "oooooooooooooooo",
  "oOOOoooooooOOOo.",
  ".OOOOOOOOOOOOO..",
  "..OOOOOOOOOOO...",
  "...ffffffffff...",
  "..ffff....ffff..",
  ".fffff....fffff.",
  ".ffff......ffff.",
];

const flyerLegend = { p: P.purple, P: "#7a3067", k: P.black, w: P.white, c: P.cyan };
// 16 x 12 bat-ish flyer, frame A wings up
const FLYER_A = [
  "c......cc......c",
  "cc....cccc....cc",
  ".cc..cccccc..cc.",
  ".ccc.pppppp.ccc.",
  "..ccppppppppcc..",
  "...ppwkppwkpp...",
  "...ppkkppkkpp...",
  "..pppppppppppp..",
  "..pPPppppppPPp..",
  "...PPPPPPPPPP...",
  "....PP....PP....",
  "...PP......PP...",
];

const FLYER_B = [
  "................",
  "................",
  ".....pppppp.....",
  "...pppppppppp...",
  "cccppwkppwkppccc",
  ".ccppkkppkkppcc.",
  "..cppppppppppc..",
  "..pPPppppppPPp..",
  "...PPPPPPPPPP...",
  "....PP....PP....",
  "...PP......PP...",
  "................",
];

const shellLegend = {
  g: P.lightGreen, G: P.darkGreen, y: "#e8d282", k: P.black, w: P.white, s: P.skin, e: P.green,
};
// 14 x 18 koopa-ish
const SHELLKICKER = [
  "....ssss......",
  "...ssksss.....",
  "...sskss......",
  "...sssss......",
  "....ss........",
  "..gggggg......",
  ".gggggggg.....",
  "gggeeeegggy...",
  "ggeeeeeeggy...",
  "geeeeeeeegy...",
  "geeGGGGeegy...",
  "ggeeeeeegyy...",
  ".ggggggggy....",
  "..gggggg......",
  "...yyyy.......",
  "..yy..yy......",
  ".yyy..yyy.....",
  ".yy....yy.....",
];

// 14 x 12 shell
const SHELL = [
  "....gggggg....",
  "..gggggggggg..",
  ".ggeeeeeeeegg.",
  ".geeGGGGGGeeg.",
  "geeGGeeeeGGeeg",
  "geeGeeeeeeGeeg",
  "geeGeeeeeeGeeg",
  "geeGGeeeeGGeeg",
  ".geeGGGGGGeeg.",
  ".ggeeeeeeeegg.",
  "..gggggggggg..",
  "..yyy....yyy..",
];

const bossLegend = {
  g: P.lightGreen, G: P.darkGreen, e: P.green, y: "#e8d282", k: P.black,
  w: P.white, r: P.red, o: P.orange, s: P.skin,
};
// 30 x 30 big bruiser boss
const BOSS = [
  "......rrr..........rrr........",
  ".....rrrr..........rrrr.......",
  "....rrr..............rrr......",
  "....ggggggggggggggggggg.......",
  "...ggggggggggggggggggggg......",
  "..gggwwkkgggggggggwwkkggg.....",
  "..gggwkkkgggggggggwkkkggg.....",
  "..ggggggggggggggggggggggg.....",
  "..gggggggggggggggggggggg......",
  "...gggggkkkkkkkkkkkggggg......",
  "...ggggkwwkwwkwwkwwkgggg......",
  "....gggkkkkkkkkkkkkkggg.......",
  "..ggeeeeeeeeeeeeeeeeeeegg.....",
  ".ggeeeGGGGGGGGGGGGGGGeeegg....",
  ".geeGGGeeeeeeeeeeeeGGGeeeg....",
  "ggeeGGeeGGGGGGGGGGeeGGeeegg...",
  "ggeeGeeeGGeeeeeeGGeeeGeeegg...",
  "ggeeGeeeGGeeeeeeGGeeeGeeegg...",
  "ggeeGGeeGGGGGGGGGGeeGGeeegg...",
  ".geeGGGeeeeeeeeeeeeGGGeeeg....",
  ".ggeeeGGGGGGGGGGGGGGGeeegg....",
  "..ggeeeeeeeeeeeeeeeeeeegg.....",
  "...ggggggggggggggggggggg......",
  "....ggggggg....ggggggg........",
  "....yyyyyy......yyyyyy........",
  "...yyyyyy........yyyyyy.......",
  "...yyyyy..........yyyyy.......",
  "..yyyyy............yyyyy......",
  "..yyyy..............yyyy......",
  ".yyyy................yyyy.....",
];

const itemLegend = {
  y: P.yellow, o: P.orange, r: P.red, w: P.white, k: P.black,
  s: P.skin, p: P.pink, g: P.lightGreen,
};

const COIN_A = [
  "...yyyyyy...",
  "..yyyyyyyy..",
  ".yyooooooyy.",
  ".yyoyyyyoyy.",
  "yyooyyyyooyy",
  "yyoyy..yyoyy",
  "yyoyy..yyoyy",
  "yyooyyyyooyy",
  ".yyoyyyyoyy.",
  ".yyooooooyy.",
  "..yyyyyyyy..",
  "...yyyyyy...",
];

const COIN_B = [
  "....yyyy....",
  "....yyyy....",
  "...yooooy...",
  "...yoyyoy...",
  "...yoyyoy...",
  "...yoyyoy...",
  "...yoyyoy...",
  "...yoyyoy...",
  "...yoyyoy...",
  "...yooooy...",
  "....yyyy....",
  "....yyyy....",
];

const MUSHROOM = [
  "....rrrrrr....",
  "..rrwwrrwwrr..",
  ".rrwwrrrrwwrr.",
  ".rrrrrwwrrrrr.",
  "rrwwrrwwrrwwrr",
  "rrwwrrrrrrwwrr",
  ".rrrrrrrrrrrr.",
  "..ssskssksss..",
  "..sssssssss...",
  "...sssssss....",
];

const HEART = [
  "..pp....pp..",
  ".prrp..prrp.",
  "prrrrpprrrrp",
  "prrwrrrrrrrp",
  "prrrrrrrrrrp",
  ".prrrrrrrrp.",
  "..prrrrrrp..",
  "...prrrrp...",
  "....prrp....",
  ".....pp.....",
];

// ---------------------------------------------------------------------------
// Tiles — drawn with canvas primitives + deterministic speckle noise
// ---------------------------------------------------------------------------
function speckle(ctx: CanvasRenderingContext2D, color: string, seed: number, count: number) {
  ctx.fillStyle = color;
  let s = seed;
  for (let i = 0; i < count; i++) {
    s = (s * 16807) % 2147483647;
    const x = s % 16;
    s = (s * 16807) % 2147483647;
    const y = s % 16;
    ctx.fillRect(x, y, 1, 1);
  }
}

function tileGroundTop(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = P.brown;
  ctx.fillRect(0, 0, 16, 16);
  speckle(ctx, P.darkBrown, 7, 14);
  ctx.fillStyle = P.lightGreen;
  ctx.fillRect(0, 0, 16, 4);
  ctx.fillStyle = P.green;
  ctx.fillRect(0, 3, 16, 2);
  ctx.fillRect(2, 5, 2, 1);
  ctx.fillRect(9, 5, 3, 1);
  return toTexture(c);
}

function tileGround(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = P.brown;
  ctx.fillRect(0, 0, 16, 16);
  speckle(ctx, P.darkBrown, 31, 18);
  speckle(ctx, "#835a33", 13, 10);
  return toTexture(c);
}

function tileBrick(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = "#b05a2c";
  ctx.fillRect(0, 0, 16, 16);
  ctx.fillStyle = "#7d3b1a";
  for (const y of [0, 7, 15]) ctx.fillRect(0, y, 16, 1);
  ctx.fillRect(7, 1, 1, 6);
  ctx.fillRect(3, 8, 1, 7);
  ctx.fillRect(11, 8, 1, 7);
  ctx.fillStyle = "#d97742";
  ctx.fillRect(0, 1, 16, 1);
  return toTexture(c);
}

function tileQuestion(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = P.orange;
  ctx.fillRect(0, 0, 16, 16);
  ctx.fillStyle = P.yellow;
  ctx.fillRect(1, 1, 14, 14);
  ctx.fillStyle = P.orange;
  ctx.fillRect(2, 2, 12, 12);
  // "?" glyph
  ctx.fillStyle = P.white;
  ctx.fillRect(5, 4, 6, 2);
  ctx.fillRect(9, 6, 2, 2);
  ctx.fillRect(7, 8, 3, 2);
  ctx.fillRect(7, 12, 2, 2);
  ctx.fillStyle = P.black;
  for (const [x, y] of [[1, 1], [14, 1], [1, 14], [14, 14]] as const) ctx.fillRect(x, y, 1, 1);
  return toTexture(c);
}

function tileUsed(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = "#7d3b1a";
  ctx.fillRect(0, 0, 16, 16);
  ctx.fillStyle = "#9c5a30";
  ctx.fillRect(1, 1, 14, 14);
  ctx.fillStyle = "#7d3b1a";
  ctx.fillRect(3, 3, 10, 10);
  return toTexture(c);
}

function tileStone(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = P.darkGray;
  ctx.fillRect(0, 0, 16, 16);
  ctx.fillStyle = "#3a4466";
  for (const y of [0, 7, 15]) ctx.fillRect(0, y, 16, 1);
  ctx.fillRect(5, 1, 1, 6);
  ctx.fillRect(10, 8, 1, 7);
  ctx.fillStyle = P.gray;
  ctx.fillRect(0, 1, 16, 1);
  speckle(ctx, "#3a4466", 43, 8);
  return toTexture(c);
}

function tileSpike(): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  ctx.fillStyle = P.gray;
  for (const bx of [0, 8]) {
    ctx.beginPath();
    ctx.moveTo(bx, 16);
    ctx.lineTo(bx + 4, 4);
    ctx.lineTo(bx + 8, 16);
    ctx.closePath();
    ctx.fill();
  }
  ctx.fillStyle = P.white;
  ctx.fillRect(3, 8, 1, 3);
  ctx.fillRect(11, 8, 1, 3);
  return toTexture(c);
}

function pipe(part: "tl" | "tr" | "bl" | "br"): Texture {
  const [c, ctx] = makeCanvas(16, 16);
  const left = part === "tl" || part === "bl";
  const top = part === "tl" || part === "tr";
  ctx.fillStyle = P.green;
  ctx.fillRect(0, 0, 16, 16);
  ctx.fillStyle = P.lightGreen;
  if (left) ctx.fillRect(2, 0, 3, 16);
  else ctx.fillRect(9, 0, 2, 16);
  ctx.fillStyle = P.darkGreen;
  if (left) ctx.fillRect(0, 0, 1, 16);
  else ctx.fillRect(15, 0, 1, 16);
  if (top) {
    ctx.fillStyle = P.darkGreen;
    ctx.fillRect(0, 14, 16, 2);
    ctx.fillStyle = P.lightGreen;
    ctx.fillRect(0, 0, 16, 2);
  }
  return toTexture(c);
}

// ---------------------------------------------------------------------------
// FX + misc
// ---------------------------------------------------------------------------
function dot(size: number, color: string): Texture {
  const [c, ctx] = makeCanvas(size, size);
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, size, size);
  return toTexture(c);
}

function circleDot(size: number, color: string): Texture {
  const [c, ctx] = makeCanvas(size, size);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
  ctx.fill();
  return toTexture(c);
}

function star(size: number, color: string): Texture {
  const [c, ctx] = makeCanvas(size, size);
  ctx.fillStyle = color;
  const m = Math.floor(size / 2);
  ctx.fillRect(m, 0, 1, size);
  ctx.fillRect(0, m, size, 1);
  ctx.fillRect(m - 1, m - 1, 3, 3);
  return toTexture(c);
}

/** Soft radial light — used for additive glow and erase-blend cave lighting. */
function radialLight(size: number): Texture {
  const [c, ctx] = makeCanvas(size, size);
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.4, "rgba(255,255,255,0.7)");
  g.addColorStop(0.75, "rgba(255,255,255,0.22)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  return toTexture(c);
}

function checkpointFlag(active: boolean): Texture {
  const [c, ctx] = makeCanvas(12, 28);
  ctx.fillStyle = "#c0cbdc";
  ctx.fillRect(2, 0, 2, 28);
  ctx.fillStyle = active ? P.lightGreen : P.darkGray;
  ctx.beginPath();
  ctx.moveTo(4, 1);
  ctx.lineTo(12, 5);
  ctx.lineTo(4, 9);
  ctx.closePath();
  ctx.fill();
  return toTexture(c);
}

function goalFlag(): Texture {
  const [c, ctx] = makeCanvas(16, 48);
  ctx.fillStyle = "#c0cbdc";
  ctx.fillRect(2, 0, 2, 48);
  ctx.fillStyle = P.yellow;
  ctx.beginPath();
  ctx.arc(3, 2, 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = P.red;
  ctx.beginPath();
  ctx.moveTo(4, 5);
  ctx.lineTo(16, 11);
  ctx.lineTo(4, 17);
  ctx.closePath();
  ctx.fill();
  return toTexture(c);
}

function movingPlatform(): Texture {
  const [c, ctx] = makeCanvas(48, 8);
  ctx.fillStyle = P.gray;
  ctx.fillRect(0, 0, 48, 8);
  ctx.fillStyle = "#c0cbdc";
  ctx.fillRect(0, 0, 48, 2);
  ctx.fillStyle = P.darkGray;
  ctx.fillRect(0, 6, 48, 2);
  for (const x of [3, 14, 25, 36, 44]) {
    ctx.fillStyle = "#3a4466";
    ctx.fillRect(x, 3, 2, 2);
  }
  return toTexture(c);
}

function torch(): Texture {
  const [c, ctx] = makeCanvas(6, 12);
  ctx.fillStyle = P.brown;
  ctx.fillRect(2, 5, 2, 7);
  ctx.fillStyle = P.orange;
  ctx.fillRect(1, 2, 4, 4);
  ctx.fillStyle = P.yellow;
  ctx.fillRect(2, 0, 2, 4);
  return toTexture(c);
}

function cloud(): Texture {
  const [c, ctx] = makeCanvas(28, 12);
  ctx.fillStyle = "rgba(255,255,255,0.9)";
  ctx.beginPath();
  ctx.arc(8, 8, 5, 0, Math.PI * 2);
  ctx.arc(15, 6, 6, 0, Math.PI * 2);
  ctx.arc(21, 8, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillRect(5, 8, 18, 4);
  return toTexture(c);
}

export interface GameTextures {
  player: { idle: Texture[]; run: Texture[]; jump: Texture[]; fall: Texture[] };
  playerBig: { idle: Texture[]; run: Texture[]; jump: Texture[]; fall: Texture[] };
  walker: Texture[];
  flyer: Texture[];
  shellkicker: Texture[];
  shell: Texture[];
  boss: Texture[];
  coin: Texture[];
  mushroom: Texture;
  heart: Texture;
  tiles: Record<string, Texture>;
  checkpointOff: Texture;
  checkpointOn: Texture;
  goal: Texture;
  cloud: Texture;
  platform: Texture;
  torch: Texture;
  particleSquare: Texture;
  particleCircle: Texture;
  particleStar: Texture;
  light: Texture;
}

let cache: GameTextures | null = null;

export function getTextures(): GameTextures {
  if (cache) return cache;

  const bigify = (rows: string[]) => stretchRows(rows, 8, 13, 1);
  const player = {
    idle: [grid(PLAYER_IDLE, playerLegend)],
    run: [grid(PLAYER_RUN1, playerLegend), grid(PLAYER_IDLE, playerLegend), grid(PLAYER_RUN2, playerLegend)],
    jump: [grid(PLAYER_JUMP, playerLegend)],
    fall: [grid(PLAYER_JUMP, playerLegend)],
  };
  const playerBig = {
    idle: [grid(bigify(PLAYER_IDLE), playerLegend)],
    run: [grid(bigify(PLAYER_RUN1), playerLegend), grid(bigify(PLAYER_IDLE), playerLegend), grid(bigify(PLAYER_RUN2), playerLegend)],
    jump: [grid(bigify(PLAYER_JUMP), playerLegend)],
    fall: [grid(bigify(PLAYER_JUMP), playerLegend)],
  };

  cache = {
    player,
    playerBig,
    walker: [grid(WALKER, walkerLegend)],
    flyer: [grid(FLYER_A, flyerLegend), grid(FLYER_B, flyerLegend)],
    shellkicker: [grid(SHELLKICKER, shellLegend)],
    shell: [grid(SHELL, shellLegend)],
    boss: [grid(BOSS, bossLegend)],
    coin: [grid(COIN_A, itemLegend), grid(COIN_B, itemLegend)],
    mushroom: grid(MUSHROOM, itemLegend),
    heart: grid(HEART, itemLegend),
    tiles: {
      groundTop: tileGroundTop(),
      ground: tileGround(),
      brick: tileBrick(),
      question: tileQuestion(),
      used: tileUsed(),
      stone: tileStone(),
      spike: tileSpike(),
      pipeTL: pipe("tl"),
      pipeTR: pipe("tr"),
      pipeBL: pipe("bl"),
      pipeBR: pipe("br"),
    },
    checkpointOff: checkpointFlag(false),
    checkpointOn: checkpointFlag(true),
    goal: goalFlag(),
    cloud: cloud(),
    platform: movingPlatform(),
    torch: torch(),
    particleSquare: dot(3, "#ffffff"),
    particleCircle: circleDot(5, "#ffffff"),
    particleStar: star(5, "#ffffff"),
    light: radialLight(256),
  };
  return cache;
}
