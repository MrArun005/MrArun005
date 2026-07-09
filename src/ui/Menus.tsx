import { useGameStore } from "@state/store";
import { LEVEL_NAMES } from "@game/level/levels";

const overlay: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  background: "rgba(16, 18, 31, 0.82)",
  color: "#fff",
  textShadow: "2px 2px 0 #181425",
  pointerEvents: "auto",
  gap: 14,
};

const btn: React.CSSProperties = {
  font: "inherit",
  fontSize: 18,
  fontWeight: 700,
  letterSpacing: 1,
  padding: "10px 28px",
  cursor: "pointer",
  color: "#fff",
  background: "#2c6ff2",
  border: "3px solid #181425",
  borderRadius: 6,
  boxShadow: "0 4px 0 #181425",
  minWidth: 240,
};

const btnAlt: React.CSSProperties = { ...btn, background: "#5a6988" };

function Title({ children }: { children: React.ReactNode }) {
  return <h1 style={{ fontSize: 42, margin: 0, color: "#fee761", textAlign: "center" }}>{children}</h1>;
}

export function MainMenu() {
  const startGame = useGameStore((s) => s.startGame);
  const setScreen = useGameStore((s) => s.setScreen);
  return (
    <div style={overlay}>
      <Title>SUPER PLUMBER BROS</Title>
      <p style={{ margin: "0 0 10px", color: "#8b9bb4" }}>PixiJS v8 · WebGPU · ECS</p>
      <button style={btn} onClick={() => startGame(0)}>START GAME</button>
      <button style={btnAlt} onClick={() => setScreen("levelselect")}>LEVEL SELECT</button>
      <p style={{ fontSize: 13, color: "#8b9bb4", maxWidth: 460, textAlign: "center", lineHeight: 1.7 }}>
        ARROWS / WASD move · SPACE/Z jump (hold = higher) · SHIFT/X run
        <br />
        DOWN on a pipe warps · ESC pause · F1 debug · gamepads supported
      </p>
    </div>
  );
}

export function LevelSelect() {
  const unlocked = useGameStore((s) => s.unlockedLevels);
  const startGame = useGameStore((s) => s.startGame);
  const setScreen = useGameStore((s) => s.setScreen);
  return (
    <div style={overlay}>
      <Title>LEVEL SELECT</Title>
      {LEVEL_NAMES.map((name, i) => {
        const locked = i >= unlocked;
        return (
          <button
            key={name}
            style={{ ...btn, background: locked ? "#3a4466" : "#2c6ff2", opacity: locked ? 0.6 : 1 }}
            disabled={locked}
            onClick={() => startGame(i)}
          >
            {i + 1}. {name} {locked ? "🔒" : ""}
          </button>
        );
      })}
      <button style={btnAlt} onClick={() => setScreen("menu")}>BACK</button>
    </div>
  );
}

export function PauseMenu() {
  const resume = useGameStore((s) => s.resume);
  const setScreen = useGameStore((s) => s.setScreen);
  const crt = useGameStore((s) => s.crt);
  const toggleCrt = useGameStore((s) => s.toggleCrt);
  const debug = useGameStore((s) => s.debug);
  const toggleDebug = useGameStore((s) => s.toggleDebug);
  return (
    <div style={overlay}>
      <Title>PAUSED</Title>
      <button style={btn} onClick={resume}>RESUME</button>
      <button style={btnAlt} onClick={toggleCrt}>CRT SHADER: {crt ? "ON" : "OFF"}</button>
      <button style={btnAlt} onClick={toggleDebug}>DEBUG (F1): {debug ? "ON" : "OFF"}</button>
      <button style={btnAlt} onClick={() => setScreen("menu")}>QUIT TO MENU</button>
    </div>
  );
}

export function LevelComplete() {
  const score = useGameStore((s) => s.score);
  const nextLevel = useGameStore((s) => s.nextLevel);
  const setScreen = useGameStore((s) => s.setScreen);
  return (
    <div style={overlay}>
      <Title>LEVEL CLEAR!</Title>
      <p style={{ fontSize: 20 }}>SCORE {String(score).padStart(6, "0")}</p>
      <button style={btn} onClick={nextLevel}>NEXT LEVEL →</button>
      <button style={btnAlt} onClick={() => setScreen("menu")}>MENU</button>
    </div>
  );
}

export function GameOver() {
  const level = useGameStore((s) => s.level);
  const score = useGameStore((s) => s.score);
  const startGame = useGameStore((s) => s.startGame);
  const setScreen = useGameStore((s) => s.setScreen);
  return (
    <div style={overlay}>
      <Title>GAME OVER</Title>
      <p style={{ fontSize: 20 }}>SCORE {String(score).padStart(6, "0")}</p>
      <button style={btn} onClick={() => startGame(level)}>TRY AGAIN</button>
      <button style={btnAlt} onClick={() => setScreen("menu")}>MENU</button>
    </div>
  );
}

export function Victory() {
  const score = useGameStore((s) => s.score);
  const setScreen = useGameStore((s) => s.setScreen);
  return (
    <div style={overlay}>
      <Title>👑 YOU WIN! 👑</Title>
      <p style={{ fontSize: 20 }}>THE CASTLE KEEP HAS FALLEN</p>
      <p style={{ fontSize: 20 }}>FINAL SCORE {String(score).padStart(6, "0")}</p>
      <button style={btn} onClick={() => setScreen("menu")}>BACK TO MENU</button>
    </div>
  );
}
