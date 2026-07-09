import { CAMERA, TILE } from "../constants";
import type { Ctx } from "../context";
import { GridTile } from "../level/ldtk";

/**
 * F1 debug overlay: hitboxes for every collider, spike tiles, the camera
 * deadzone, and light radii. Drawn in world space inside the camera container
 * so it lines up with interpolated rendering. Stats (FPS, entity count) are
 * pushed to the zustand store and rendered by React.
 */
export function debugSystem(ctx: Ctx, enabled: boolean): void {
  const g = ctx.layers.debug;
  g.clear();
  if (!enabled) return;

  for (const e of ctx.queries.colliders) {
    const { x, y } = e.position;
    const c = e.collider;
    const color = e.playerControl
      ? 0x2ce8f5
      : e.enemyAI
        ? 0xe43b44
        : e.collectible
          ? 0xfee761
          : e.platform
            ? 0x63c74d
            : 0xffffff;
    g.rect(x + c.ox, y + c.oy, c.w, c.h).stroke({ color, width: 0.5, alpha: 0.9 });
  }

  // Spike tiles
  const lvl = ctx.level;
  for (let ty = 0; ty < lvl.cHei; ty++) {
    for (let tx = 0; tx < lvl.cWid; tx++) {
      if (lvl.grid[ty * lvl.cWid + tx] === GridTile.Spike) {
        g.rect(tx * TILE, ty * TILE, TILE, TILE).stroke({ color: 0xf77622, width: 0.5, alpha: 0.5 });
      }
    }
  }

  // Camera deadzone box
  g.rect(
    ctx.camera.x - CAMERA.DEADZONE_W / 2,
    ctx.camera.y - CAMERA.DEADZONE_H / 2,
    CAMERA.DEADZONE_W,
    CAMERA.DEADZONE_H,
  ).stroke({ color: 0xb55088, width: 0.5, alpha: 0.7 });

  // Light radii
  for (const e of ctx.queries.lights) {
    g.circle(e.position.x + 6, e.position.y + 6, e.light.radius).stroke({
      color: 0xffe98a,
      width: 0.5,
      alpha: 0.35,
    });
  }
}
