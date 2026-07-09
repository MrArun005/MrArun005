import { Application, Container, Graphics } from "pixi.js";
import { AdvancedBloomFilter, CRTFilter } from "pixi-filters";
import { FIXED_STEP, MAX_FRAME_MS, VIEW_H, VIEW_W } from "./constants";
import type { Ctx } from "./context";
import { createWorld } from "./ecs/world";
import { getTextures } from "./gfx/textures";
import { buildParallax } from "./gfx/parallax";
import { InputManager } from "./input/InputManager";
import { LEVELS } from "./level/levels";
import { destroyLevel, loadLevel } from "./level/loader";
import { spawnLevelEntities } from "./level/spawn";
import { LightingLayer } from "./fx/lighting";
import { ParticleFX } from "./fx/particles";
import { createTierFilters, createVignetteFilter } from "./fx/shaders";
import { TweenManager } from "./fx/tweens";
import { aiSystem } from "./systems/ai";
import { animationSystem } from "./systems/animation";
import { cameraSystem, snapCamera } from "./systems/camera";
import { debugSystem } from "./systems/debug";
import { inputSystem } from "./systems/input";
import { interactionsSystem } from "./systems/interactions";
import { physicsSystem } from "./systems/physics";
import { platformSystem } from "./systems/platforms";
import { renderSystem, worldToScreen } from "./systems/render";
import { useGameStore } from "@state/store";

/**
 * Orchestrates the whole game: Pixi app (WebGPU-first), fixed-timestep
 * simulation decoupled from rendering, level lifecycle, post-processing and
 * the zustand bridge. React never touches anything in here per-frame.
 */
export class Game {
  readonly app: Application;
  readonly input = new InputManager();
  readonly ctx: Ctx;

  private viewport = new Container();
  private accumulator = 0;
  private lastAlpha = 0;
  private hitStopMs = 0;
  private realTime = 0;
  private levelIndex = 0;
  private fpsSmooth = 60;
  private tickMsSmooth = 0;
  private statsTimer = 0;
  private crtFilter: CRTFilter;
  private vignette = createVignetteFilter();

  private constructor(app: Application) {
    this.app = app;
    const textures = getTextures();
    const { world, queries } = createWorld();
    const lighting = new LightingLayer(textures.light);
    const particles = new ParticleFX(textures);

    const layers = {
      sky: new Container(),
      parallaxFar: new Container(),
      parallaxNear: new Container(),
      camera: new Container(),
      back: new Container(),
      glow: new Container(),
      entities: new Container(),
      debug: new Graphics(),
    };

    this.crtFilter = new CRTFilter({
      curvature: 2,
      lineWidth: 2,
      lineContrast: 0.18,
      noise: 0.08,
      noiseSize: 1,
      vignetting: 0, // our own vignette filter handles this
    });

    const game = this;
    this.ctx = {
      world,
      queries,
      input: this.input,
      textures,
      tierFilters: createTierFilters(),
      // Replaced on the first loadLevel; never read before then.
      level: null as unknown as Ctx["level"],
      layers,
      particles,
      tweens: new TweenManager(),
      lighting,
      camera: { x: 0, y: 0, prevX: 0, prevY: 0, lookX: 0, lookY: 0, trauma: 0 },
      player: null,
      time: 0,
      tileBumps: [],
      pendingWarp: null,
      pendingRespawn: false,
      pendingComplete: false,
      respawn: { x: 48, y: 200 },
      activatedCheckpoints: new Set(),
      addTrauma(amount: number) {
        this.camera.trauma = Math.min(1, this.camera.trauma + amount);
        // Haptics on mobile for meaty hits.
        if (amount >= 0.3 && typeof navigator !== "undefined" && navigator.vibrate) {
          navigator.vibrate(Math.round(amount * 60));
        }
      },
      hitStop(ms: number) {
        game.hitStopMs = Math.max(game.hitStopMs, ms);
      },
    };

    this.buildStage();
    this.input.attach();
    this.wireStore();

    // Mobile-friendly: backgrounding the tab/app auto-pauses instead of
    // letting the accumulator pile up.
    document.addEventListener("visibilitychange", () => {
      if (document.hidden && useGameStore.getState().screen === "playing") {
        useGameStore.getState().setScreen("paused");
      }
    });

    app.ticker.add(() => this.tick());
  }

