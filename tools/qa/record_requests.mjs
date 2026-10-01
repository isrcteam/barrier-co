import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';

const [, , base, ...paths] = process.argv;
if (!base) {
  console.error('Usage: node record_requests.mjs https://store.com / /collections/all /products/some-product /cart');
  process.exit(1);
}
const origin = new URL(base).host;
const pages = paths.length ? paths : ['/', '/collections/all', '/cart'];
const result = {};
const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1' });
for (const path of pages) {
  const page = await context.newPage();
  page.on('response', async (res) => {
    const host = new URL(res.url()).host;
    if (host === origin || host.endsWith('shopify.com') || host.endsWith('shopifycdn.com') || host.endsWith('shopifycloud.com')) return;
    let bytes = 0;
    try { bytes = (await res.body()).length; } catch { bytes = Number(res.headers()['content-length'] || 0); }
    const entry = (result[host] ??= { count: 0, bytes: 0, pages: [] });
    entry.count += 1;
    entry.bytes += bytes;
    if (!entry.pages.includes(path)) entry.pages.push(path);
  });
  await page.goto(new URL(path, base).toString(), { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await page.close();
}
await browser.close();
writeFileSync('docs/data/third-party-requests.json', JSON.stringify(result, null, 2));
console.log(`Recorded ${Object.keys(result).length} third-party domains across ${pages.length} pages to docs/data/third-party-requests.json`);
