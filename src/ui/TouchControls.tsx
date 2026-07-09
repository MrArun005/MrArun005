import { useRef } from "react";
import type { InputManager, GameAction } from "@game/input/InputManager";

/**
 * Mobile-first touch controls feeding the same InputManager as keyboard and
 * gamepad. The D-pad is one continuous surface — sliding a thumb between
 * ◀ / ▼ / ▶ retargets without lifting, like a real pad. Sized with vmin and
 * kept clear of notches/home bars by the #hud-root safe-area padding.
 */

const BTN = "clamp(56px, 13vmin, 88px)";

const zone: React.CSSProperties = {
  position: "absolute",
  bottom: "max(14px, env(safe-area-inset-bottom))",
  pointerEvents: "auto",
  display: "flex",
  gap: "clamp(8px, 2vmin, 16px)",
};

const btnBase: React.CSSProperties = {
  width: BTN,
  height: BTN,
  borderRadius: "22%",
  border: "3px solid rgba(255,255,255,0.45)",
  background: "rgba(24, 20, 37, 0.38)",
  color: "rgba(255,255,255,0.9)",
  fontSize: "clamp(20px, 5vmin, 32px)",
  fontWeight: 700,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  userSelect: "none",
  touchAction: "none",
};

const DPAD_ACTIONS: GameAction[] = ["left", "down", "right"];

function DPad({ input }: { input: InputManager }) {
  const ref = useRef<HTMLDivElement>(null);
  const active = useRef<Map<number, GameAction>>(new Map());

  const actionAt = (clientX: number): GameAction => {
    const rect = ref.current!.getBoundingClientRect();
    const t = (clientX - rect.left) / rect.width;
    return DPAD_ACTIONS[Math.min(2, Math.max(0, Math.floor(t * 3)))]!;
  };

  const press = (pointerId: number, action: GameAction | null) => {
    const prev = active.current.get(pointerId);
    if (prev === action) return;
    if (prev) input.setVirtual(prev, false);
    if (action) {
      input.setVirtual(action, true);
      active.current.set(pointerId, action);
    } else {
      active.current.delete(pointerId);
    }
  };

  return (
    <div
      ref={ref}
      style={{ ...zone, left: "max(14px, env(safe-area-inset-left))", touchAction: "none" }}
      onPointerDown={(e) => {
        e.preventDefault();
        ref.current!.setPointerCapture(e.pointerId);
        press(e.pointerId, actionAt(e.clientX));
      }}
      onPointerMove={(e) => {
        if (active.current.has(e.pointerId)) press(e.pointerId, actionAt(e.clientX));
      }}
      onPointerUp={(e) => press(e.pointerId, null)}
      onPointerCancel={(e) => press(e.pointerId, null)}
    >
      <div style={btnBase}>◀</div>
      <div style={btnBase}>▼</div>
      <div style={btnBase}>▶</div>
    </div>
  );
}

function ActionButton({ input, action, label, big }: {
  input: InputManager;
  action: GameAction;
  label: string;
  big?: boolean;
}) {
  return (
    <div
      style={{
        ...btnBase,
        borderRadius: "50%",
        ...(big ? { width: `calc(${BTN} * 1.25)`, height: `calc(${BTN} * 1.25)` } : {}),
      }}
      onPointerDown={(e) => {
        e.preventDefault();
        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
        input.setVirtual(action, true);
      }}
      onPointerUp={() => input.setVirtual(action, false)}
      onPointerCancel={() => input.setVirtual(action, false)}
    >
      {label}
    </div>
  );
}

export function TouchControls({ input }: { input: InputManager }) {
  return (
    <>
      <DPad input={input} />
      <div style={{ ...zone, right: "max(14px, env(safe-area-inset-right))", alignItems: "flex-end" }}>
        <ActionButton input={input} action="run" label="B" />
        <ActionButton input={input} action="jump" label="A" big />
      </div>
    </>
  );
}
