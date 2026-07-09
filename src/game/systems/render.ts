import { CAMERA, VIEW_H, VIEW_W } from "../constants";
import type { Ctx } from "../context";

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Cheap deterministic "noise" for shake — layered incommensurate sines. */
function noise1(t: number): number {
  return Math.sin(t * 47.3) * 0.55 + Math.sin(t * 91.7 + 2.1) * 0.3 + Math.sin(t * 173.3 + 4.7) * 0.15;
}
function noise2(t: number): number {
  return Math.sin(t * 53.9 + 1.3) * 0.55 + Math.sin(t * 101.1 + 3.4) * 0.3 + Math.sin(t * 167.9) * 0.15;
}

/**
 * Render pass: interpolate entity positions between the previous and current
 * fixed ticks, then place the camera (with trauma shake) and parallax layers.
 */
export function renderSystem(ctx: Ctx, alpha: number, realTime: number): void {
  // --- Entities -----------------------------------------------------------
  for (const e of ctx.queries.sprites) {
    const x = lerp(e.prev.x, e.position.x, alpha);
    const y = lerp(e.prev.y, e.position.y, alpha);
    const s = e.sprite;
    if (e.collider) {
      let vy = y + e.collider.oy + e.collider.h;
      const vx = x + e.collider.ox + e.collider.w / 2;
      // Collectibles bob gently.
      if (e.collectible && e.collectible.popVy <= 0 && e.ghost) {
        vy -= Math.sin(realTime * 3 + e.position.x * 0.15) * 1.5 + 1.5;
      }
      s.view.position.set(vx, vy);
    } else {
      // Decor sprites (torches): feet at bottom-center of their texture box.
      s.view.position.set(x + s.img.texture.width / 2, y + s.img.texture.height);
    }
  }

  // --- Camera + trauma shake --------------------------------------------
  const cam = ctx.camera;
  const camX = lerp(cam.prevX, cam.x, alpha);
  const camY = lerp(cam.prevY, cam.y, alpha);
  const shake = cam.trauma * cam.trauma; // trauma², so small trauma barely shakes
  const shakeX = shake * CAMERA.MAX_SHAKE_PX * noise1(realTime);
  const shakeY = shake * CAMERA.MAX_SHAKE_PX * noise2(realTime);
  const roll = shake * CAMERA.MAX_SHAKE_ROLL * noise1(realTime * 1.31);

  // Pivot trick: the camera container rotates/centers around the view point.
  const world = ctx.layers.camera;
  world.pivot.set(camX + shakeX, camY + shakeY);
  world.position.set(VIEW_W / 2, VIEW_H / 2);
  world.rotation = roll;

  // --- Parallax (multipliers 0 / 0.2 / 0.5 / 1.0) -------------------------
  const originX = camX - VIEW_W / 2;
  const originY = camY - VIEW_H / 2;
  ctx.layers.parallaxFar.position.set(-originX * 0.2, -originY * 0.1);
  ctx.layers.parallaxNear.position.set(-originX * 0.5, -originY * 0.25);

  return;
}

/** Screen-space position of a world point under the current camera (no roll). */
export function worldToScreen(
  ctx: Ctx,
  wx: number,
  wy: number,
  alpha: number,
): { x: number; y: number } {
  const cam = ctx.camera;
  const camX = lerp(cam.prevX, cam.x, alpha);
  const camY = lerp(cam.prevY, cam.y, alpha);
  return { x: wx - camX + VIEW_W / 2, y: wy - camY + VIEW_H / 2 };
}
