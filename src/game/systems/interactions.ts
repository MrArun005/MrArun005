import {
  HIT_STOP_BOSS_MS,
  HIT_STOP_HURT_MS,
  HIT_STOP_STOMP_MS,
  PLAYER,
  TILE,
} from "../constants";
import type { Ctx } from "../context";
import { aabbOverlap, type Entity } from "../ecs/components";
import { GridTile } from "../level/ldtk";
import { setTile, tileAt } from "../level/loader";
import { spawnCollectible } from "../level/spawn";
import { enterShellIdle, kickShell } from "./ai";
import { useGameStore } from "@state/store";

/**
 * All entity-entity gameplay: stomps, contact damage, shell kicks, pickups,
 * question blocks, checkpoints, pipes and the goal.
 */
export function interactionsSystem(ctx: Ctx, dt: number): void {
  processTileBumps(ctx);
  updateCollectibles(ctx, dt);

  const player = ctx.player;
  if (!player?.position || !player.playerControl) return;
  const pc = player.playerControl;

  if (pc.dead) {
    pc.deadTimer -= dt;
    if (pc.deadTimer <= 0) ctx.pendingRespawn = true;
    return;
  }

  pc.invuln = Math.max(0, pc.invuln - dt);

  // --- Environment hazards -------------------------------------------------
  if (player.position.y > ctx.level.pxHei + 40) {
    killPlayer(ctx);
    return;
  }
  if (touchesSpike(ctx, player)) {
    hurtPlayer(ctx);
    if (pc.dead) return;
  }

  // --- Enemies ----------------------------------------------------------
  for (const e of ctx.queries.enemies) {
    if (e.dead) continue;
    const ai = e.enemyAI;
    if (ai.state === "dying" || ai.state === "intro") continue;
    if (!aabbOverlap(player, e)) {
      // Shell-moving mows down other enemies even without touching the player.
      continue;
    }

    if (ai.kind === "projectile") {
      ctx.world.addComponent(e, "dead", true);
      ctx.particles.poof(e.position.x + 4, e.position.y + 4, 0xf77622, 25);
      hurtPlayer(ctx);
      if (pc.dead) return;
      continue;
    }

    const playerBottom = player.position.y + player.collider!.oy + player.collider!.h;
    const enemyTop = e.position.y + e.collider.oy;
    const falling = player.velocity!.y > 30;
    const isStomp = falling && playerBottom - enemyTop < e.collider.h * 0.6;

    if (isStomp) {
      stompEnemy(ctx, e);
      if (pc.dead) return;
    } else {
      // Side contact.
      if (ai.kind === "shellkicker" && ai.state === "shell-idle") {
        const dir = player.position.x + player.collider!.w / 2 < e.position.x + e.collider.w / 2 ? 1 : -1;
        kickShell(ctx, e, dir);
        useGameStore.getState().addScore(100);
      } else if (ai.kind === "shellkicker" && ai.state === "waking") {
        // Waking shells are harmless; nudging them re-idles them.
        enemyReIdle(e);
      } else {
        hurtPlayer(ctx);
        if (pc.dead) return;
      }
    }
  }

  shellVsEnemies(ctx);

  // --- Collectibles ------------------------------------------------------
  for (const e of ctx.queries.collectibles) {
    if (e.dead || e.collectible.popVy > 0) continue;
    if (!aabbOverlap(player, e)) continue;
    collect(ctx, e);
  }

  // --- Checkpoints ------------------------------------------------------
  for (const e of ctx.queries.checkpoints) {
    if (e.checkpoint.activated || !aabbOverlap(player, e)) continue;
    e.checkpoint.activated = true;
    ctx.activatedCheckpoints.add(e.checkpoint.id);
    if (e.sprite) e.sprite.img.texture = ctx.textures.checkpointOn;
    ctx.respawn = {
      x: e.position.x + 6,
      y: e.position.y + e.collider.h,
    };
    ctx.particles.sparkle(e.position.x + 6, e.position.y + 6, 14, 0x63c74d);
    useGameStore.getState().addScore(200);
    useGameStore.getState().setCheckpointHint("CHECKPOINT!");
    setTimeout(() => useGameStore.getState().setCheckpointHint(null), 1600);
  }

  // --- Goal ---------------------------------------------------------------
  for (const e of ctx.queries.goals) {
    if (aabbOverlap(player, e)) {
      ctx.particles.sparkle(e.position.x + 8, e.position.y + 12, 20);
      ctx.pendingComplete = true;
    }
  }

  // --- Pipe warps -----------------------------------------------------------
  if (pc.grounded && pc.warpCooldown <= 0 && ctx.input.isHeld("down")) {
    for (const e of ctx.queries.pipes) {
      if (!aabbOverlap(player, e)) continue;
      ctx.pendingWarp = e.pipe.targetLevel;
      pc.warpCooldown = 1;
      break;
    }
  }
}

