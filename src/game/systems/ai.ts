import { Sprite } from "pixi.js";
import { BOSS, ENEMY, HIT_STOP_STOMP_MS, TILE } from "../constants";
import type { Ctx } from "../context";
import type { Entity } from "../ecs/components";
import { isSolidAt } from "../level/loader";
import { spawnEnemy } from "../level/spawn";
import { useGameStore } from "@state/store";

const tierSpeed = (tier: number) => 1 + 0.35 * (tier - 1);

/** Finite-state machines for every enemy type. */
export function aiSystem(ctx: Ctx, dt: number): void {
  for (const e of ctx.queries.enemies) {
    const ai = e.enemyAI;
    ai.invuln = Math.max(0, ai.invuln - dt);
    switch (ai.kind) {
      case "walker":
        walkerAI(ctx, e as Required2<typeof e>, dt);
        break;
      case "flyer":
        flyerAI(ctx, e as Required2<typeof e>, dt);
        break;
      case "shellkicker":
        shellAI(ctx, e as Required2<typeof e>, dt);
        break;
      case "boss":
        bossAI(ctx, e as Required2<typeof e>, dt);
        break;
      case "projectile":
        projectileAI(ctx, e as Required2<typeof e>, dt);
        break;
    }
    // Cull anything that fell out of the level.
    if (e.position.y > ctx.level.pxHei + 64 && !e.dead) {
      ctx.world.addComponent(e, "dead", true);
    }
  }
}

type Required2<T> = T & Required<Pick<Entity, "position" | "velocity" | "collider" | "enemyAI" | "sprite">>;

function walkerAI(ctx: Ctx, e: Required2<Entity>, _dt: number): void {
  const ai = e.enemyAI;
  const speed = ENEMY.WALKER_SPEED * tierSpeed(ai.tier);
  if (ai.grounded && ai.turnAtEdges) {
    // Turn around before walking off a ledge.
    const frontX = ai.dir > 0 ? e.position.x + e.collider.w + 1 : e.position.x - 1;
    const tx = Math.floor(frontX / TILE);
    const ty = Math.floor((e.position.y + e.collider.h + 2) / TILE);
    if (!isSolidAt(ctx.level, tx, ty)) ai.dir *= -1;
  }
  e.velocity.x = ai.dir * speed;
  e.sprite.facing = ai.dir;
}

function flyerAI(ctx: Ctx, e: Required2<Entity>, _dt: number): void {
  const ai = e.enemyAI;
  const speed = ENEMY.FLYER_SPEED * tierSpeed(ai.tier);
  const patrol = 56;
  if (e.position.x < ai.anchor.x - patrol) ai.dir = 1;
  if (e.position.x > ai.anchor.x + patrol) ai.dir = -1;
  e.velocity.x = ai.dir * speed;
  // Sine hover around the anchor line, driven analytically for stability.
  const freq = 2.2 * (ai.tier >= 2 ? 1.4 : 1);
  e.velocity.y = Math.cos(ctx.time * freq + ai.anchor.x * 0.05) * ENEMY.FLYER_AMPLITUDE * freq * 0.5;
  e.sprite.facing = ai.dir;
}

function shellAI(ctx: Ctx, e: Required2<Entity>, dt: number): void {
  const ai = e.enemyAI;
  switch (ai.state) {
    case "walk":
      e.velocity.x = ai.dir * ENEMY.SHELL_WALK_SPEED * tierSpeed(ai.tier);
      e.sprite.facing = ai.dir;
      e.sprite.anim = "idle";
      break;
    case "shell-idle":
      e.velocity.x = 0;
      e.sprite.anim = "special";
      ai.timer -= dt;
      if (ai.timer <= 0) {
        ai.state = "waking";
        ai.timer = 1.2;
      }
      break;
    case "waking":
      e.velocity.x = 0;
      e.sprite.anim = "special";
      ai.timer -= dt;
      if (ai.timer <= 0) enterShellWalk(e);
      break;
    case "shell-moving":
      e.velocity.x = ai.dir * ENEMY.SHELL_KICK_SPEED;
      e.sprite.anim = "special";
      if (ai.hitWall) {
        ctx.particles.dust(e.position.x + e.collider.w / 2, e.position.y + e.collider.h, ai.dir, 5);
        ctx.addTrauma(0.08);
      }
      break;
    default:
      ai.state = "walk";
  }
}

