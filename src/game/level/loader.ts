import { Container, Sprite, Texture } from "pixi.js";
import type { GameTextures } from "../gfx/textures";
import { TILE } from "../constants";
import {
  GridTile,
  getLayer,
  getLevelField,
  isSolid,
  type LDtkEntity,
  type LDtkLevel,
  type LevelTheme,
} from "./ldtk";

export interface LoadedLevel {
  ldtk: LDtkLevel;
  theme: LevelTheme;
  cWid: number;
  cHei: number;
  pxWid: number;
  pxHei: number;
  /** Mutable collision grid (question blocks turn into used blocks, etc). */
  grid: Uint8Array;
  tilemap: Container;
  tileSprites: (Sprite | null)[];
  entities: LDtkEntity[];
}

export function tileAt(level: LoadedLevel, tx: number, ty: number): number {
  if (tx < 0 || tx >= level.cWid) return GridTile.Ground; // side walls are solid
  if (ty < 0) return GridTile.Empty; // open sky
  if (ty >= level.cHei) return GridTile.Empty; // open pit (falling = death)
  return level.grid[ty * level.cWid + tx]!;
}

export function isSolidAt(level: LoadedLevel, tx: number, ty: number): boolean {
  return isSolid(tileAt(level, tx, ty));
}

function textureFor(level: LoadedLevel, tx: number, ty: number, tex: GameTextures): Texture | null {
  const v = tileAt(level, tx, ty);
  const t = tex.tiles;
  switch (v) {
    case GridTile.Ground: {
      const openAbove = !isSolidAt(level, tx, ty - 1);
      return openAbove ? t.groundTop! : t.ground!;
    }
    case GridTile.Brick:
      return t.brick!;
    case GridTile.QuestionCoin:
    case GridTile.QuestionMushroom:
      return t.question!;
    case GridTile.Used:
      return t.used!;
    case GridTile.Stone:
      return t.stone!;
    case GridTile.Spike:
      return t.spike!;
    case GridTile.Pipe: {
      const leftIsPipe = tileAt(level, tx - 1, ty) === GridTile.Pipe;
      const aboveIsPipe = tileAt(level, tx, ty - 1) === GridTile.Pipe;
      if (!aboveIsPipe) return leftIsPipe ? t.pipeTR! : t.pipeTL!;
      return leftIsPipe ? t.pipeBR! : t.pipeBL!;
    }
    case GridTile.InvisibleWall:
      return null;
    default:
      return null;
  }
}

export function loadLevel(ldtk: LDtkLevel, tex: GameTextures): LoadedLevel {
  const collision = getLayer(ldtk, "Collision");
  const entitiesLayer = getLayer(ldtk, "Entities");
  if (!collision) throw new Error(`Level ${ldtk.identifier} has no Collision IntGrid layer`);

  const level: LoadedLevel = {
    ldtk,
    theme: getLevelField<LevelTheme>(ldtk, "theme", "overworld"),
    cWid: collision.__cWid,
    cHei: collision.__cHei,
    pxWid: ldtk.pxWid,
    pxHei: ldtk.pxHei,
    grid: Uint8Array.from(collision.intGridCsv),
    tilemap: new Container(),
    tileSprites: new Array(collision.__cWid * collision.__cHei).fill(null),
    entities: entitiesLayer?.entityInstances ?? [],
  };

  for (let ty = 0; ty < level.cHei; ty++) {
    for (let tx = 0; tx < level.cWid; tx++) {
      const texture = textureFor(level, tx, ty, tex);
      if (!texture) continue;
      const s = new Sprite(texture);
      s.position.set(tx * TILE, ty * TILE);
      level.tilemap.addChild(s);
      level.tileSprites[ty * level.cWid + tx] = s;
    }
  }
  // Cull off-screen tile sprites cheaply: Pixi handles it, but grouping the
  // tilemap as a cacheable render group helps the WebGPU batcher.
  level.tilemap.isRenderGroup = true;
  return level;
}

/** Mutate a tile (e.g. question → used) and refresh its sprite. */
export function setTile(
  level: LoadedLevel,
  tx: number,
  ty: number,
  value: GridTile,
  tex: GameTextures,
): Sprite | null {
  if (tx < 0 || tx >= level.cWid || ty < 0 || ty >= level.cHei) return null;
  const idx = ty * level.cWid + tx;
  level.grid[idx] = value;
  let sprite = level.tileSprites[idx];
  const texture = textureFor(level, tx, ty, tex);
  if (!texture) {
    if (sprite) {
      sprite.destroy();
      level.tileSprites[idx] = null;
    }
    return null;
  }
  if (!sprite) {
    sprite = new Sprite(texture);
    sprite.position.set(tx * TILE, ty * TILE);
    level.tilemap.addChild(sprite);
    level.tileSprites[idx] = sprite;
  } else {
    sprite.texture = texture;
  }
  return sprite;
}

export function destroyLevel(level: LoadedLevel): void {
  level.tilemap.destroy({ children: true });
}
