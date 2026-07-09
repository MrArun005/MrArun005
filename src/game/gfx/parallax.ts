import { Container, Graphics, Sprite } from "pixi.js";
import { VIEW_H, VIEW_W } from "../constants";
import type { LevelTheme } from "../level/ldtk";
import type { GameTextures } from "./textures";

/**
 * Theme-specific parallax backdrops. Four layers total:
 *   sky (multiplier 0) → far (0.2) → near (0.5) → gameplay world (1.0).
 * Layers are built wide enough to cover their scroll range for the level.
 */

interface ParallaxBuild {
  sky: Container;
  far: Container;
  near: Container;
}

/** Deterministic pseudo-random for stable decorations. */
function rng(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
}

function gradient(colors: Array<[number, number]>, h = VIEW_H): Graphics {
  // colors: [color, band height fraction]
  const g = new Graphics();
  let y = 0;
  for (const [color, frac] of colors) {
    const bh = Math.ceil(h * frac);
    g.rect(-64, y, VIEW_W + 128, bh + 1).fill(color);
    y += bh;
  }
  return g;
}

export function buildParallax(theme: LevelTheme, levelWidth: number, tex: GameTextures): ParallaxBuild {
  const farWidth = VIEW_W + levelWidth * 0.25 + 64;
  const nearWidth = VIEW_W + levelWidth * 0.55 + 64;
  const sky = new Container();
  const far = new Container();
  const near = new Container();
  const rand = rng(1337);

  if (theme === "overworld") {
    sky.addChild(gradient([
      [0x3a9efd, 0.35],
      [0x5fb9ff, 0.3],
      [0x8fd3ff, 0.2],
      [0xc3ecff, 0.15],
    ]));
    // Sun
    const sun = new Graphics().circle(VIEW_W - 70, 44, 16).fill(0xfff3a0);
    sun.circle(VIEW_W - 70, 44, 22).fill({ color: 0xfff3a0, alpha: 0.25 });
    sky.addChild(sun);

    // Far mountains
    const mountains = new Graphics();
    for (let x = -40; x < farWidth; x += 90) {
      const h = 60 + rand() * 50;
      mountains.moveTo(x, VIEW_H).lineTo(x + 65, VIEW_H - h).lineTo(x + 130, VIEW_H).closePath().fill(0x4a7bd4);
      mountains.moveTo(x + 45, VIEW_H).lineTo(x + 95, VIEW_H - h * 0.7).lineTo(x + 150, VIEW_H).closePath()
        .fill(0x5d8fe8);
    }
    far.addChild(mountains);

    // Near hills + clouds
    const hills = new Graphics();
    for (let x = -60; x < nearWidth; x += 120) {
      const h = 36 + rand() * 30;
      hills.ellipse(x + 60, VIEW_H + 14, 85, h).fill(0x3e8948);
    }
    near.addChild(hills);
    for (let i = 0; i < Math.ceil(nearWidth / 130); i++) {
      const c = new Sprite(tex.cloud);
      c.position.set(i * 130 + rand() * 60, 24 + rand() * 70);
      c.alpha = 0.85;
      c.scale.set(1 + rand());
      near.addChild(c);
    }
  } else if (theme === "cave") {
    sky.addChild(gradient([
      [0x10121f, 0.55],
      [0x171a2c, 0.45],
    ]));
    // Distant crystal glints
    const glints = new Graphics();
    for (let i = 0; i < 60; i++) {
      glints.rect(rand() * VIEW_W, rand() * VIEW_H, 1, 1).fill({ color: 0x2ce8f5, alpha: 0.25 + rand() * 0.5 });
    }
    sky.addChild(glints);

    // Far rock columns
    const rocks = new Graphics();
    for (let x = -30; x < farWidth; x += 70) {
      const w = 24 + rand() * 30;
      const h = 70 + rand() * 90;
      rocks.rect(x, VIEW_H - h, w, h).fill(0x232840);
      rocks.rect(x + 8, 0, w * 0.5, 40 + rand() * 60).fill(0x232840);
    }
    far.addChild(rocks);

    // Near stalagmites/stalactites
    const stal = new Graphics();
    for (let x = -40; x < nearWidth; x += 55) {
      const h = 40 + rand() * 55;
      stal.moveTo(x, VIEW_H).lineTo(x + 14, VIEW_H - h).lineTo(x + 28, VIEW_H).closePath().fill(0x2e3450);
      const th = 30 + rand() * 45;
      stal.moveTo(x + 22, 0).lineTo(x + 34, th).lineTo(x + 46, 0).closePath().fill(0x2e3450);
    }
    near.addChild(stal);
  } else {
    // castle
    sky.addChild(gradient([
      [0x2b0f1e, 0.4],
      [0x471426, 0.3],
      [0x611b2e, 0.3],
    ]));
    // Blood moon + stars
    const moon = new Graphics().circle(70, 48, 18).fill(0xe43b44);
    moon.circle(70, 48, 25).fill({ color: 0xe43b44, alpha: 0.2 });
    sky.addChild(moon);
    const stars = new Graphics();
    for (let i = 0; i < 40; i++) {
      stars.rect(rand() * VIEW_W, rand() * VIEW_H * 0.6, 1, 1).fill({ color: 0xf6757a, alpha: 0.3 + rand() * 0.5 });
    }
    sky.addChild(stars);

    // Far castle towers
    const towers = new Graphics();
    for (let x = -30; x < farWidth; x += 110) {
      const h = 80 + rand() * 70;
      towers.rect(x, VIEW_H - h, 44, h).fill(0x1a0b12);
      for (let bx = 0; bx < 44; bx += 11) towers.rect(x + bx, VIEW_H - h - 7, 6, 7).fill(0x1a0b12);
      // lit windows
      if (rand() > 0.4) towers.rect(x + 18, VIEW_H - h + 18, 5, 8).fill({ color: 0xf77622, alpha: 0.8 });
    }
    far.addChild(towers);

    // Near battlements
    const walls = new Graphics();
    for (let x = -40; x < nearWidth; x += 90) {
      const h = 34 + rand() * 26;
      walls.rect(x, VIEW_H - h, 70, h).fill(0x2b1420);
      for (let bx = 0; bx < 70; bx += 14) walls.rect(x + bx, VIEW_H - h - 6, 8, 6).fill(0x2b1420);
    }
    near.addChild(walls);
  }

  return { sky, far, near };
}
