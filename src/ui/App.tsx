import { useGameStore } from "@state/store";
import type { InputManager } from "@game/input/InputManager";
import { HUD } from "./HUD";
import { DebugOverlay } from "./DebugOverlay";
import { TouchControls } from "./TouchControls";
import { RotateOverlay } from "./RotateOverlay";
import { GameOver, LevelComplete, LevelSelect, MainMenu, PauseMenu, Victory } from "./Menus";

/**
 * The entire React tree. It renders DOM on top of the Pixi canvas and talks
 * to the game exclusively through the zustand store (plus virtual buttons
 * feeding the InputManager). Zero React in the game loop.
 */
export function App({ input }: { input: InputManager }) {
  const screen = useGameStore((s) => s.screen);
  const debug = useGameStore((s) => s.debug);
  const touchDevice = useGameStore((s) => s.touchDevice);

  return (
    <>
      {(screen === "playing" || screen === "paused") && <HUD />}
      {screen === "menu" && <MainMenu />}
      {screen === "levelselect" && <LevelSelect />}
      {screen === "paused" && <PauseMenu />}
      {screen === "levelcomplete" && <LevelComplete />}
      {screen === "gameover" && <GameOver />}
      {screen === "victory" && <Victory />}
      {debug && <DebugOverlay />}
      {touchDevice && screen === "playing" && <TouchControls input={input} />}
      <RotateOverlay />
    </>
  );
}