export function enterShellIdle(e: Entity): void {
  const ai = e.enemyAI!;
  ai.state = "shell-idle";
  ai.timer = ENEMY.SHELL_WAKE_TIME;
  e.velocity!.x = 0;
  // Shrink to shell height.
  const col = e.collider!;
  e.position!.y += col.h - 11;
  col.h = 11;
}

export function enterShellWalk(e: Entity): void {
  const ai = e.enemyAI!;
  ai.state = "walk";
  const col = e.collider!;
  e.position!.y -= 15 - col.h;
  col.h = 15;
  e.sprite!.anim = "idle";
}

export function kickShell(ctx: Ctx, e: Entity, dir: number): void {
  const ai = e.enemyAI!;
  ai.state = "shell-moving";
  ai.dir = dir;
  ctx.hitStop(HIT_STOP_STOMP_MS * 0.6);
  ctx.addTrauma(0.18);
  ctx.particles.dust(e.position!.x + e.collider!.w / 2, e.position!.y + e.collider!.h, dir, 6);
}

// ---------------------------------------------------------------------------
// Projectiles (boss fireballs)
// ---------------------------------------------------------------------------
export function spawnFireball(ctx: Ctx, x: number, y: number, vx: number, vy: number): void {
  const img = new Sprite(ctx.textures.particleCircle);
  img.anchor.set(0.5, 1);
  img.tint = 0xf77622;
  img.scale.set(1.6);
  ctx.layers.entities.addChild(img);
  ctx.world.add({
    position: { x: x - 4, y: y - 8 },
    prev: { x: x - 4, y: y - 8 },
    velocity: { x: vx, y: vy },
    collider: { w: 8, h: 8, ox: 0, oy: 0 },
    ghost: true,
    gravity: true,
    sprite: {
      view: img,
      img,
      baseScale: 1.6,
      squashX: 1,
      squashY: 1,
      facing: 1,
      anim: "idle",
      animTime: 0,
      frames: { idle: [ctx.textures.particleCircle] },
      fps: 1,
    },
    enemyAI: {
      kind: "projectile",
      state: "patrol",
      tier: 1,
      dir: Math.sign(vx) || 1,
      timer: 3,
      anchor: { x, y },
      phase: 1,
      invuln: 0,
      turnAtEdges: false,
      hitWall: false,
      grounded: false,
      wasAirborne: false,
      seq: 0,
    },
  });
}

function projectileAI(ctx: Ctx, e: Required2<Entity>, dt: number): void {
  const ai = e.enemyAI;
  ai.timer -= dt;
  if (ai.timer <= 0) ctx.world.addComponent(e, "dead", true);
  // Fire trail
  if (Math.random() < 0.4) {
    ctx.particles.sparkle(e.position.x + 4, e.position.y + 4, 1, 0xf77622);
  }
}

