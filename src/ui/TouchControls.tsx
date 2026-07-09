import type { InputManager, GameAction } from "@game/input/InputManager";

const pad: React.CSSProperties = {
  position: "absolute",
  bottom: 18,
  display: "flex",
  gap: 12,
  pointerEvents: "auto",
};

const key: React.CSSProperties = {
  width: 64,
  height: 64,
  borderRadius: 12,
  border: "3px solid rgba(255,255,255,0.5)",
  background: "rgba(24, 20, 37, 0.4)",
  color: "#fff",
  fontSize: 24,
  fontWeight: 700,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  userSelect: "none",
  touchAction: "none",
};

function TouchButton({ input, action, label }: { input: InputManager; action: GameAction; label: string }) {
  return (
    <div
      style={key}
      onPointerDown={(e) => {
        e.preventDefault();
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
        input.setVirtual(action, true);
      }}
      onPointerUp={() => input.setVirtual(action, false)}
      onPointerCancel={() => input.setVirtual(action, false)}
    >
      {label}
    </div>
  );
}

/** Virtual buttons that feed the same InputManager as keyboard/gamepad. */
export function TouchControls({ input }: { input: InputManager }) {
  return (
    <>
      <div style={{ ...pad, left: 18 }}>
        <TouchButton input={input} action="left" label="◀" />
        <TouchButton input={input} action="right" label="▶" />
        <TouchButton input={input} action="down" label="▼" />
      </div>
      <div style={{ ...pad, right: 18 }}>
        <TouchButton input={input} action="run" label="B" />
        <TouchButton input={input} action="jump" label="A" />
      </div>
    </>
  );
}
