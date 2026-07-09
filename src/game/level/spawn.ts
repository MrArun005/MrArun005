import { Sprite, type Texture } from "pixi.js";
import { BOSS, ENEMY, PLAYER, TILE } from "../constants";
import type { Ctx } from "../context";
import type { CollectibleKind, Entity, EnemyKind, SpriteComp } from "../ecs/components";
import { getEntityField, type LDtkEntity } from "./ldtk";

export type SpawnDeps = Pick<
  Ctx,
  "world" | "textures" | "tierFilters" | "layers" | "level" | "lighting"
>;

function makeSpriteComp(
  frames: SpriteComp["frames"],
  fps = 8,
): SpriteComp {
  const first = frames.idle?.[0] ?? Object.values(frames)[0]?.[0];
  const img = new Sprite(first);
  img.anchor.set(0.5, 1); // feet-anchored: squash/stretch pivots at the ground
  return {
    view: img,
    img,
    baseScale: 1,
    squashX: 1,
    squashY: 1,
    facing: 1,
    anim: "idle",
    animTime: 0,
    frames,
    fps,
  };
}

function applyTier(deps: SpawnDeps, sprite: SpriteComp, tier: number): void {
  const filter = deps.tierFilters[tier];
  if (tier >= 2 && filter) sprite.img.filters = [filter];
}

/** Feet position for a 1-cell LDtk entity: bottom-center of its cell. */
function feetOf(e: LDtkEntity): { x: number; y: number } {
  return { x: e.px[0] + TILE / 2, y: e.px[1] + TILE };
}

export function spawnPlayer(deps: SpawnDeps, x: number, y: number): Entity {
  const t = deps.textures;
  const sprite = makeSpriteComp(
    { idle: t.player.idle, run: t.player.run, jump: t.player.jump, fall: t.player.fall },
    10,
  );
  deps.layers.entities.addChild(sprite.view);
  const w = PLAYER.WIDTH;
  const h = PLAYER.HEIGHT;
  const entity = deps.world.add({
    position: { x: x - w / 2, y: y - h },
    prev: { x: x - w / 2, y: y - h },
    velocity: { x: 0, y: 0 },
    collider: { w, h, ox: 0, oy: 0 },
    gravity: true,
    sprite,
    health: { hp: 1, max: 2 },
    playerControl: {
      coyoteTimer: 0,
      jumpBufferTimer: 0,
      jumping: false,
      grounded: false,
      wasGrounded: false,
      runFrames: 0,
      ridingPlatform: null,
      invuln: 0,
      dead: false,
      deadTimer: 0,
      warpCooldown: 0,
    },
    ...(deps.level.theme === "cave" ? { light: { radius: 64, color: 0xffffff, flicker: 0.05 } } : {}),
  });
  return entity;
}

export function spawnEnemy(
  deps: SpawnDeps,
  kind: EnemyKind,
  tier: number,
  x: number,
  y: number,
): Entity {
  const t = deps.textures;
  let frames: SpriteComp["frames"];
  let w: number, h: number;
  let fps = 6;
  switch (kind) {
    case "flyer":
      frames = { idle: t.flyer };
      w = 14;
      h = 11;
      fps = 8;
      break;
    case "shellkicker":
      frames = { idle: t.shellkicker, special: t.shell };
      w = 12;
      h = 15;
      break;
    case "boss":
      frames = { idle: t.boss };
      w = 26;
      h = 28;
      break;
    default:
      frames = { idle: t.walker };
      w = 14;
      h = 13;
  }
  const sprite = makeSpriteComp(frames, fps);
  applyTier(deps, sprite, tier);
  deps.layers.entities.addChild(sprite.view);

  const isFlyer = kind === "flyer";
  const entity = deps.world.add({
    position: { x: x - w / 2, y: y - h },
    prev: { x: x - w / 2, y: y - h },
    velocity: { x: 0, y: 0 },
    collider: { w, h, ox: 0, oy: 0 },
    sprite,
    enemyAI: {
      kind,
      state: kind === "boss" ? "intro" : kind === "flyer" ? "hover" : kind === "shellkicker" ? "walk" : "patrol",
      tier,
      dir: -1,
      timer: 0,
      anchor: { x: x - w / 2, y: y - h },
      phase: 1,
      invuln: 0,
      turnAtEdges: kind === "walker",
      hitWall: false,
      grounded: false,
      wasAirborne: false,
      seq: 0,
    },
    ...(isFlyer ? { ghost: true as const } : { gravity: true as const }),
    ...(kind === "boss" ? { health: { hp: BOSS.HP, max: BOSS.HP } } : {}),
  });
  // Tiered enemies start faster; speed applied in the AI system via tier.
  void ENEMY;
  return entity;
}

