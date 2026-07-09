import { useEffect, useState } from "react";
import { useGameStore } from "@state/store";

/**
 * The game is a landscape 480x270 world — on a portrait phone, ask for a
 * rotate instead of squeezing the view. Pure CSS/JS; disappears on rotate.
 */
export function RotateOverlay() {
  const touchDevice = useGameStore((s) => s.touchDevice);
  const [portrait, setPortrait] = useState(
    () => window.matchMedia("(orientation: portrait)").matches,
  );

  useEffect(() => {
    const mq = window.matchMedia("(orientation: portrait)");
    const onChange = (e: MediaQueryListEvent) => setPortrait(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  if (!touchDevice || !portrait) return null;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "#10121f",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 18,
        zIndex: 50,
        pointerEvents: "auto",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 56, animation: "spin-hint 1.6s ease-in-out infinite" }}>📱</div>
      <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: 1, color: "#fee761" }}>
        ROTATE YOUR DEVICE
      </div>
      <div style={{ fontSize: 14, color: "#8b9bb4" }}>This game plays in landscape</div>
      <style>{`@keyframes spin-hint { 0%, 20% { transform: rotate(0deg); } 60%, 100% { transform: rotate(90deg); } }`}</style>
    </div>
  );
}