// ---------------------------------------------------------------------------
// Boss — 3-phase FSM
// ---------------------------------------------------------------------------
function bossAI(ctx: Ctx, e: Required2<Entity>, dt: number): void {
  const ai = e.enemyAI;
  const hp = e.health?.hp ?? 0;
  const player = ctx.player;
  ai.phase = hp > 6 ? 1 : hp > 3 ? 2 : 3;
  const scale = ai.phase === 3 ? 1.5 : ai.phase === 2 ? 1.2 : 1;
  const center = e.position.x + e.collider.w / 2;
  const playerCenter = player?.position ? player.position.x + player.collider!.w / 2 : center;
  const toPlayer = Math.sign(playerCenter - center) || 1;

  switch (ai.state) {
    case "intro":
      e.velocity.x = 0;
      if (player?.position && Math.abs(playerCenter - center) < 150) {
        ai.state = "pace";
        ai.timer = 1.2;
        useGameStore.getState().setBossHp(hp, e.health?.max ?? BOSS.HP);
        ctx.addTrauma(0.35);
      }
      break;

    case "pace":
      ai.dir = toPlayer;
      e.sprite.facing = ai.dir;
      e.velocity.x = ai.dir * BOSS.PACE_SPEED * scale;
      ai.timer -= dt;
      if (ai.timer <= 0) {
        ai.state = "windup";
        ai.timer = ai.phase === 3 ? 0.3 : 0.5;
        e.sprite.squashX = 1.25;
        e.sprite.squashY = 0.75;
      }
      break;

    case "windup":
      e.velocity.x = 0;
      ai.timer -= dt;
      if (ai.timer <= 0) {
        ai.seq++;
        if (ai.phase === 1) {
          startJumpAttack(e, toPlayer, scale);
        } else if (ai.phase === 2) {
          if (ai.seq % 2 === 0) startCharge(e, toPlayer, scale);
          else ai.state = "summon";
          ai.timer = 0.8;
        } else {
          // Phase 3: enraged — mixes everything, biased to charges.
          if (ai.seq % 3 === 0) startJumpAttack(e, toPlayer, scale);
          else startCharge(e, toPlayer, scale);
        }
      }
      break;

    case "jump-attack":
      if (ai.grounded && ai.wasAirborne) {
        // Landing shockwave.
        const feetY = e.position.y + e.collider.h;
        ctx.particles.shockwave(center, feetY);
        ctx.addTrauma(0.55);
        ctx.hitStop(60);
        const n = ai.phase === 3 ? 4 : 2;
        for (let i = 0; i < n; i++) {
          const dir = i % 2 === 0 ? 1 : -1;
          const speed = 60 + 40 * Math.ceil((i + 1) / 2);
          spawnFireball(ctx, center, e.position.y + 8, dir * speed, -160);
        }
        e.sprite.squashX = 1.4;
        e.sprite.squashY = 0.65;
        ai.state = "pace";
        ai.timer = 1.5 / scale;
      }
      break;

    case "charge":
      e.velocity.x = ai.dir * (ai.phase === 3 ? BOSS.ENRAGE_SPEED : BOSS.CHARGE_SPEED * scale);
      e.sprite.facing = ai.dir;
      if (Math.random() < 0.3) {
        ctx.particles.dust(center - ai.dir * 10, e.position.y + e.collider.h, -ai.dir, 1);
      }
      if (ai.hitWall) {
        ai.state = "stunned";
        ai.timer = ai.phase === 3 ? 0.7 : 1.1;
        ctx.addTrauma(0.45);
        ctx.hitStop(50);
        ctx.particles.dust(center + ai.dir * 12, e.position.y + e.collider.h, -ai.dir, 10);
      }
      break;

    case "summon": {
      e.velocity.x = 0;
      ai.timer -= dt;
      if (ai.timer <= 0) {
        let minions = 0;
        for (const other of ctx.queries.enemies) {
          if (other.enemyAI.kind === "walker") minions++;
        }
        if (minions < 3) {
          for (const dir of [-1, 1]) {
            const m = spawnEnemy(ctx, "walker", 2, center + dir * 24, e.position.y + e.collider.h);
            if (m.enemyAI) m.enemyAI.dir = dir;
          }
          ctx.particles.poof(center, e.position.y + 16, 0x63c74d, 60);
        }
        ai.state = "pace";
        ai.timer = 1.3 / scale;
      }
      break;
    }

    case "stunned":
      e.velocity.x = 0;
      ai.timer -= dt;
      if (ai.timer <= 0) {
        ai.state = "pace";
        ai.timer = 1.0;
      }
      break;

    case "dying":
      e.velocity.x = 0;
      ai.timer -= dt;
      if (Math.random() < 0.3) {
        ctx.particles.poof(
          center + (Math.random() - 0.5) * 24,
          e.position.y + Math.random() * e.collider.h,
          0x63c74d,
          15,
        );
        ctx.addTrauma(0.1);
      }
      if (ai.timer <= 0) {
        // The big one: 600-particle death poof.
        ctx.particles.poof(center, e.position.y + e.collider.h / 2, 0x63c74d, 600);
        ctx.addTrauma(1);
        ctx.hitStop(140);
        ctx.world.addComponent(e, "dead", true);
        ctx.pendingComplete = true;
      }
      break;

    default:
      ai.state = "pace";
      ai.timer = 1;
  }
}

function startJumpAttack(e: Required2<Entity>, dir: number, scale: number): void {
  const ai = e.enemyAI;
  ai.state = "jump-attack";
  ai.dir = dir;
  e.velocity.y = -BOSS.JUMP_VELOCITY;
  e.velocity.x = dir * BOSS.CHARGE_SPEED * 0.6 * scale;
  e.sprite.squashX = 0.7;
  e.sprite.squashY = 1.35;
}

function startCharge(e: Required2<Entity>, dir: number, _scale: number): void {
  const ai = e.enemyAI;
  ai.state = "charge";
  ai.dir = dir;
  e.sprite.facing = dir;
}
