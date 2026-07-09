import { PLAYER } from "../constants";
import type { Ctx } from "../context";

function moveToward(current: number, target: number, maxDelta: number): number {
  if (Math.abs(target - current) <= maxDelta) return target;
  return current + Math.sign(target - current) * maxDelta;
}

/**
 * Translates input intent into player velocity. Implements the feel
 * non-negotiables: coyote time, jump buffering and variable jump height
 * (asymmetric gravity lives in the physics system).
 */
export function inputSystem(ctx: Ctx, dt: number): void {
  const player = ctx.player;
  if (!player?.playerControl || !player.velocity || !player.sprite) return;
  const pc = player.playerControl;
  const v = player.velocity;
  const input = ctx.input;

  if (pc.dead) return;

  pc.warpCooldown = Math.max(0, pc.warpCooldown - dt);

  const axis = input.axisX();
  const running = input.isHeld("run");
  const targetSpeed = axis * (running ? PLAYER.SPRINT_SPEED : PLAYER.RUN_SPEED);
  const accel = !pc.grounded
    ? PLAYER.AIR_ACCEL
    : axis !== 0 && Math.sign(axis) !== Math.sign(v.x) && v.x !== 0
      ? PLAYER.DECEL
      : axis === 0
        ? PLAYER.DECEL
        : PLAYER.ACCEL;
  const prevVx = v.x;
  v.x = moveToward(v.x, targetSpeed, accel * dt);

  if (axis !== 0) {
    // Skid dust on hard direction changes.
    if (pc.grounded && Math.sign(axis) !== Math.sign(prevVx) && Math.abs(prevVx) > 60) {
      ctx.particles.dust(
        player.position!.x + player.collider!.w / 2,
        player.position!.y + player.collider!.h,
        -Math.sign(prevVx),
        4,
      );
    }
    player.sprite.facing = axis;
  }

  // --- Coyote time -----------------------------------------------------
  if (pc.grounded) pc.coyoteTimer = PLAYER.COYOTE_TIME;
  else pc.coyoteTimer = Math.max(0, pc.coyoteTimer - dt);

  // --- Jump buffer -------------------------------------------------------
  if (input.justPressed("jump")) pc.jumpBufferTimer = PLAYER.JUMP_BUFFER;
  else pc.jumpBufferTimer = Math.max(0, pc.jumpBufferTimer - dt);

  if (pc.jumpBufferTimer > 0 && pc.coyoteTimer > 0) {
    pc.jumpBufferTimer = 0;
    pc.coyoteTimer = 0;
    pc.grounded = false;
    pc.ridingPlatform = null;
    pc.jumping = true;
    v.y = -PLAYER.JUMP_VELOCITY;
    // Stretch on takeoff.
    player.sprite.squashX = 0.72;
    player.sprite.squashY = 1.3;
    ctx.particles.jumpPuff(
      player.position!.x + player.collider!.w / 2,
      player.position!.y + player.collider!.h,
    );
  }

  // --- Variable jump height ---------------------------------------------
  if (pc.jumping && !input.isHeld("jump") && v.y < -PLAYER.JUMP_CUT_VELOCITY) {
    v.y = -PLAYER.JUMP_CUT_VELOCITY;
  }
  if (v.y >= 0) pc.jumping = false;
}
