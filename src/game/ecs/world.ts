import { World } from "miniplex";
import type { Entity } from "./components";

/**
 * The miniplex world plus pre-built archetype queries. Queries are created
 * once here — miniplex caches them, but keeping them in one place documents
 * every system's data dependencies.
 */
export function createWorld() {
  const world = new World<Entity>();

  const queries = {
    /** Everything that simulates: copy prev ← position at tick start. */
    simulated: world.with("position", "prev"),
    moving: world.with("position", "velocity"),
    withGravity: world.with("position", "velocity", "gravity"),
    colliders: world.with("position", "collider"),
    players: world.with("position", "velocity", "collider", "playerControl", "sprite", "health"),
    enemies: world.with("position", "velocity", "collider", "enemyAI", "sprite"),
    collectibles: world.with("position", "collider", "collectible", "sprite"),
    platforms: world.with("position", "collider", "platform"),
    pipes: world.with("position", "collider", "pipe"),
    checkpoints: world.with("position", "collider", "checkpoint"),
    goals: world.with("position", "collider", "goal"),
    sprites: world.with("position", "prev", "sprite"),
    lights: world.with("position", "light"),
    dead: world.with("dead"),
  };

  return { world, queries };
}

export type GameWorld = ReturnType<typeof createWorld>;
export type Queries = GameWorld["queries"];
export type { Entity };