export function spawnCollectible(
  deps: SpawnDeps,
  kind: CollectibleKind,
  x: number,
  y: number,
  popVy = 0,
): Entity {
  const t = deps.textures;
  const frames: SpriteComp["frames"] =
    kind === "coin" ? { idle: t.coin } : kind === "mushroom" ? { idle: [t.mushroom] } : { idle: [t.heart] };
  const sprite = makeSpriteComp(frames, 4);
  deps.layers.glow.addChild(sprite.view);
  const w = kind === "coin" ? 10 : 13;
  const h = kind === "coin" ? 12 : 10;
  return deps.world.add({
    position: { x: x - w / 2, y: y - h },
    prev: { x: x - w / 2, y: y - h },
    velocity: { x: 0, y: 0 },
    collider: { w, h, ox: 0, oy: 0 },
    ghost: true,
    sprite,
    collectible: { kind, popVy, sparkleTimer: Math.random() },
    ...(deps.level.theme === "cave" ? { light: { radius: 22, color: 0xffe98a, flicker: 0.1 } } : {}),
  });
}

function texSprite(tex: Texture): SpriteComp {
  return makeSpriteComp({ idle: [tex] }, 1);
}

/** Populate the world from the level's LDtk Entities layer. */
export function spawnLevelEntities(deps: SpawnDeps): {
  player: Entity;
  spawnPoint: { x: number; y: number };
  hasBoss: boolean;
} {
  let player: Entity | null = null;
  let spawnPoint = { x: 48, y: 200 };
  let hasBoss = false;
  const { world, textures: t, layers, level } = deps;

  for (const e of level.entities) {
    const feet = feetOf(e);
    switch (e.__identifier) {
      case "PlayerStart":
        spawnPoint = feet;
        break;
      case "Walker":
      case "Walker2":
      case "Walker3":
        spawnEnemy(deps, "walker", Number(e.__identifier.slice(6) || 1), feet.x, feet.y);
        break;
      case "Flyer":
      case "Flyer2":
        spawnEnemy(deps, "flyer", e.__identifier === "Flyer2" ? 2 : 1, feet.x, feet.y);
        break;
      case "ShellKicker":
      case "ShellKicker2":
        spawnEnemy(deps, "shellkicker", e.__identifier === "ShellKicker2" ? 2 : 1, feet.x, feet.y);
        break;
      case "Boss":
        spawnEnemy(deps, "boss", 3, feet.x, feet.y);
        hasBoss = true;
        break;
      case "Coin":
        spawnCollectible(deps, "coin", feet.x, feet.y);
        break;
      case "Heart":
        spawnCollectible(deps, "heart", feet.x, feet.y);
        break;
      case "Checkpoint": {
        const sprite = texSprite(t.checkpointOff);
        layers.back.addChild(sprite.view);
        world.add({
          position: { x: feet.x - 6, y: feet.y - 28 },
          prev: { x: feet.x - 6, y: feet.y - 28 },
          collider: { w: 12, h: 28, ox: 0, oy: 0 },
          sprite,
          checkpoint: { id: `${e.px[0]},${e.px[1]}`, activated: false },
        } as Entity);
        break;
      }
      case "Goal": {
        const sprite = texSprite(t.goal);
        layers.back.addChild(sprite.view);
        world.add({
          position: { x: feet.x - 8, y: feet.y - 48 },
          prev: { x: feet.x - 8, y: feet.y - 48 },
          collider: { w: 16, h: 48, ox: 0, oy: 0 },
          sprite,
          goal: true,
        });
        break;
      }
      case "PlatformH":
      case "PlatformV": {
        const sprite = texSprite(t.platform);
        layers.back.addChild(sprite.view);
        const axis = getEntityField<string>(e, "axis", e.__identifier === "PlatformV" ? "y" : "x") as "x" | "y";
        const px = { x: e.px[0], y: e.px[1] + TILE - 8 };
        world.add({
          position: { ...px },
          prev: { ...px },
          velocity: { x: 0, y: 0 },
          collider: { w: 48, h: 8, ox: 0, oy: 0 },
          sprite,
          platform: {
            origin: { ...px },
            axis,
            range: getEntityField<number>(e, "range", 48),
            speed: getEntityField<number>(e, "speed", 36),
            t: 0,
            carry: { x: 0, y: 0 },
          },
        });
        break;
      }
      case "PipeWarp": {
        world.add({
          position: { x: e.px[0], y: e.px[1] },
          prev: { x: e.px[0], y: e.px[1] },
          collider: { w: 32, h: 16, ox: 0, oy: 0 },
          pipe: {
            targetLevel: getEntityField<number>(e, "target", -1),
            targetSpawn: getEntityField<string | null>(e, "spawn", null),
            id: `${e.px[0]},${e.px[1]}`,
          },
        });
        break;
      }
      case "Torch": {
        const sprite = texSprite(t.torch);
        layers.back.addChild(sprite.view);
        world.add({
          position: { x: feet.x - 3, y: feet.y - 12 },
          prev: { x: feet.x - 3, y: feet.y - 12 },
          sprite,
          light: { radius: 72, color: 0xffb060, flicker: 0.15 },
        } as Entity);
        break;
      }
    }
  }

  player = spawnPlayer(deps, spawnPoint.x, spawnPoint.y);
  return { player, spawnPoint, hasBoss };
}
