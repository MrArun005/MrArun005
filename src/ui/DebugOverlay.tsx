import { useGameStore } from "@state/store";

/** F1 stats panel: FPS, entity/particle counts, renderer, tick cost. */
export function DebugOverlay() {
  const stats = useGameStore((s) => s.stats);
  return (
    <div
      style={{
        position: "absolute",
        bottom: 12,
        left: 12,
        padding: "8px 12px",
        background: "rgba(24, 20, 37, 0.85)",
        border: "1px solid #5a6988",
        borderRadius: 4,
        color: "#2ce8f5",
        fontSize: 12,
        lineHeight: 1.8,
        whiteSpace: "pre",
      }}
    >
      {`FPS        ${stats.fps}
ENTITIES   ${stats.entityCount}
PARTICLES  ${stats.particleCount}
TICK       ${stats.tickMs} ms
RENDERER   ${stats.renderer.toUpperCase()}`}
    </div>
  );
}
