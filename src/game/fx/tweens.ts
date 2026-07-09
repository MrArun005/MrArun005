export type EaseFn = (t: number) => number;

export const easeOutQuad: EaseFn = (t) => 1 - (1 - t) * (1 - t);
export const easeOutBack: EaseFn = (t) => {
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};
export const easeInQuad: EaseFn = (t) => t * t;

interface Tween {
  elapsed: number;
  duration: number;
  ease: EaseFn;
  onUpdate: (t: number) => void;
  onComplete?: (() => void) | undefined;
}

/**
 * Minimal tween runner for visual-only animation (block bumps, flag pops,
 * boss flashes). Runs on render time, not simulation time — purely cosmetic.
 */
export class TweenManager {
  private tweens: Tween[] = [];

  add(opts: {
    duration: number;
    ease?: EaseFn;
    onUpdate: (t: number) => void;
    onComplete?: () => void;
  }): void {
    this.tweens.push({
      elapsed: 0,
      duration: opts.duration,
      ease: opts.ease ?? easeOutQuad,
      onUpdate: opts.onUpdate,
      onComplete: opts.onComplete,
    });
  }

  /** Bounce a value up and back (block bumps): onUpdate receives 0→1→0. */
  bump(duration: number, onUpdate: (t: number) => void, onComplete?: () => void): void {
    this.add({
      duration,
      ease: (t) => t,
      onUpdate: (t) => onUpdate(Math.sin(t * Math.PI)),
      ...(onComplete ? { onComplete } : {}),
    });
  }

  update(dt: number): void {
    for (let i = this.tweens.length - 1; i >= 0; i--) {
      const tw = this.tweens[i]!;
      tw.elapsed += dt;
      const t = Math.min(1, tw.elapsed / tw.duration);
      tw.onUpdate(tw.ease(t));
      if (t >= 1) {
        this.tweens.splice(i, 1);
        tw.onComplete?.();
      }
    }
  }

  clear(): void {
    this.tweens = [];
  }
}
