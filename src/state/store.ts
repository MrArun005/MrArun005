import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

/**
 * Meta-state lives in zustand: React (HUD, menus) subscribes to it, and the
 * game loop writes to it via `useGameStore.getState()` / `setState()`.
 * Nothing in here is read per-frame by the simulation — the ECS world owns
 * all hot data. Zero React in the game loop.
 */

export type GameScreen =
  | "menu"
  | "levelselect"
  | "playing"
  | "paused"
  | "levelcomplete"
  | "gameover"
  | "victory";

export interface DebugStats {
  fps: number;
  entityCount: number;
  particleCount: number;
  renderer: string;
  tickMs: number;
}

interface GameState {
  screen: GameScreen;
  score: number;
  coins: number;
  lives: number;
  /** 1 = small, 2 = big (mushroom). Mirrors the player Health component for the HUD. */
  playerHp: number;
  level: number; // 0-based index into LEVELS
  unlockedLevels: number;
  bossHp: number;
  bossMaxHp: number;
  checkpointHint: string | null;
  debug: boolean;
  /** Optional CRT post-processing shader. */
  crt: boolean;
  /** Bumped on every fresh (re)start so the game engine knows to reload. */
  runId: number;
  stats: DebugStats;
  touchDevice: boolean;

  startGame: (level: number) => void;
  nextLevel: () => void;
  resume: () => void;
  toggleCrt: () => void;
  setScreen: (s: GameScreen) => void;
  addScore: (n: number) => void;
  addCoin: () => void;
  setLives: (n: number) => void;
  loseLife: () => void;
  setPlayerHp: (n: number) => void;
  setBossHp: (hp: number, max?: number) => void;
  completeLevel: () => void;
  toggleDebug: () => void;
  setStats: (s: Partial<DebugStats>) => void;
  setCheckpointHint: (s: string | null) => void;
}

export const useGameStore = create<GameState>()(
  subscribeWithSelector((set, get) => ({
    screen: "menu",
    score: 0,
    coins: 0,
    lives: 3,
    playerHp: 1,
    level: 0,
    unlockedLevels: 1,
    bossHp: 0,
    bossMaxHp: 0,
    checkpointHint: null,
    debug: false,
    crt: false,
    runId: 0,
    stats: { fps: 0, entityCount: 0, particleCount: 0, renderer: "?", tickMs: 0 },
    touchDevice:
      typeof window !== "undefined" &&
      (window.matchMedia?.("(pointer: coarse)").matches || "ontouchstart" in window),

    startGame: (level) =>
      set((s) => ({
        screen: "playing",
        level,
        score: 0,
        coins: 0,
        lives: 3,
        playerHp: 1,
        bossHp: 0,
        bossMaxHp: 0,
        checkpointHint: null,
        runId: s.runId + 1,
      })),
    nextLevel: () =>
      set((s) => ({
        screen: "playing",
        level: s.level + 1,
        bossHp: 0,
        bossMaxHp: 0,
        playerHp: 1,
        runId: s.runId + 1,
      })),
    resume: () => set({ screen: "playing" }),
    toggleCrt: () => set((s) => ({ crt: !s.crt })),
    setScreen: (screen) => set({ screen }),
    addScore: (n) => set((s) => ({ score: s.score + n })),
    addCoin: () =>
      set((s) => {
        const coins = s.coins + 1;
        // Classic rule: 100 coins = extra life.
        if (coins >= 100) return { coins: coins - 100, lives: s.lives + 1, score: s.score + 100 };
        return { coins, score: s.score + 100 };
      }),
    setLives: (lives) => set({ lives }),
    loseLife: () => {
      const lives = get().lives - 1;
      set({ lives });
      if (lives <= 0) set({ screen: "gameover" });
    },
    setPlayerHp: (playerHp) => set({ playerHp }),
    setBossHp: (bossHp, max) =>
      set((s) => ({ bossHp, bossMaxHp: max ?? s.bossMaxHp })),
    completeLevel: () =>
      set((s) => ({
        screen: "levelcomplete",
        unlockedLevels: Math.max(s.unlockedLevels, s.level + 2),
      })),
    toggleDebug: () => set((s) => ({ debug: !s.debug })),
    setStats: (partial) => set((s) => ({ stats: { ...s.stats, ...partial } })),
    setCheckpointHint: (checkpointHint) => set({ checkpointHint }),
  })),
);