  static async create(container: HTMLElement): Promise<Game> {
    const app = new Application();
    await app.init({
      preference: "webgpu", // WebGPU first, automatic WebGL fallback
      background: 0x10121f,
      resizeTo: window,
      antialias: false,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
      autoDensity: true,
    });
    container.appendChild(app.canvas);
    const game = new Game(app);
    useGameStore.getState().setStats({ renderer: app.renderer.name });
    return game;
  }

  // -------------------------------------------------------------------------
  // Stage graph
  // -------------------------------------------------------------------------
  private buildStage(): void {
    const L = this.ctx.layers;
    const { particles, lighting } = this.ctx;

    // Bloom over collectibles + front (sparkle) particles.
    const glowWrap = new Container();
    glowWrap.addChild(L.glow);
    const bloom = new AdvancedBloomFilter({
      threshold: 0.35,
      bloomScale: 1.0,
      brightness: 1.0,
      blur: 3,
      quality: 4,
    });
    glowWrap.filters = [bloom];

    L.camera.addChild(L.back, particles.back, glowWrap, L.entities, particles.front, lighting.glows, L.debug);
    this.viewport.addChild(L.sky, L.parallaxFar, L.parallaxNear, L.camera, lighting.darkness);
    lighting.resize(VIEW_W, VIEW_H);

    // Mask + letterbox the virtual 480x270 viewport.
    const mask = new Graphics().rect(0, 0, VIEW_W, VIEW_H).fill(0xffffff);
    this.viewport.addChild(mask);
    this.viewport.mask = mask;

    this.app.stage.addChild(this.viewport);
    this.applyPostFilters();
    this.layout();
    this.app.renderer.on("resize", () => this.layout());
  }

  private layout(): void {
    // app.screen is in logical (CSS) pixels regardless of resolution.
    const w = this.app.screen.width;
    const h = this.app.screen.height;
    const scale = Math.min(w / VIEW_W, h / VIEW_H);
    this.viewport.scale.set(scale);
    this.viewport.position.set((w - VIEW_W * scale) / 2, (h - VIEW_H * scale) / 2);
  }

  private applyPostFilters(): void {
    const filters = [this.vignette];
    if (useGameStore.getState().crt) filters.push(this.crtFilter as unknown as typeof this.vignette);
    this.viewport.filters = filters;
  }

  private wireStore(): void {
    // A new runId means "load store.level from scratch".
    useGameStore.subscribe(
      (s) => s.runId,
      () => {
        this.ctx.activatedCheckpoints.clear();
        this.startLevel(useGameStore.getState().level, true);
      },
    );
    useGameStore.subscribe(
      (s) => s.crt,
      () => this.applyPostFilters(),
    );
  }

  // -------------------------------------------------------------------------
  // Level lifecycle
  // -------------------------------------------------------------------------
  private clearWorld(): void {
    const { world } = this.ctx;
    for (const e of [...world.entities]) {
      e.sprite?.view.destroy();
      world.remove(e);
    }
    this.ctx.particles.clear();
    this.ctx.tweens.clear();
    this.ctx.lighting.clearGlows();
    this.ctx.tileBumps.length = 0;
    this.ctx.player = null;
  }

