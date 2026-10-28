# Super Plumber Bros 🍄

A Mario-style platformer built to show off a modern web-game stack:

**Vite + TypeScript (strict) + PixiJS v8 (WebGPU-first) + miniplex ECS + zustand + React HUD overlay**

All art is generated procedurally at boot (pixel grids + canvas) — zero binary assets in the repo.

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # typecheck + production build
node scripts/smoke-test.mjs   # headless boot & gameplay test (needs Chromium)
```

## Architecture

```
src/
├── main.tsx                  # boots Pixi (WebGPU → WebGL fallback) + React HUD
├── state/store.ts            # zustand: score/lives/level/screen — meta-state only
├── ui/                       # React: HUD, pause menu, level select, debug panel,
│                             #   touch controls. Subscribes to zustand. Zero React
│                             #   in the game loop.
└── game/
    ├── Game.ts               # fixed-timestep loop (1/60s accumulator) decoupled
    │                         #   from render; interpolates positions between ticks;
    │                         #   hit-stop; level lifecycle; post-processing
    ├── context.ts            # Ctx — the service bag every system receives
    ├── ecs/                  # miniplex world; components: Position, Velocity,
    │                         #   Collider(AABB), Sprite, PlayerControl, EnemyAI,
    │                         #   Health, Collectible, Platform, Pipe, Checkpoint, Light
    ├── systems/              # input, physics, collision (in physics.ts), platforms,
    │                         #   ai (FSM per enemy type + 3-phase boss), interactions,
    │                         #   camera, animation, render, debug
    ├── level/                # LDtk JSON schema types + loader + entity spawner;
    │   └── data/*.json       #   3 sample levels as LDtk-schema JSON (IntGrid
    │                         #   collision layer + Entities layer)
    ├── fx/                   # GPU particles (ParticleContainer, 500+ poofs),
    │                         #   custom GLSL+WGSL shaders (vignette, palette swap),
    │                         #   erase-blend 2D lighting, tweens
    ├── gfx/                  # procedural pixel-art textures + parallax builders
    └── input/                # keyboard + Gamepad API + touch, edge-buffered
```

### Game feel (the non-negotiables)

- **Coyote time** 100 ms, **jump buffer** 120 ms, **variable jump height** (release to cut), **asymmetric gravity** (1.6× falling)
- **Corner correction** — clipping a ceiling edge by ≤5 px nudges you around it
- **Squash & stretch** on jump/land/stomp, **hit-stop** 60 ms on stomps (more on boss hits)
- Camera: **deadzone** box, velocity **lookahead**, **trauma-based screen shake** (shake = trauma², decays over time)

### Modern rendering

- WebGPU-first (`preference: "webgpu"`), automatic WebGL fallback — custom filters ship **both WGSL and GLSL**
- **Bloom** (pixi-filters AdvancedBloom) on collectibles + sparkles, custom **vignette**, optional **CRT** shader (toggle in pause menu)
- **Palette-swap fragment shader** recolors enemy tier variants (tier 2 = blue elite, tier 3 = red brute) from one texture
- **GPU particles** via Pixi v8 `ParticleContainer` — dust, sparkles, coin bursts, 500+ particle death poofs, boss shockwaves
- **4-layer parallax** (sky 0 / far 0.2 / near 0.5 / world 1.0) with per-theme backdrops
- **Dynamic 2D lighting** in the cave: screen darkness rendered through an `AlphaFilter` with `erase`-blend light sprites punching soft holes, plus additive glow sprites

### Content

- **3 levels** (Green Hills → Crystal Cave → Castle Keep) authored as **LDtk-schema JSON** (`src/game/level/data/`); regenerate with `node scripts/generate-levels.mjs`
- Enemies: **walker**, **flyer** (sine hover), **shell-kicker** (stomp → shell → kick, shells mow down enemies) — one FSM per type
- **Question blocks** (coins + mushroom power-up; big players smash bricks), **pipes as level warps** (hold ▼), **moving platforms** that carry you, **checkpoints**
- **Boss with a 3-phase FSM**: jump-shockwaves → charges + minion summons → enraged everything, stomp it 9 times

### Controls

| Action | Keyboard | Gamepad | Touch |
|---|---|---|---|
| Move | ←/→ or A/D | left stick / d-pad | ◀ ▶ |
| Jump (hold = higher) | Space / Z / K | A | A |
| Run | Shift / X / J | B / X | B |
| Enter pipe | ↓ / S | d-pad down | ▼ |
| Pause | Esc / P | Start | — |
| Debug overlay (hitboxes, FPS, entity count) | F1 | — | — |
