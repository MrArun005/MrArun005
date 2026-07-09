import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Game } from "@game/Game";
import { App } from "@ui/App";
import { useGameStore } from "@state/store";

async function boot() {
  const gameHost = document.getElementById("app")!;
  const hudHost = document.getElementById("hud-root")!;

  const game = await Game.create(gameHost);

  // Handy for debugging + automated smoke tests.
  (window as unknown as Record<string, unknown>).__game = { game, store: useGameStore };

  createRoot(hudHost).render(
    <StrictMode>
      <App input={game.input} />
    </StrictMode>,
  );
}

boot().catch((err) => {
  console.error("Failed to boot game:", err);
  const el = document.getElementById("hud-root");
  if (el) {
    el.innerHTML = `<div style="color:#e43b44;padding:40px;font-size:18px">
      Failed to start (WebGPU/WebGL unavailable?): ${String(err)}
    </div>`;
  }
});
