import { PLAYER } from "../constants";
import type { Ctx } from "../context";

/**
 * Render-time animation: squash/stretch decay, frame selection/stepping,
 * facing flips and invulnerability blinking. Purely visual — runs on render
 * frames, frozen during hit-stop.
 */
export function animationSystem(ctx: Ctx, dt: number): void {
  const decay = Math.min(1, 9 * dt);

  for (const e of ctx.queries.sprites) {
    const s = e.sprite;

    // Squash/stretch springs back to 1.
    s.squashX += (1 - s.squashX) * decay;
    s.squashY += (1 - s.squashY) * decay;

    // --- Pick the animation --------------------------------------------
    let rate = 1;
    if (e.playerControl) {
      const pc = e.playerControl;
      const vx = Math.abs(e.velocity?.x ?? 0);
      if (pc.dead) {
        s.anim = "jump";
        s.img.rotation += 6 * dt;
      } else {
        s.img.rotation = 0;
        if (!pc.grounded) s.anim = (e.velocity?.y ?? 0) < 0 ? "jump" : "fall";
        else if (vx > 8) {
          s.anim = "run";
          rate = Math.max(0.5, vx / PLAYER.RUN_SPEED);
        } else s.anim = "idle";
      }
    } else if (e.enemyAI?.kind === "boss") {
      s.anim = "idle";
    }
    // (Shell-kickers set their own anim in the AI; collectibles just cycle.)

    // --- Step frames ------------------------------------------------------
    s.animTime += dt * rate;
    const frames = s.frames[s.anim] ?? s.frames.idle;
    if (frames && frames.length > 0) {
      const idx = Math.floor(s.animTime * s.fps) % frames.length;
      const tex = frames[idx]!;
      if (s.img.texture !== tex) s.img.texture = tex;
    }

    // --- Facing & squash into scale ------------------------------------
    s.view.scale.set(s.baseScale * s.squashX * s.facing, s.baseScale * s.squashY);

    // --- Blink while invulnerable ----------------------------------------
    const invuln = e.playerControl?.invuln ?? e.enemyAI?.invuln ?? 0;
    if (invuln > 0) {
      s.img.alpha = Math.sin(ctx.time * 40) > 0 ? 0.35 : 0.9;
    } else if (s.img.alpha !== 1) {
      s.img.alpha = 1;
    }

    // Boss rage tint in phase 3.
    if (e.enemyAI?.kind === "boss") {
      const phase = e.enemyAI.phase;
      s.img.tint = phase === 3 ? 0xffb0a0 : phase === 2 ? 0xffe0c0 : 0xffffff;
    }
  }
}