// ---------------------------------------------------------------------------

function touchesSpike(ctx: Ctx, player: Entity): boolean {
  const col = player.collider!;
  const x0 = Math.floor((player.position!.x + col.ox) / TILE);
  const x1 = Math.floor((player.position!.x + col.ox + col.w - 0.01) / TILE);
  const y0 = Math.floor((player.position!.y + col.oy) / TILE);
  const y1 = Math.floor((player.position!.y + col.oy + col.h - 0.01) / TILE);
  for (let ty = y0; ty <= y1; ty++) {
    for (let tx = x0; tx <= x1; tx++) {
      if (tileAt(ctx.level, tx, ty) === GridTile.Spike) return true;
    }
  }
  return false;
}

function bouncePlayer(ctx: Ctx): void {
  const player = ctx.player!;
  const held = ctx.input.isHeld("jump");
  player.velocity!.y = -(held ? PLAYER.STOMP_BOUNCE_HELD : PLAYER.STOMP_BOUNCE);
  player.playerControl!.jumping = true;
  const s = player.sprite!;
  s.squashX = 0.75;
  s.squashY = 1.28;
}

function stompEnemy(ctx: Ctx, e: Entity): void {
  const ai = e.enemyAI!;
  const store = useGameStore.getState();
  const cx = e.position!.x + e.collider!.w / 2;
  const cy = e.position!.y + e.collider!.h / 2;

  switch (ai.kind) {
    case "walker":
    case "flyer": {
      ctx.world.addComponent(e, "dead", true);
      ctx.particles.poof(cx, cy, ai.kind === "flyer" ? 0xb55088 : 0xf77622, 90 + ai.tier * 40);
      store.addScore(ai.kind === "flyer" ? 200 : 100);
      ctx.hitStop(HIT_STOP_STOMP_MS);
      ctx.addTrauma(0.18);
      bouncePlayer(ctx);
      break;
    }
    case "shellkicker": {
      if (ai.state === "walk" || ai.state === "waking") {
        enterShellIdle(e);
        store.addScore(100);
      } else if (ai.state === "shell-idle") {
        const pcx = ctx.player!.position!.x + ctx.player!.collider!.w / 2;
        kickShell(ctx, e, pcx < cx ? 1 : -1);
        store.addScore(100);
      } else {
        // Moving shell: stop it.
        ai.state = "shell-idle";
        ai.timer = 6;
        e.velocity!.x = 0;
        store.addScore(200);
      }
      ctx.hitStop(HIT_STOP_STOMP_MS);
      ctx.addTrauma(0.15);
      bouncePlayer(ctx);
      break;
    }
    case "boss": {
      if (ai.invuln > 0) {
        bouncePlayer(ctx);
        break;
      }
      const health = e.health!;
      health.hp -= 1;
      ai.invuln = 1.2;
      useGameStore.getState().setBossHp(health.hp, health.max);
      useGameStore.getState().addScore(500);
      ctx.particles.poof(cx, e.position!.y, 0x63c74d, 80);
      ctx.hitStop(HIT_STOP_BOSS_MS);
      ctx.addTrauma(0.6);
      bouncePlayer(ctx);
      e.sprite!.squashX = 1.35;
      e.sprite!.squashY = 0.7;
      if (health.hp <= 0) {
        ai.state = "dying";
        ai.timer = 1.6;
        e.velocity!.x = 0;
      } else if (ai.state !== "stunned") {
        ai.state = "pace";
        ai.timer = 0.8;
      }
      break;
    }
    case "projectile":
      ctx.world.addComponent(e, "dead", true);
      ctx.particles.poof(cx, cy, 0xf77622, 20);
      bouncePlayer(ctx);
      break;
  }
}

