import { TILE } from "../constants";

/**
 * A faithful subset of the LDtk JSON schema (https://ldtk.io/json/):
 * levels contain layerInstances; an IntGrid layer carries collision tiles as
 * `intGridCsv`, an Entities layer carries entity instances with px coords and
 * fieldInstances. The loader consumes ONLY this JSON shape — you could export
 * a real .ldtk project and feed its levels straight in.
 */

export interface LDtkField {
  __identifier: string;
  __type: string;
  __value: unknown;
}

export interface LDtkEntity {
  __identifier: string;
  __grid: [number, number];
  px: [number, number];
  width: number;
  height: number;
  fieldInstances: LDtkField[];
}

export interface LDtkLayer {
  __identifier: string;
  __type: "IntGrid" | "Entities";
  __cWid: number;
  __cHei: number;
  __gridSize: number;
  intGridCsv: number[];
  entityInstances: LDtkEntity[];
}

export interface LDtkLevel {
  identifier: string;
  iid: string;
  pxWid: number;
  pxHei: number;
  fieldInstances: LDtkField[];
  layerInstances: LDtkLayer[];
}

export type LevelTheme = "overworld" | "cave" | "castle";

/** IntGrid values used by the Collision layer. */
export const enum GridTile {
  Empty = 0,
  Ground = 1,
  Brick = 2,
  QuestionCoin = 3,
  QuestionMushroom = 4,
  Used = 5,
  Stone = 6,
  Spike = 7,
  Pipe = 8,
  InvisibleWall = 9,
}

export function isSolid(v: number): boolean {
  return v === GridTile.Ground || v === GridTile.Brick || v === GridTile.QuestionCoin ||
    v === GridTile.QuestionMushroom || v === GridTile.Used || v === GridTile.Stone ||
    v === GridTile.Pipe || v === GridTile.InvisibleWall;
}

export function isBumpable(v: number): boolean {
  return v === GridTile.Brick || v === GridTile.QuestionCoin || v === GridTile.QuestionMushroom;
}

// ---------------------------------------------------------------------------
// ASCII → LDtk builder (authoring convenience; output is plain LDtk JSON)
// ---------------------------------------------------------------------------

const TILE_CHARS: Record<string, GridTile> = {
  "#": GridTile.Ground,
  B: GridTile.Brick,
  "?": GridTile.QuestionCoin,
  M: GridTile.QuestionMushroom,
  S: GridTile.Stone,
  "^": GridTile.Spike,
  P: GridTile.Pipe,
  I: GridTile.InvisibleWall,
};

const ENTITY_CHARS: Record<string, string> = {
  p: "PlayerStart",
  w: "Walker",
  W: "Walker2", // tier 2 palette swap
  v: "Walker3", // tier 3
  f: "Flyer",
  F: "Flyer2",
  k: "ShellKicker",
  K: "ShellKicker2",
  c: "Coin",
  h: "Heart",
  C: "Checkpoint",
  m: "PlatformH",
  n: "PlatformV",
  X: "Boss",
  G: "Goal",
  D: "PipeWarp",
  L: "Torch",
};

export interface AsciiLevelSpec {
  identifier: string;
  theme: LevelTheme;
  rows: string[];
  /**
   * Optional field overrides per entity char, consumed in reading order
   * (top-left → bottom-right). E.g. { D: [{ target: 1 }] } gives the first
   * PipeWarp a `target` field of 1.
   */
  fields?: Partial<Record<string, Record<string, unknown>[]>>;
}

function toFieldInstances(obj: Record<string, unknown>): LDtkField[] {
  return Object.entries(obj).map(([k, v]) => ({
    __identifier: k,
    __type: typeof v === "number" ? "Int" : typeof v === "boolean" ? "Bool" : "String",
    __value: v,
  }));
}

let iidCounter = 0;

export function buildLDtkLevel(spec: AsciiLevelSpec): LDtkLevel {
  const cHei = spec.rows.length;
  const cWid = Math.max(...spec.rows.map((r) => r.length));
  const intGridCsv = new Array<number>(cWid * cHei).fill(0);
  const entities: LDtkEntity[] = [];
  const fieldCursor: Record<string, number> = {};

  for (let y = 0; y < cHei; y++) {
    const row = spec.rows[y]!;
    for (let x = 0; x < cWid; x++) {
      const ch = row[x] ?? " ";
      const tile = TILE_CHARS[ch];
      if (tile !== undefined) {
        intGridCsv[y * cWid + x] = tile;
        continue;
      }
      const id = ENTITY_CHARS[ch];
      if (id) {
        const idx = (fieldCursor[ch] = (fieldCursor[ch] ?? -1) + 1);
        const fields = spec.fields?.[ch]?.[idx] ?? {};
        entities.push({
          __identifier: id,
          __grid: [x, y],
          px: [x * TILE, y * TILE],
          width: TILE,
          height: TILE,
          fieldInstances: toFieldInstances(fields),
        });
      }
    }
  }

  return {
    identifier: spec.identifier,
    iid: `level-${iidCounter++}`,
    pxWid: cWid * TILE,
    pxHei: cHei * TILE,
    fieldInstances: toFieldInstances({ theme: spec.theme }),
    layerInstances: [
      {
        __identifier: "Entities",
        __type: "Entities",
        __cWid: cWid,
        __cHei: cHei,
        __gridSize: TILE,
        intGridCsv: [],
        entityInstances: entities,
      },
      {
        __identifier: "Collision",
        __type: "IntGrid",
        __cWid: cWid,
        __cHei: cHei,
        __gridSize: TILE,
        intGridCsv,
        entityInstances: [],
      },
    ],
  };
}

export function getLevelField<T>(level: LDtkLevel, name: string, fallback: T): T {
  const f = level.fieldInstances.find((x) => x.__identifier === name);
  return f ? (f.__value as T) : fallback;
}

export function getEntityField<T>(e: LDtkEntity, name: string, fallback: T): T {
  const f = e.fieldInstances.find((x) => x.__identifier === name);
  return f ? (f.__value as T) : fallback;
}

export function getLayer(level: LDtkLevel, id: string): LDtkLayer | undefined {
  return level.layerInstances.find((l) => l.__identifier === id);
}
