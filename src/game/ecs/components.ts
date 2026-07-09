import type { Container, Sprite, Texture } from "pixi.js";

export interface Vec2 {
  x: number;
  y: number;
}

/** AABB collider. `ox/oy` offset the box from the entity position (top-left of box). */
export interface Collider {
  w: number;
  h: number;
  ox: number;
  oy: number;
}

export type AnimName = "idle" | "run" | "jump" | "fall" | "hurt" | "special";

export interface SpriteComp {
  /** Root display object, positioned at the collider's bottom-center (feet). */
  view: Container;
  /** The texture-bearing sprite inside `view` (animation swaps its texture). */
  img: Sprite;
  /** Base scale before squash/stretch (pixel-art sprites are authored at 1:1). */
  baseScale: number;
  /** Squash/stretch multipliers, tweened back to 1 by the animation system. */
  squashX: number;
  squashY: number;
  /** -1 or 1; multiplied into scale.x. */
  facing: number;
  anim: AnimName;
  animTime: number;
  /** Per-anim frame textures, resolved by the animation system. */
  frames: Partial<Record<AnimName, Texture[]>>;
  fps: number;
}

export interface PlayerControl {
  coyoteTimer: number;
  jumpBufferTimer: number;
  jumping: boolean; // currently in a player-initiated jump (for variable height)
  grounded: boolean;
  wasGrounded: boolean;
  runFrames: number;
  /** Entity id of the moving platform we stand on, for carry velocity. */
  ridingPlatform: Entity | null;
  invuln: number;
  dead: boolean;
  deadTimer: number;
  warpCooldown: number;
}

export type EnemyKind = "walker" | "flyer" | "shellkicker" | "boss" | "projectile";

export type EnemyState =
  // walker / generic
  | "patrol"
  // flyer
  | "hover"
  | "swoop"
  // shell-kicker
  | "walk"
  | "shell-idle"
  | "shell-moving"
  | "waking"
  // boss
  | "intro"
  | "pace"
  | "windup"
  | "jump-attack"
  | "charge"
  | "summon"
  | "stunned"
  | "dying";

export interface EnemyAI {
  kind: EnemyKind;
  state: EnemyState;
  /** Palette tier: 1 = base colors, 2/3 = palette-swapped variants (faster/tougher). */
  tier: number;
  dir: number;
  timer: number;
  /** Anchor for flyers (sine hover) and boss arena logic. */
  anchor: Vec2;
  phase: number; // boss phase 1..3
  invuln: number;
  turnAtEdges: boolean;
  /** Set by the physics system each tick. */
  hitWall: boolean;
  grounded: boolean;
  /** Airborne last tick — lets the boss detect landings. */
  wasAirborne: boolean;
  /** Attack sequence counter (boss alternates charge/summon with this). */
  seq: number;
}

export interface Health {
  hp: number;
  max: number;
}

export type CollectibleKind = "coin" | "mushroom" | "heart";

export interface Collectible {
  kind: CollectibleKind;
  /** Pop animation when spawned from a question block. */
  popVy: number;
  sparkleTimer: number;
}

export interface MovingPlatform {
  origin: Vec2;
  axis: "x" | "y";
  range: number; // px of travel from origin (one direction)
  speed: number; // px/s
  t: number; // phase accumulator
  /** Velocity applied this tick — used to carry the player. */
  carry: Vec2;
}

export interface PipeWarp {
  /** Level index to warp to, or -1 for "warp within level" to targetSpawn. */
  targetLevel: number;
  targetSpawn: string | null;
  id: string;
}

export interface CheckpointComp {
  id: string;
  activated: boolean;
}

export interface Entity {
  position?: Vec2;
  /** Position at the previous fixed tick — render interpolates prev→position. */
  prev?: Vec2;
  velocity?: Vec2;
  collider?: Collider;
  sprite?: SpriteComp;
  playerControl?: PlayerControl;
  enemyAI?: EnemyAI;
  health?: Health;
  collectible?: Collectible;
  platform?: MovingPlatform;
  pipe?: PipeWarp;
  checkpoint?: CheckpointComp;
  goal?: true;
  /** Marked for removal at the end of the tick. */
  dead?: true;
  /** Ignores tile collision (flyers, projectiles, pop-ups). */
  ghost?: true;
  gravity?: true;
  /** Light halo in cave levels: radius in px. */
  light?: { radius: number; color: number; flicker: number };
}

export const aabbLeft = (e: Entity): number => e.position!.x + e.collider!.ox;
export const aabbTop = (e: Entity): number => e.position!.y + e.collider!.oy;
export const aabbRight = (e: Entity): number => aabbLeft(e) + e.collider!.w;
export const aabbBottom = (e: Entity): number => aabbTop(e) + e.collider!.h;

export function aabbOverlap(a: Entity, b: Entity): boolean {
  return (
    aabbLeft(a) < aabbRight(b) &&
    aabbRight(a) > aabbLeft(b) &&
    aabbTop(a) < aabbBottom(b) &&
    aabbBottom(a) > aabbTop(b)
  );
}
