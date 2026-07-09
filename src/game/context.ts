import type { Container, Filter, Graphics } from "pixi.js";
import type { World } from "miniplex";
import type { Entity } from "./ecs/components";
import type { Queries } from "./ecs/world";
import type { InputManager } from "./input/InputManager";
import type { GameTextures } from "./gfx/textures";
import type { LoadedLevel } from "./level/loader";
import type { ParticleFX } from "./fx/particles";
import type { TweenManager } from "./fx/tweens";
import type { LightingLayer } from "./fx/lighting";

export interface CameraState {
  x: number;
  y: number;
  prevX: number;
  prevY: number;
  /** Smoothed horizontal lookahead offset. */
  lookX: number;
  lookY: number;
  /** 0..1; shake magnitude is trauma² (trauma-based screen shake). */
  trauma: number;
}

export interface Layers {
  /** Screen-fixed backdrop (gradient, stars). Parallax multiplier 0. */
  sky: Container;
  /** Parallax multiplier 0.2. */
  parallaxFar: Container;
  /** Parallax multiplier 0.5. */
  parallaxNear: Container;
  /** World container translated by -camera (multiplier 1.0). */
  camera: Container;
  /** Inside camera: platforms/pipes decor behind entities. */
  back: Container;
  /** Inside camera: collectibles — has the bloom filter. */
  glow: Container;
  /** Inside camera: enemies, player. */
  entities: Container;
  /** Screen-fixed debug overlay graphics (hitboxes). */
  debug: Graphics;
}

/**
 * Everything a system needs. Systems are plain functions `(ctx, dt) => void`
 * — no classes, no events, just data in the world plus this bag of services.
 */
export interface Ctx {
  world: World<Entity>;
  queries: Queries;
  input: InputManager;
  textures: GameTextures;
  tierFilters: Record<number, Filter>;
  level: LoadedLevel;
  layers: Layers;
  particles: ParticleFX;
  tweens: TweenManager;
  lighting: LightingLayer;
  camera: CameraState;
  player: Entity | null;
  /** Simulated time in seconds (advances only on fixed ticks). */
  time: number;

  /** Tiles head-bumped by the player this tick (question blocks, bricks). */
  tileBumps: Array<{ tx: number; ty: number }>;

  // Commands consumed by Game at the end of the tick ------------------------
  pendingWarp: number | null;
  pendingRespawn: boolean;
  pendingComplete: boolean;
  /** Where the player respawns after death (updated by checkpoints). */
  respawn: { x: number; y: number };
  /** Checkpoint ids already hit this run — survive respawns, reset on new runs. */
  activatedCheckpoints: Set<string>;

  addTrauma(amount: number): void;
  hitStop(ms: number): void;
}

export type System = (ctx: Ctx, dt: number) => void;
