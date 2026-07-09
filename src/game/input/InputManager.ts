/**
 * Unified input: keyboard + Gamepad API + touch (virtual buttons fed from the
 * React overlay). The game loop reads edge-triggered (`pressed`) and
 * level-triggered (`held`) state once per fixed tick.
 */

export type GameAction = "left" | "right" | "up" | "down" | "jump" | "run" | "pause" | "debug";

const KEY_MAP: Record<string, GameAction> = {
  ArrowLeft: "left",
  KeyA: "left",
  ArrowRight: "right",
  KeyD: "right",
  ArrowUp: "up",
  KeyW: "up",
  ArrowDown: "down",
  KeyS: "down",
  Space: "jump",
  KeyZ: "jump",
  KeyK: "jump",
  ShiftLeft: "run",
  KeyX: "run",
  KeyJ: "run",
  Escape: "pause",
  KeyP: "pause",
  F1: "debug",
};

const GAMEPAD_BUTTONS: Partial<Record<number, GameAction>> = {
  0: "jump", // A / Cross
  1: "run", // B / Circle
  2: "run", // X / Square
  9: "pause", // Start
  12: "up",
  13: "down",
  14: "left",
  15: "right",
};

const AXIS_DEADZONE = 0.35;

export class InputManager {
  private held = new Set<GameAction>();
  private prevHeld = new Set<GameAction>();
  /** Virtual (touch) input — OR-ed with physical input. */
  private virtual = new Set<GameAction>();
  private keyboard = new Set<GameAction>();
  private gamepad = new Set<GameAction>();
  /** Keys tapped since the last tick — a press+release inside one 60 Hz tick
   *  still registers as held for exactly one update (never lose fast taps). */
  private tapped = new Set<GameAction>();
  gamepadConnected = false;

  private onKeyDown = (e: KeyboardEvent) => {
    const action = KEY_MAP[e.code];
    if (!action) return;
    if (e.code === "F1" || e.code === "Space" || e.code.startsWith("Arrow")) e.preventDefault();
    if (!e.repeat) this.tapped.add(action);
    this.keyboard.add(action);
  };

  private onKeyUp = (e: KeyboardEvent) => {
    const action = KEY_MAP[e.code];
    if (action) this.keyboard.delete(action);
  };

  attach(target: Window = window): void {
    target.addEventListener("keydown", this.onKeyDown);
    target.addEventListener("keyup", this.onKeyUp);
    target.addEventListener("blur", () => {
      this.keyboard.clear();
      this.virtual.clear();
    });
  }

  detach(target: Window = window): void {
    target.removeEventListener("keydown", this.onKeyDown);
    target.removeEventListener("keyup", this.onKeyUp);
  }

  /** Called from the React touch controls (pointer down/up on virtual buttons). */
  setVirtual(action: GameAction, down: boolean): void {
    if (down) {
      this.virtual.add(action);
      this.tapped.add(action);
    } else this.virtual.delete(action);
  }

  private pollGamepad(): void {
    this.gamepad.clear();
    this.gamepadConnected = false;
    const pads = typeof navigator !== "undefined" && navigator.getGamepads ? navigator.getGamepads() : [];
    for (const pad of pads) {
      if (!pad || !pad.connected) continue;
      this.gamepadConnected = true;
      pad.buttons.forEach((btn, i) => {
        const action = GAMEPAD_BUTTONS[i];
        if (action && (btn.pressed || btn.value > 0.5)) this.gamepad.add(action);
      });
      const ax = pad.axes[0] ?? 0;
      const ay = pad.axes[1] ?? 0;
      if (ax < -AXIS_DEADZONE) this.gamepad.add("left");
      if (ax > AXIS_DEADZONE) this.gamepad.add("right");
      if (ay < -AXIS_DEADZONE) this.gamepad.add("up");
      if (ay > AXIS_DEADZONE) this.gamepad.add("down");
    }
  }

  /** Snapshot inputs for this tick. Call exactly once per fixed update. */
  update(): void {
    this.pollGamepad();
    this.prevHeld = new Set(this.held);
    this.held = new Set<GameAction>([
      ...this.keyboard,
      ...this.gamepad,
      ...this.virtual,
      ...this.tapped,
    ]);
    this.tapped.clear();
  }

  isHeld(action: GameAction): boolean {
    return this.held.has(action);
  }

  /** True only on the tick the action transitioned from up → down. */
  justPressed(action: GameAction): boolean {
    return this.held.has(action) && !this.prevHeld.has(action);
  }

  justReleased(action: GameAction): boolean {
    return !this.held.has(action) && this.prevHeld.has(action);
  }

  axisX(): number {
    return (this.isHeld("right") ? 1 : 0) - (this.isHeld("left") ? 1 : 0);
  }
}
