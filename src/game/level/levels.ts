import type { LDtkLevel } from "./ldtk";
import level1 from "./data/level-1.json";
import level2 from "./data/level-2.json";
import level3 from "./data/level-3.json";

/**
 * Sample levels ship as LDtk-schema JSON (see scripts/generate-levels.mjs to
 * re-author them). Any level exported from a real LDtk project with a
 * "Collision" IntGrid layer + "Entities" layer will load the same way.
 */
export const LEVELS: LDtkLevel[] = [
  level1 as unknown as LDtkLevel,
  level2 as unknown as LDtkLevel,
  level3 as unknown as LDtkLevel,
];

export const LEVEL_NAMES = LEVELS.map((l) => l.identifier.replace(/_/g, " "));
