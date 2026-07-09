import { useGameStore } from "@state/store";

const barStyle: React.CSSProperties = {
  position: "absolute",
  // env() keeps the bar clear of notches on phones.
  top: "calc(10px + env(safe-area-inset-top))",
  left: "calc(14px + env(safe-area-inset-left))",
  right: "calc(14px + env(safe-area-inset-right))",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  color: "#fff",
  textShadow: "2px 2px 0 #181425",
  fontSize: "clamp(13px, 2.6vmin, 19px)",
  fontWeight: 700,
  letterSpacing: 1,
};

/** Pure-React HUD. Subscribes to zustand — never touches the game loop. */
export function HUD() {
  const score = useGameStore((s) => s.score);
  const coins = useGameStore((s) => s.coins);
  const lives = useGameStore((s) => s.lives);
  const playerHp = useGameStore((s) => s.playerHp);
  const bossHp = useGameStore((s) => s.bossHp);
  const bossMaxHp = useGameStore((s) => s.bossMaxHp);
  const checkpointHint = useGameStore((s) => s.checkpointHint);

  return (
    <div style={barStyle}>
      <div>
        <div>SCORE {String(score).padStart(6, "0")}</div>
        <div style={{ fontSize: "0.8em", marginTop: 4, color: "#fee761" }}>
          ● ×{String(coins).padStart(2, "0")}
        </div>
      </div>

      {bossMaxHp > 0 && (
        <div style={{ textAlign: "center", flex: 1, maxWidth: 320, margin: "0 24px" }}>
          <div style={{ fontSize: "0.75em", color: "#f6757a", marginBottom: 4 }}>BOSS</div>
          <div
            style={{
              height: 12,
              border: "2px solid #181425",
              background: "#3a2430",
              borderRadius: 3,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${(Math.max(0, bossHp) / bossMaxHp) * 100}%`,
                height: "100%",
                background: bossHp > 6 ? "#63c74d" : bossHp > 3 ? "#fee761" : "#e43b44",
                transition: "width 200ms ease-out",
              }}
            />
          </div>
        </div>
      )}

      <div style={{ textAlign: "right" }}>
        <div style={{ color: "#f6757a" }}>♥ ×{lives}</div>
        <div style={{ fontSize: "0.75em", marginTop: 4, color: playerHp >= 2 ? "#63c74d" : "#8b9bb4" }}>
          {playerHp >= 2 ? "SUPER" : "SMALL"}
        </div>
      </div>

      {checkpointHint && (
        <div
          style={{
            position: "absolute",
            top: 70,
            left: 0,
            right: 0,
            textAlign: "center",
            color: "#63c74d",
            fontSize: "clamp(16px, 3vmin, 24px)",
            animation: "hud-pop 300ms ease-out",
          }}
        >
          {checkpointHint}
        </div>
      )}
    </div>
  );
}
