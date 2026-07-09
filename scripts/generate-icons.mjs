/**
 * Renders public/icon.svg to the PNG sizes PWA manifests + iOS need.
 * Run: node scripts/generate-icons.mjs
 */
import { chromium } from "playwright-core";
import { readFileSync } from "node:fs";

const svg = readFileSync(new URL("../public/icon.svg", import.meta.url), "utf8");
const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });

for (const size of [180, 192, 512]) {
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  await page.setContent(
    `<body style="margin:0"><div style="width:${size}px;height:${size}px;image-rendering:pixelated">
       ${svg.replace("<svg ", `<svg width="${size}" height="${size}" `)}
     </div></body>`,
  );
  await page.screenshot({ path: new URL(`../public/icon-${size}.png`, import.meta.url).pathname });
  await page.close();
  console.log(`wrote public/icon-${size}.png`);
}
await browser.close();
