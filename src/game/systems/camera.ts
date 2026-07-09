import { CAMERA, VIEW_H, VIEW_W } from "../constants";
import type { Ctx } from "../context";

const clamp = (v: number, lo: number, hi: number) => (lo > hi ? (lo + hi) / 2 : Math.min(hi, Math.max(lo, v)));

/**
 * Fixed-step camera: deadzone box + velocity-facing lookahead + trauma decay.
 * The render pass interpolates prev→current and layers shake on top.
 */
export function cameraSystem(ctx: Ctx, dt: number): void {
  const cam = ctx.camera;
  cam.prevX = cam.x;
  cam.prevY = cam.y;
  cam.trauma = Math.max(0, cam.trauma - CAMERA.TRAUMA_DECAY * dt);

  const player = ctx.player;
  if (!player?.position || !player.collider || !player.sprite) return;

  const cx = player.position.x + player.collider.ox + player.collider.w / 2;
  const cy = player.position.y + player.collider.oy + player.collider.h / 2;

  // Lookahead: bias toward where the player is heading.
  const lookTargetX = player.sprite.facing * CAMERA.LOOKAHEAD_X;
  const lookTargetY = (player.velocity?.y ?? 0) > 180 ? CAMERA.LOOKAHEAD_FALL : 0;
  const k = Math.min(1, CAMERA.LOOKAHEAD_LERP * dt);
  cam.lookX += (lookTargetX - cam.lookX) * k;
  cam.lookY += (lookTargetY - cam.lookY) * k;

  const desiredX = cx + cam.lookX;
  const desiredY = cy + cam.lookY - 12;

  // Deadzone: only move the camera when the target escapes the box.
  const dzx = CAMERA.DEADZONE_W / 2;
  const dzy = CAMERA.DEADZONE_H / 2;
  const dx = desiredX - cam.x;
  const dy = desiredY - cam.y;
  if (dx > dzx) cam.x += dx - dzx;
  else if (dx < -dzx) cam.x += dx + dzx;
  if (dy > dzy) cam.y += dy - dzy;
  else if (dy < -dzy) cam.y += dy + dzy;

  cam.x = clamp(cam.x, VIEW_W / 2, ctx.level.pxWid - VIEW_W / 2);
  cam.y = clamp(cam.y, VIEW_H / 2, ctx.level.pxHei - VIEW_H / 2);
}

/** Snap the camera to the player (level start / respawn). */
export function snapCamera(ctx: Ctx): void {
  const cam = ctx.camera;
  const player = ctx.player;
  if (!player?.position || !player.collider) return;
  cam.x = clamp(
    player.position.x + player.collider.w / 2,
    VIEW_W / 2,
    ctx.level.pxWid - VIEW_W / 2,
  );
  cam.y = clamp(
    player.position.y + player.collider.h / 2 - 12,
    VIEW_H / 2,
    ctx.level.pxHei - VIEW_H / 2,
  );
  cam.prevX = cam.x;
  cam.prevY = cam.y;
  cam.lookX = 0;
  cam.lookY = 0;
}
