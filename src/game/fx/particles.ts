import { Particle, ParticleContainer, Texture } from "pixi.js";
import type { GameTextures } from "../gfx/textures";

interface Sim {
  p: Particle;
  vx: number;
  vy: number;
  gravity: number;
  drag: number;
  life: number;
  maxLife: number;
  startScale: number;
  endScale: number;
  startAlpha: number;
  twinkle: number; // >0: alpha oscillates at this frequency
  spin: number;
  front: boolean;
}

const MAX_PARTICLES = 4000;

/**
 * GPU particle emitters built on Pixi v8 ParticleContainer — position, scale,
 * rotation and color are dynamic properties uploaded to the GPU each frame,
 * so thousands of quads render in a single draw call per container.
 */
export class ParticleFX {
  readonly back: ParticleContainer;
  readonly front: ParticleContainer;
  private sims: Sim[] = [];

  constructor(private tex: GameTextures) {
    const opts = {
      dynamicProperties: { position: true, scale: true, rotation: true, color: true },
    };
    this.back = new ParticleContainer(opts);
    this.front = new ParticleContainer(opts);
  }

  get count(): number {
    return this.sims.length;
  }

  private spawn(opts: {
    texture: Texture;
    x: number;
    y: number;
    vx: number;
    vy: number;
    life: number;
    tint?: number;
    gravity?: number;
    drag?: number;
    startScale?: number;
    endScale?: number;
    alpha?: number;
    twinkle?: number;
    spin?: number;
    front?: boolean;
  }): void {
    if (this.sims.length >= MAX_PARTICLES) return;
    const p = new Particle({
      texture: opts.texture,
      x: opts.x,
      y: opts.y,
      anchorX: 0.5,
      anchorY: 0.5,
      scaleX: opts.startScale ?? 1,
      scaleY: opts.startScale ?? 1,
      tint: opts.tint ?? 0xffffff,
      alpha: opts.alpha ?? 1,
    });
    const front = opts.front ?? true;
    (front ? this.front : this.back).addParticle(p);
    this.sims.push({
      p,
      vx: opts.vx,
      vy: opts.vy,
      gravity: opts.gravity ?? 0,
      drag: opts.drag ?? 0,
      life: opts.life,
      maxLife: opts.life,
      startScale: opts.startScale ?? 1,
      endScale: opts.endScale ?? opts.startScale ?? 1,
      startAlpha: opts.alpha ?? 1,
      twinkle: opts.twinkle ?? 0,
      spin: opts.spin ?? 0,
      front,
    });
  }

  /** Ground dust: landing, direction changes, shell skids. */
  dust(x: number, y: number, dir: number, count = 6): void {
    for (let i = 0; i < count; i++) {
      this.spawn({
        texture: this.tex.particleCircle,
        x: x + (Math.random() - 0.5) * 6,
        y: y - Math.random() * 3,
        vx: dir * (10 + Math.random() * 30) + (Math.random() - 0.5) * 20,
        vy: -(10 + Math.random() * 25),
        gravity: 60,
        drag: 3,
        life: 0.3 + Math.random() * 0.25,
        tint: 0xc8b7a0,
        startScale: 0.7 + Math.random() * 0.6,
        endScale: 0.1,
        alpha: 0.8,
        front: false,
      });
    }
  }

  /** Ambient glint on collectibles + pickup bursts. */
  sparkle(x: number, y: number, count = 1, tint = 0xffe98a): void {
    for (let i = 0; i < count; i++) {
      this.spawn({
        texture: this.tex.particleStar,
        x: x + (Math.random() - 0.5) * 12,
        y: y + (Math.random() - 0.5) * 12,
        vx: (Math.random() - 0.5) * 14,
        vy: -8 - Math.random() * 18,
        life: 0.4 + Math.random() * 0.4,
        tint,
        startScale: 0.5 + Math.random() * 0.7,
        endScale: 0,
        twinkle: 18,
        spin: (Math.random() - 0.5) * 6,
      });
    }
  }

  coinBurst(x: number, y: number): void {
    this.sparkle(x, y, 10);
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      this.spawn({
        texture: this.tex.particleSquare,
        x,
        y,
        vx: Math.cos(a) * 55,
        vy: Math.sin(a) * 55 - 25,
        gravity: 220,
        life: 0.45,
        tint: 0xfee761,
        startScale: 1,
        endScale: 0.2,
      });
    }
  }

  /**
   * Death poof — the big one. 500+ particles on boss death, a couple hundred
   * for regular enemies; a ring shockwave plus a filled burst.
   */
  poof(x: number, y: number, tint: number, count = 220): void {
    for (let i = 0; i < count; i++) {
      const ring = i % 3 === 0;
      const a = Math.random() * Math.PI * 2;
      const speed = ring ? 120 + Math.random() * 60 : Math.random() * 150;
      this.spawn({
        texture: i % 2 ? this.tex.particleSquare : this.tex.particleCircle,
        x: x + (Math.random() - 0.5) * 8,
        y: y + (Math.random() - 0.5) * 8,
        vx: Math.cos(a) * speed,
        vy: Math.sin(a) * speed - 30,
        gravity: ring ? 40 : 180,
        drag: ring ? 2.5 : 0.8,
        life: 0.5 + Math.random() * 0.7,
        tint: Math.random() < 0.25 ? 0xffffff : tint,
        startScale: 0.6 + Math.random() * 1.2,
        endScale: 0,
        spin: (Math.random() - 0.5) * 10,
      });
    }
  }

  /** Boss shockwave: a fast horizontal dust wave along the ground. */
  shockwave(x: number, y: number): void {
    for (let dir = -1; dir <= 1; dir += 2) {
      for (let i = 0; i < 30; i++) {
        this.spawn({
          texture: this.tex.particleCircle,
          x: x + dir * i * 2,
          y: y - Math.random() * 4,
          vx: dir * (90 + Math.random() * 120),
          vy: -(20 + Math.random() * 50),
          gravity: 320,
          drag: 1.5,
          life: 0.4 + Math.random() * 0.4,
          tint: 0xb0a080,
          startScale: 0.8 + Math.random(),
          endScale: 0.1,
          alpha: 0.9,
        });
      }
    }
  }

  jumpPuff(x: number, y: number): void {
    this.dust(x, y, 0, 4);
  }

  update(dt: number): void {
    if (dt <= 0) return;
    for (let i = this.sims.length - 1; i >= 0; i--) {
      const s = this.sims[i]!;
      s.life -= dt;
      if (s.life <= 0) {
        (s.front ? this.front : this.back).removeParticle(s.p);
        this.sims.splice(i, 1);
        continue;
      }
      const t = 1 - s.life / s.maxLife;
      s.vy += s.gravity * dt;
      if (s.drag > 0) {
        const f = Math.max(0, 1 - s.drag * dt);
        s.vx *= f;
        s.vy *= f;
      }
      s.p.x += s.vx * dt;
      s.p.y += s.vy * dt;
      const sc = s.startScale + (s.endScale - s.startScale) * t;
      s.p.scaleX = sc;
      s.p.scaleY = sc;
      s.p.rotation += s.spin * dt;
      let alpha = s.startAlpha * (s.life < 0.2 ? s.life / 0.2 : 1);
      if (s.twinkle > 0) alpha *= 0.6 + 0.4 * Math.sin(s.life * s.twinkle);
      s.p.alpha = alpha;
    }
  }

  clear(): void {
    for (const s of this.sims) (s.front ? this.front : this.back).removeParticle(s.p);
    this.sims = [];
  }
}