function enemyReIdle(e: Entity): void {
  const ai = e.enemyAI!;
  ai.state = "shell-idle";
  ai.timer = 4;
}

/** A kicked shell wrecks everything in its path. */
function shellVsEnemies(ctx: Ctx): void {
  const store = useGameStore.getState();
  for (const shell of ctx.queries.enemies) {
    const sai = shell.enemyAI;
    if (sai.kind !== "shellkicker" || sai.state !== "shell-moving" || shell.dead) continue;
    for (const e of ctx.queries.enemies) {
      if (e === shell || e.dead) continue;
      const ai = e.enemyAI;
      if (ai.kind === "boss" || ai.kind === "projectile" || ai.state === "dying") continue;
      if (!aabbOverlap(shell, e)) continue;
      ctx.world.addComponent(e, "dead", true);
      ctx.particles.poof(
        e.position.x + e.collider.w / 2,
        e.position.y + e.collider.h / 2,
        0xffffff,
        120,
      );
      store.addScore(400);
      ctx.addTrauma(0.12);
    }
  }
}

function updateCollectibles(ctx: Ctx, dt: number): void {
  for (const e of ctx.queries.collectibles) {
    const c = e.collectible;
    if (c.popVy > 0) {
      // Rising out of a question block.
      const step = Math.min(c.popVy, 28 * dt);
      e.position.y -= step;
      c.popVy -= step;
      if (c.popVy <= 0 && c.kind === "mushroom") {
        // Mushrooms start sliding once they emerge.
        ctx.world.removeComponent(e, "ghost");
        ctx.world.addComponent(e, "gravity", true);
        e.velocity!.x = 32;
      }
    }
  }
}

function collect(ctx: Ctx, e: Entity): void {
  const store = useGameStore.getState();
  const cx = e.position!.x + e.collider!.w / 2;
  const cy = e.position!.y + e.collider!.h / 2;
  switch (e.collectible!.kind) {
    case "coin":
      store.addCoin();
      ctx.particles.coinBurst(cx, cy);
      break;
    case "mushroom":
      if ((ctx.player!.health?.hp ?? 1) < 2) growPlayer(ctx);
      else store.addScore(500);
      ctx.particles.sparkle(cx, cy, 12, 0xe43b44);
      break;
    case "heart":
      store.setLives(useGameStore.getState().lives + 1);
      ctx.particles.sparkle(cx, cy, 14, 0xf6757a);
      break;
  }
  ctx.world.addComponent(e, "dead", true);
}

// ---------------------------------------------------------------------------
// Player state changes
// ---------------------------------------------------------------------------
export function growPlayer(ctx: Ctx): void {
  const player = ctx.player!;
  const t = ctx.textures;
  player.health!.hp = 2;
  const col = player.collider!;
  const diff = PLAYER.BIG_HEIGHT - col.h;
  col.h = PLAYER.BIG_HEIGHT;
  player.position!.y -= diff;
  const s = player.sprite!;
  s.frames = {
    idle: t.playerBig.idle,
    run: t.playerBig.run,
    jump: t.playerBig.jump,
    fall: t.playerBig.fall,
  };
  s.squashX = 1.3;
  s.squashY = 0.75;
  useGameStore.getState().setPlayerHp(2);
}

