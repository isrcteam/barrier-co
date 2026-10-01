import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(name);
  return i === -1 ? def : args.splice(i, 2)[1];
};
const out = opt('--out', 'docs/qa/screens/live');
const password = opt('--password', process.env.STORE_PASSWORD || '');
const [base, ...paths] = args;
if (!base) {
  console.error('Usage: node capture.mjs <base-url> [paths...] [--out folder] [--password storefront-password]');
  console.error('Preview theme: pass the base with ?preview_theme_id=<id>; it is kept on every path.');
  process.exit(1);
}
const WIDTHS = { 'desktop-1920': 1920, 'desktop-1440': 1440, 'desktop-1280': 1280, 'ipad-landscape': 1180, 'ipad-portrait': 820, 'iphone': 390 };
const baseUrl = new URL(base);
const keep = baseUrl.searchParams;
const list = paths.length ? paths : ['/', '/collections/all', '/cart'];
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const manifest = [];
for (const [label, width] of Object.entries(WIDTHS)) {
  const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce', deviceScaleFactor: 1 });
  if (password) {
    const p = await context.newPage();
    await p.goto(new URL('/password', baseUrl).toString());
    await p.fill('input[type="password"]', password).catch(() => {});
    await p.keyboard.press('Enter').catch(() => {});
    await p.waitForLoadState('networkidle').catch(() => {});
    await p.close();
  }
  for (const path of list) {
    const url = new URL(path, baseUrl);
    keep.forEach((v, k) => url.searchParams.set(k, v));
    const page = await context.newPage();
    await page.goto(url.toString(), { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
    await page.addStyleTag({ content: '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important} [id*="preview-bar"],#PBarNextFrameWrapper,iframe#preview-bar-iframe{display:none!important}' });
    await page.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 600) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 120));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(800);
    const slug = (path === '/' ? 'home' : path.replace(/^\/|\/$/g, '').replace(/[^a-z0-9]+/gi, '-')).toLowerCase();
    const file = join(out, `${slug}--${label}.png`);
    await page.screenshot({ path: file, fullPage: true });
    manifest.push({ path, width: label, file });
    await page.close();
  }
  await context.close();
}
await browser.close();
writeFileSync(join(out, 'manifest.json'), JSON.stringify({ base, captured: new Date().toISOString(), shots: manifest }, null, 2));
console.log(`Captured ${manifest.length} screenshots to ${out}`);
