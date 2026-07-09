import { PLAYER } from "../constants";
import type { Ctx } from "../context";

/**
 * Moving platforms are kinematic: they follow a cosine path and carry the
 * player by applying their per-tick delta after the player's own physics.
 */
export function platformSystem(ctx: Ctx, dt: number): void {
  const player = ctx.player;

  for (const e of ctx.queries.platforms) {
    const p = e.platform;
    p.t += dt;
    // One full round trip covers 2*range at average `speed` px/s.
    const omega = (Math.PI * p.speed) / p.range;
    const offset = (p.range / 2) * (1 - Math.cos(p.t * omega));
    const nx = p.axis === "x" ? p.origin.x + offset : p.origin.x;
    const ny = p.axis === "y" ? p.origin.y + offset : p.origin.y;
    p.carry.x = nx - e.position.x;
    p.carry.y = ny - e.position.y;
    e.position.x = nx;
    e.position.y = ny;

    if (!player?.position || !player.collider || !player.playerControl || player.playerControl.dead) continue;
    const pc = player.playerControl;
    const pcol = player.collider;
    const px0 = player.position.x + pcol.ox;
    const px1 = px0 + pcol.w;
    const bottom = player.position.y + pcol.oy + pcol.h;
    const top = e.position.y + e.collider.oy;
    const ex0 = e.position.x + e.collider.ox;
    const ex1 = ex0 + e.collider.w;

    const overlapX = px1 > ex0 + 1 && px0 < ex1 - 1;
    const nearTop = bottom - top >= -4 && bottom - top <= 9;
    if (overlapX && nearTop && player.velocity!.y >= 0) {
      // Ride: snap feet to the platform and carry its motion.
      player.position.x += p.carry.x;
      player.position.y = top - pcol.h - pcol.oy;
      player.velocity!.y = 0;
      if (!pc.grounded) {
        pc.coyoteTimer = PLAYER.COYOTE_TIME;
      }
      pc.grounded = true;
      pc.ridingPlatform = e;
    } else if (pc.ridingPlatform === e) {
      pc.ridingPlatform = null;
    }
  }
}
