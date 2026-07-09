/** Simulation runs at a fixed 60 Hz; rendering interpolates between ticks. */
export const FIXED_STEP = 1 / 60;
/** Max frame time fed to the accumulator — avoids the spiral of death after tab-switches. */
export const MAX_FRAME_MS = 100;

export const TILE = 16;

/** Virtual viewport in world pixels; the stage is scaled up to fill the window. */
export const VIEW_W = 480;
export const VIEW_H = 270;

// ---------------------------------------------------------------------------
// Player movement tuning (units: world px, seconds)
// ---------------------------------------------------------------------------
export const PLAYER = {
  RUN_SPEED: 130,
  SPRINT_SPEED: 185,
  ACCEL: 1500,
  DECEL: 1800,
  AIR_ACCEL: 1100,
  JUMP_VELOCITY: 342, // ≈ 3.8 tiles of height with GRAVITY_UP
  GRAVITY_UP: 1500,
  /** Falling gravity is asymmetric — 1.6x — so jumps feel snappy, not floaty. */
  GRAVITY_DOWN: 1500 * 1.6,
  MAX_FALL: 460,
  /** Releasing jump early clamps upward velocity to this — variable jump height. */
  JUMP_CUT_VELOCITY: 110,
  /** Grace period after walking off a ledge during which jump still works. */
  COYOTE_TIME: 0.1, // 100 ms
  /** Pressing jump slightly before landing still triggers the jump. */
  JUMP_BUFFER: 0.12, // 120 ms
  /** Bumping a ceiling within this many px of its edge nudges the player around it. */
  CORNER_CORRECTION: 5,
  STOMP_BOUNCE: 240,
  STOMP_BOUNCE_HELD: 340,
  HURT_INVULN: 1.6,
  WIDTH: 12,
  HEIGHT: 14,
  BIG_HEIGHT: 19,
} as const;

// ---------------------------------------------------------------------------
// Juice
// ---------------------------------------------------------------------------
export const HIT_STOP_STOMP_MS = 60;
export const HIT_STOP_HURT_MS = 90;
export const HIT_STOP_BOSS_MS = 120;

export const CAMERA = {
  DEADZONE_W: 40,
  DEADZONE_H: 32,
  LOOKAHEAD_X: 36,
  LOOKAHEAD_FALL: 40,
  LOOKAHEAD_LERP: 3.5, // 1/s exponential smoothing rate
  MAX_SHAKE_PX: 9,
  MAX_SHAKE_ROLL: 0.03, // radians
  TRAUMA_DECAY: 1.4, // per second
} as const;

export const ENEMY = {
  WALKER_SPEED: 34,
  FLYER_SPEED: 46,
  FLYER_AMPLITUDE: 28,
  SHELL_WALK_SPEED: 28,
  SHELL_KICK_SPEED: 260,
  SHELL_WAKE_TIME: 6,
} as const;

export const BOSS = {
  HP: 9,
  CONTACT_DAMAGE: 1,
  PACE_SPEED: 40,
  CHARGE_SPEED: 150,
  ENRAGE_SPEED: 210,
  JUMP_VELOCITY: 380,
  STOMPED_INVULN: 1.2,
} as const;

export const Z = {
  SKY: 0,
  PARALLAX_FAR: 1,
  PARALLAX_NEAR: 2,
  WORLD: 3,
  PARTICLES_BACK: 4,
  ENTITIES: 5,
  PLAYER: 6,
  PARTICLES_FRONT: 7,
  LIGHTING: 8,
  DEBUG: 9,
} as const;