  private startLevel(index: number, freshRun: boolean): void {
    const ctx = this.ctx;
    this.levelIndex = Math.max(0, Math.min(index, LEVELS.length - 1));

    this.clearWorld();
    if (ctx.level) destroyLevel(ctx.level);
    ctx.layers.back.removeChildren();
    for (const key of ["sky", "parallaxFar", "parallaxNear"] as const) {
      ctx.layers[key].removeChildren().forEach((c) => c.destroy({ children: true }));
    }

    ctx.level = loadLevel(LEVELS[this.levelIndex]!, ctx.textures);
    ctx.layers.camera.addChildAt(ctx.level.tilemap, 0);

    const { sky, far, near } = buildParallax(ctx.level.theme, ctx.level.pxWid, ctx.textures);
    ctx.layers.sky.addChild(sky);
    ctx.layers.parallaxFar.addChild(far);
    ctx.layers.parallaxNear.addChild(near);

    // Dynamic lighting only in the cave; warm glows in cave + castle.
    ctx.lighting.setEnabled(ctx.level.theme === "cave");
    ctx.lighting.glows.visible = ctx.level.theme !== "overworld";

    const { player, spawnPoint, hasBoss } = spawnLevelEntities(ctx);
    ctx.player = player;

    if (freshRun) {
      ctx.respawn = { ...spawnPoint };
    } else if (ctx.respawn) {
      // Respawn at checkpoint: move the player there.
      player.position!.x = ctx.respawn.x - player.collider!.w / 2;
      player.position!.y = ctx.respawn.y - player.collider!.h;
      player.prev!.x = player.position!.x;
      player.prev!.y = player.position!.y;
    }

    // Restore checkpoints already hit this run (no double rewards).
    for (const e of ctx.queries.checkpoints) {
      if (ctx.activatedCheckpoints.has(e.checkpoint.id)) {
        e.checkpoint.activated = true;
        if (e.sprite) e.sprite.img.texture = ctx.textures.checkpointOn;
      }
    }

    // Warm glows on torches + goal flags.
    for (const e of ctx.queries.lights) {
      if (e.sprite) {
        ctx.lighting.createGlow(
          e.position.x + 3,
          e.position.y + 4,
          28,
          e.light.color,
          0.45,
        );
      }
    }

    void hasBoss; // boss HP appears in the HUD once the boss aggros (intro exit)
    useGameStore.getState().setBossHp(0, 0);
    ctx.camera.trauma = 0;
    ctx.pendingWarp = null;
    ctx.pendingRespawn = false;
    ctx.pendingComplete = false;
    this.accumulator = 0;
    this.hitStopMs = 0;
    snapCamera(ctx);
    this.renderFrame(1, 0);
  }

  // -------------------------------------------------------------------------
  // The loop: fixed-timestep simulation, interpolated rendering
  // -------------------------------------------------------------------------
  private tick(): void {
    const dtMS = Math.min(this.app.ticker.deltaMS, MAX_FRAME_MS);
    this.realTime += dtMS / 1000;
    this.fpsSmooth += (1000 / Math.max(1, this.app.ticker.deltaMS) - this.fpsSmooth) * 0.05;

    const screen = useGameStore.getState().screen;

    if (screen !== "playing") {
      // Menus/pause: keep polling input so Esc can resume, keep rendering.
      this.input.update();
      if (screen === "paused" && this.input.justPressed("pause")) {
        useGameStore.getState().resume();
      }
      if (this.input.justPressed("debug")) useGameStore.getState().toggleDebug();
      this.accumulator = 0;
      if (this.ctx.level) this.renderFrame(this.lastAlpha, 0);
      this.pushStats();
      return;
    }

    if (!this.ctx.level) return;

    // Hit-stop: freeze the simulation AND cosmetic motion, keep drawing.
    if (this.hitStopMs > 0) {
      this.hitStopMs -= dtMS;
      this.renderFrame(this.lastAlpha, 0);
      return;
    }

    this.accumulator += dtMS / 1000;
    let steps = 0;
    const t0 = performance.now();
    while (this.accumulator >= FIXED_STEP && steps < 5) {
      this.fixedUpdate(FIXED_STEP);
      this.accumulator -= FIXED_STEP;
      steps++;
      if (this.hitStopMs > 0) break; // a stomp mid-batch freezes the rest
    }
    if (steps > 0) {
      this.tickMsSmooth += ((performance.now() - t0) / steps - this.tickMsSmooth) * 0.1;
    }
    if (steps === 5) this.accumulator = 0; // dump backlog after long stalls

    this.lastAlpha = this.accumulator / FIXED_STEP;
    this.renderFrame(this.lastAlpha, dtMS / 1000);
    this.pushStats();
  }