function shrinkPlayer(ctx: Ctx): void {
  const player = ctx.player!;
  const t = ctx.textures;
  player.health!.hp = 1;
  const col = player.collider!;
  const diff = col.h - PLAYER.HEIGHT;
  col.h = PLAYER.HEIGHT;
  player.position!.y += diff;
  const s = player.sprite!;
  s.frames = {
    idle: t.player.idle,
    run: t.player.run,
    jump: t.player.jump,
    fall: t.player.fall,
  };
  useGameStore.getState().setPlayerHp(1);
}

export function hurtPlayer(ctx: Ctx): void {
  const player = ctx.player;
  if (!player?.playerControl) return;
  const pc = player.playerControl;
  if (pc.invuln > 0 || pc.dead) return;

  if ((player.health?.hp ?? 1) >= 2) {
    shrinkPlayer(ctx);
    pc.invuln = PLAYER.HURT_INVULN;
    ctx.hitStop(HIT_STOP_HURT_MS);
    ctx.addTrauma(0.45);
  } else {
    killPlayer(ctx);
  }
}

export function killPlayer(ctx: Ctx): void {
  const player = ctx.player;
  if (!player?.playerControl || player.playerControl.dead) return;
  const pc = player.playerControl;
  pc.dead = true;
  pc.deadTimer = 1.4;
  player.velocity!.x = 0;
  player.velocity!.y = -280; // classic death hop
  ctx.hitStop(HIT_STOP_HURT_MS);
  ctx.addTrauma(0.7);
  ctx.particles.poof(
    player.position!.x + player.collider!.w / 2,
    player.position!.y + player.collider!.h / 2,
    0xe43b44,
    60,
  );
  useGameStore.getState().loseLife();
}

// ---------------------------------------------------------------------------
// Question blocks & bricks
// ---------------------------------------------------------------------------
function processTileBumps(ctx: Ctx): void {
  const store = useGameStore.getState();
  for (const { tx, ty } of ctx.tileBumps) {
    const value = tileAt(ctx.level, tx, ty);
    const topX = tx * TILE + TILE / 2;
    const topY = ty * TILE;

    if (value === GridTile.QuestionCoin || value === GridTile.QuestionMushroom) {
      const sprite = setTile(ctx.level, tx, ty, GridTile.Used, ctx.textures);
      bumpSprite(ctx, sprite, ty);
      if (value === GridTile.QuestionCoin) {
        store.addCoin();
        ctx.particles.coinBurst(topX, topY - 6);
        ctx.particles.sparkle(topX, topY - 10, 6);
      } else {
        spawnCollectible(ctx, "mushroom", topX, topY, TILE);
        ctx.particles.sparkle(topX, topY - 6, 8, 0xe43b44);
      }
    } else if (value === GridTile.Brick) {
      if ((ctx.player?.health?.hp ?? 1) >= 2) {
        // Big player smashes bricks.
        setTile(ctx.level, tx, ty, GridTile.Empty, ctx.textures);
        ctx.particles.poof(topX, topY + 8, 0xb05a2c, 45);
        ctx.addTrauma(0.12);
        ctx.hitStop(30);
        store.addScore(50);
      } else {
        bumpSprite(ctx, ctx.level.tileSprites[ty * ctx.level.cWid + tx], ty);
      }
    }
  }
  ctx.tileBumps.length = 0;
}

function bumpSprite(ctx: Ctx, sprite: { y: number } | null | undefined, ty: number): void {
  if (!sprite) return;
  const baseY = ty * TILE;
  ctx.tweens.bump(0.16, (t) => {
    sprite.y = baseY - t * 5;
  }, () => {
    sprite.y = baseY;
  });
}
