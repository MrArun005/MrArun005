import { PLAYER, TILE } from "../constants";
import type { Ctx } from "../context";
import type { Entity } from "../ecs/components";
import { isBumpable } from "../level/ldtk";
import { isSolidAt } from "../level/loader";

const ENEMY_GRAVITY = 1900;
const ENEMY_MAX_FALL = 420;

/**
 * Fixed-step integration + swept tile AABB collision.
 * Player extras: asymmetric gravity (1.6x falling), corner correction when
 * clipping a ceiling edge, and head-bump reporting for question blocks.
 */
export function physicsSystem(ctx: Ctx, dt: number): void {
  const level = ctx.level;

  for (const e of ctx.queries.moving) {
    const v = e.velocity;
    const pc = e.playerControl;

    // --- Gravity ---------------------------------------------------------
    if (e.gravity) {
      if (pc) {
        const g = v.y < 0 ? PLAYER.GRAVITY_UP : PLAYER.GRAVITY_DOWN;
        v.y = Math.min(v.y + g * dt, PLAYER.MAX_FALL);
      } else {
        v.y = Math.min(v.y + ENEMY_GRAVITY * dt, ENEMY_MAX_FALL);
      }
    }

    // Ghosts (flyers, projectiles, popping collectibles, dead player) skip
    // tile collision entirely.
    if (e.ghost || (pc && pc.dead) || !e.collider) {
      e.position.x += v.x * dt;
      e.position.y += v.y * dt;
      continue;
    }

    const col = e.collider;
    const ai = e.enemyAI;
    if (ai) {
      ai.hitWall = false;
      ai.wasAirborne = !ai.grounded;
      ai.grounded = false;
    }

    // --- Horizontal sweep --------------------------------------------------
    e.position.x += v.x * dt;
    if (v.x !== 0) {
      const dir = Math.sign(v.x);
      const edgeX = dir > 0 ? e.position.x + col.ox + col.w : e.position.x + col.ox;
      const tx = Math.floor(edgeX / TILE);
      const ty0 = Math.floor((e.position.y + col.oy) / TILE);
      const ty1 = Math.floor((e.position.y + col.oy + col.h - 0.01) / TILE);
      let blocked = false;
      for (let ty = ty0; ty <= ty1; ty++) {
        if (isSolidAt(level, tx, ty)) {
          blocked = true;
          break;
        }
      }
      if (blocked) {
        e.position.x = dir > 0 ? tx * TILE - col.w - col.ox : (tx + 1) * TILE - col.ox;
        v.x = dir > 0 ? Math.min(0, v.x) : Math.max(0, v.x);
        if (ai) {
          ai.hitWall = true;
          ai.dir *= -1;
        } else if (e.collectible) {
          // Mushrooms bounce off walls like slow walkers.
          v.x = -dir * Math.abs(v.x || 30);
        }
      }
    }

    // --- Vertical sweep ------------------------------------------------------
    e.position.y += v.y * dt;
    if (v.y > 0) {
      // Falling: land on solids.
      const bottom = e.position.y + col.oy + col.h;
      const ty = Math.floor(bottom / TILE);
      const tx0 = Math.floor((e.position.x + col.ox) / TILE);
      const tx1 = Math.floor((e.position.x + col.ox + col.w - 0.01) / TILE);
      let landed = false;
      for (let tx = tx0; tx <= tx1; tx++) {
        if (isSolidAt(level, tx, ty)) {
          landed = true;
          break;
        }
      }
      if (landed) {
        e.position.y = ty * TILE - col.h - col.oy;
        v.y = 0;
        if (pc) {
          if (!pc.grounded) landPlayer(ctx, e);
          pc.grounded = true;
        }
        if (ai) ai.grounded = true;
      } else if (pc) {
        pc.grounded = false;
        pc.ridingPlatform = null;
      }
    } else if (v.y < 0) {
      if (pc) pc.grounded = false;
      const top = e.position.y + col.oy;
      const ty = Math.floor(top / TILE);
      const tx0 = Math.floor((e.position.x + col.ox) / TILE);
      const tx1 = Math.floor((e.position.x + col.ox + col.w - 0.01) / TILE);
      const hits: number[] = [];
      for (let tx = tx0; tx <= tx1; tx++) {
        if (isSolidAt(level, tx, ty)) hits.push(tx);
      }
      if (hits.length > 0) {
        // --- Corner correction: nudge sideways around a ceiling edge -------
        if (pc && hits.length === 1) {
          const tx = hits[0]!;
          const left = e.position.x + col.ox;
          const right = left + col.w;
          const tileL = tx * TILE;
          const tileR = tileL + TILE;
          const overlapL = right - tileL; // we poke the tile from its left
          const overlapR = tileR - left; // we poke the tile from its right
          if (overlapL <= PLAYER.CORNER_CORRECTION && !isSolidAt(level, tx - 1, ty)) {
            e.position.x -= overlapL + 0.01;
            continue; // keep rising
          }
          if (overlapR <= PLAYER.CORNER_CORRECTION && !isSolidAt(level, tx + 1, ty)) {
            e.position.x += overlapR + 0.01;
            continue;
          }
        }
        e.position.y = (ty + 1) * TILE - col.oy;
        v.y = 0;
        if (pc) {
          // Head bump: report the tile most overlapped by the player's head.
          const centerX = e.position.x + col.ox + col.w / 2;
          let best = hits[0]!;
          let bestDist = Infinity;
          for (const tx of hits) {
            const d = Math.abs(tx * TILE + TILE / 2 - centerX);
            if (d < bestDist) {
              bestDist = d;
              best = tx;
            }
          }
          const value = level.grid[ty * level.cWid + best]!;
          if (isBumpable(value)) ctx.tileBumps.push({ tx: best, ty });
        }
      }
    }
  }
}

function landPlayer(ctx: Ctx, e: Entity): void {
  const sprite = e.sprite;
  const impact = Math.min(1, Math.abs(e.velocity!.y) / PLAYER.MAX_FALL);
  if (sprite) {
    // Squash on landing, scaled by impact speed.
    sprite.squashX = 1 + 0.35 * impact;
    sprite.squashY = 1 - 0.32 * impact;
  }
  ctx.particles.dust(
    e.position!.x + e.collider!.w / 2,
    e.position!.y + e.collider!.h,
    0,
    Math.round(3 + impact * 5),
  );
}