  private fixedUpdate(dt: number): void {
    const ctx = this.ctx;
    ctx.time += dt;
    this.input.update();

    const store = useGameStore.getState();
    if (this.input.justPressed("pause")) {
      store.setScreen("paused");
      return;
    }
    if (this.input.justPressed("debug")) store.toggleDebug();

    // Snapshot previous positions for render interpolation.
    for (const e of ctx.queries.simulated) {
      e.prev.x = e.position.x;
      e.prev.y = e.position.y;
    }

    inputSystem(ctx, dt);
    aiSystem(ctx, dt);
    physicsSystem(ctx, dt);
    platformSystem(ctx, dt);
    interactionsSystem(ctx, dt);
    cameraSystem(ctx, dt);

    // Reap the dead.
    for (const e of [...ctx.queries.dead]) {
      e.sprite?.view.destroy();
      ctx.world.remove(e);
    }

    // --- Level flow commands ---------------------------------------------
    if (ctx.pendingComplete) {
      ctx.pendingComplete = false;
      if (this.levelIndex >= LEVELS.length - 1) store.setScreen("victory");
      else store.completeLevel();
      return;
    }
    if (ctx.pendingWarp !== null) {
      const target = ctx.pendingWarp === -1 ? this.levelIndex + 1 : ctx.pendingWarp;
      ctx.pendingWarp = null;
      if (target >= LEVELS.length) {
        store.setScreen("victory");
      } else {
        useGameStore.setState({
          level: target,
          unlockedLevels: Math.max(useGameStore.getState().unlockedLevels, target + 1),
        });
        this.ctx.activatedCheckpoints.clear();
        this.startLevel(target, true);
      }
      return;
    }
    if (ctx.pendingRespawn) {
      ctx.pendingRespawn = false;
      if (useGameStore.getState().lives > 0) {
        useGameStore.getState().setPlayerHp(1);
        this.startLevel(this.levelIndex, false);
      }
      return;
    }
  }

  private renderFrame(alpha: number, cosmeticDt: number): void {
    const ctx = this.ctx;
    if (!ctx.level) return;

    ctx.tweens.update(cosmeticDt);
    ctx.particles.update(cosmeticDt);
    this.ambientParticles(cosmeticDt);
    animationSystem(ctx, cosmeticDt);
    renderSystem(ctx, alpha, this.realTime);

    // Dynamic lighting (cave): darkness with erased holes at each light.
    const lighting = ctx.lighting;
    if (lighting.isEnabled) {
      lighting.begin();
      for (const e of ctx.queries.lights) {
        const flicker = e.light.flicker * Math.sin(this.realTime * 9 + e.position.x);
        const pos = worldToScreen(ctx, e.position.x + 6, e.position.y + 6, alpha);
        lighting.addLight(pos.x, pos.y, e.light.radius, flicker);
      }
      lighting.end();
    }

    if (useGameStore.getState().crt) {
      this.crtFilter.time += cosmeticDt * 8;
      this.crtFilter.seed = Math.random();
    }

    debugSystem(ctx, useGameStore.getState().debug);
  }

  /** Ambient sparkle on collectibles so bloom has something to chew on. */
  private ambientParticles(dt: number): void {
    if (dt <= 0) return;
    for (const e of this.ctx.queries.collectibles) {
      const c = e.collectible;
      c.sparkleTimer -= dt;
      if (c.sparkleTimer <= 0) {
        c.sparkleTimer = 0.6 + Math.random() * 1.2;
        this.ctx.particles.sparkle(
          e.position.x + e.collider.w / 2,
          e.position.y + e.collider.h / 2,
          1,
          c.kind === "coin" ? 0xffe98a : 0xffffff,
        );
      }
    }
  }

  private pushStats(): void {
    this.statsTimer -= this.app.ticker.deltaMS / 1000;
    if (this.statsTimer > 0) return;
    this.statsTimer = 0.25;
    const store = useGameStore.getState();
    if (!store.debug) return;
    store.setStats({
      fps: Math.round(this.fpsSmooth),
      entityCount: this.ctx.world.entities.length,
      particleCount: this.ctx.particles.count,
      tickMs: Math.round(this.tickMsSmooth * 100) / 100,
    });
  }
}
