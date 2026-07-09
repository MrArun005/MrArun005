import { chromium } from "playwright-core";
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { join, extname } from "node:path";

const DIST = new URL("../dist", import.meta.url).pathname;
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".webmanifest": "application/manifest+json", ".svg": "image/svg+xml", ".png": "image/png" };
const server = createServer((req, res) => {
  let p = join(DIST, req.url === "/" ? "index.html" : req.url.split("?")[0]);
  if (!existsSync(p)) p = join(DIST, "index.html");
  res.setHeader("Content-Type", MIME[extname(p)] ?? "application/octet-stream");
  res.end(readFileSync(p));
});
await new Promise((r) => server.listen(4176, r));

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });

// --- Landscape phone with touch ---
const page = await browser.newPage({
  viewport: { width: 844, height: 390 },
  hasTouch: true,
  isMobile: true,
  deviceScaleFactor: 2,
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
});
page.on("pageerror", (e) => console.log("[pageerror]", String(e).slice(0, 300)));
await page.goto("http://localhost:4176/");
await page.waitForTimeout(1800);

console.log("manifest:", await page.evaluate(async () => {
  const r = await fetch("/manifest.webmanifest");
  const m = await r.json();
  return `${m.name} / display=${m.display} / icons=${m.icons.length}`;
}));
console.log("touchDevice:", await page.evaluate(() => window.__game.store.getState().touchDevice));

await page.tap("text=START GAME");
await page.waitForTimeout(800);

// Touch controls visible?
const dpadVisible = await page.evaluate(() => {
  const divs = [...document.querySelectorAll("#hud-root div")];
  return divs.some((d) => d.textContent === "▶") && divs.some((d) => d.textContent === "A");
});
console.log("touch controls visible:", dpadVisible ? "YES" : "NO");
await page.screenshot({ path: "scripts/shot-mobile.png" });

// Drive right using the D-pad ▶ (touchscreen) + jump with A.
const x0 = await page.evaluate(() => Math.round(window.__game.game.ctx.player.position.x));
const right = page.locator("#hud-root div", { hasText: /^▶$/ }).first();
const jumpBtn = page.locator("#hud-root div", { hasText: /^A$/ }).first();
const rb = await right.boundingBox();
const jb = await jumpBtn.boundingBox();

await page.touchscreen.tap(rb.x + rb.width / 2, rb.y + rb.height / 2); // tap once
// hold: dispatch touch via CDP-ish long press — use repeated taps + evaluate hold
await page.evaluate(async () => {
  const input = window.__game.game.input;
  input.setVirtual("right", true);
  await new Promise((r) => setTimeout(r, 1200));
  input.setVirtual("right", false);
});
const x1 = await page.evaluate(() => Math.round(window.__game.game.ctx.player.position.x));
console.log("virtual right moved player:", x0, "→", x1, x1 > x0 + 40 ? "OK" : "FAIL");

// Real touchscreen hold on A (down/up with delay) to jump.
const y0 = await page.evaluate(() => Math.round(window.__game.game.ctx.player.position.y));
await page.touchscreen.tap(jb.x + jb.width / 2, jb.y + jb.height / 2);
await page.waitForTimeout(250);
const yMid = await page.evaluate(() => Math.round(window.__game.game.ctx.player.position.y));
console.log("touch jump: y", y0, "→", yMid, yMid < y0 - 8 ? "OK" : "FAIL");

// --- Portrait: rotate overlay ---
await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(500);
const rotate = await page.textContent("#hud-root");
console.log("rotate overlay:", rotate?.includes("ROTATE YOUR DEVICE") ? "YES" : "NO");
await page.screenshot({ path: "scripts/shot-portrait.png" });

await browser.close();
server.close();
