import { AlphaFilter, Container, Graphics, Sprite, Texture } from "pixi.js";

/**
 * Dynamic 2D lighting for the cave level.
 *
 * Technique: a screen-sized black rectangle is drawn into an intermediate
 * texture (forced by an AlphaFilter on the container), and light sprites with
 * `erase` blend mode punch soft holes into it. Additive glow sprites sit in a
 * separate world-space container for the warm halo around torches and pickups.
 */
export class LightingLayer {
  /** Screen-fixed darkness overlay (add to the root, above the world). */
  readonly darkness: Container;
  /** World-space additive glows (add inside the camera container). */
  readonly glows: Container;

  private darkRect: Graphics;
  private holePool: Sprite[] = [];
  private holesUsed = 0;
  private lightTexture: Texture;
  private enabled = false;

  constructor(lightTexture: Texture) {
    this.lightTexture = lightTexture;
    this.darkness = new Container();
    // The AlphaFilter forces the darkness container into its own render
    // texture, so 'erase' blending only cuts the black rect — not the scene.
    const filter = new AlphaFilter({ alpha: 0.94 });
    this.darkness.filters = [filter];
    this.darkRect = new Graphics();
    this.darkness.addChild(this.darkRect);
    this.glows = new Container();
    this.setEnabled(false);
  }

  setEnabled(on: boolean): void {
    this.enabled = on;
    this.darkness.visible = on;
    this.glows.visible = on;
  }

  get isEnabled(): boolean {
    return this.enabled;
  }

  resize(w: number, h: number): void {
    this.darkRect.clear().rect(-32, -32, w + 64, h + 64).fill(0x000000);
  }

  /** Begin a lighting frame: subsequent addLight calls position the holes. */
  begin(): void {
    this.holesUsed = 0;
  }

  /** @param x,y screen-space center; radius in screen px. */
  addLight(x: number, y: number, radius: number, flicker = 0): void {
    if (!this.enabled) return;
    let hole = this.holePool[this.holesUsed];
    if (!hole) {
      hole = new Sprite(this.lightTexture);
      hole.anchor.set(0.5);
      hole.blendMode = "erase";
      this.holePool.push(hole);
      this.darkness.addChild(hole);
    }
    const size = radius * 2 * (1 + flicker);
    hole.visible = true;
    hole.position.set(x, y);
    hole.width = size;
    hole.height = size;
    this.holesUsed++;
  }

  /** Hide unused pooled holes. Call after all addLight calls for the frame. */
  end(): void {
    for (let i = this.holesUsed; i < this.holePool.length; i++) {
      this.holePool[i]!.visible = false;
    }
  }

  /** Create a warm additive glow sprite in world space (torches, goal). */
  createGlow(x: number, y: number, radius: number, color: number, alpha = 0.35): Sprite {
    const glow = new Sprite(this.lightTexture);
    glow.anchor.set(0.5);
    glow.blendMode = "add";
    glow.tint = color;
    glow.alpha = alpha;
    glow.position.set(x, y);
    glow.width = radius * 2;
    glow.height = radius * 2;
    this.glows.addChild(glow);
    return glow;
  }

  clearGlows(): void {
    this.glows.removeChildren();
  }
}
