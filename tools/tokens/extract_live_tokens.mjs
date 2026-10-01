import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const [, , base, ...paths] = process.argv;
if (!base) {
  console.error('Usage: node extract_live_tokens.mjs https://store.com / /collections/all /products/x /cart');
  process.exit(1);
}
const list = paths.length ? paths : ['/', '/collections/all', '/cart'];
const tally = { color: {}, background: {}, border: {}, fontSize: {}, fontFamily: {}, fontWeight: {}, lineHeight: {}, spacing: {}, radius: {} };
const add = (group, value) => {
  if (!value || value === 'normal' || value === 'none' || value === '0px' || value === 'rgba(0, 0, 0, 0)') return;
  tally[group][value] = (tally[group][value] || 0) + 1;
};
const browser = await chromium.launch();
for (const width of [1440, 390]) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  for (const path of list) {
    await page.goto(new URL(path, base).toString(), { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
    const styles = await page.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        const s = getComputedStyle(el);
        if (s.visibility === 'hidden' || s.display === 'none') continue;
        const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        out.push({
          color: hasText ? s.color : null, background: s.backgroundColor, border: s.borderTopWidth !== '0px' ? s.borderTopColor : null,
          fontSize: hasText ? s.fontSize : null, fontFamily: hasText ? s.fontFamily.split(',')[0].replace(/["']/g, '').trim() : null,
          fontWeight: hasText ? s.fontWeight : null, lineHeight: hasText ? s.lineHeight : null,
          spacing: [s.paddingTop, s.paddingBottom, s.paddingLeft, s.marginTop, s.marginBottom, s.rowGap, s.columnGap],
          radius: s.borderTopLeftRadius,
        });
      }
      return out;
    });
    for (const st of styles) {
      for (const k of ['color', 'background', 'border', 'fontSize', 'fontFamily', 'fontWeight', 'lineHeight', 'radius']) add(k, st[k]);
      for (const v of st.spacing) add('spacing', v);
    }
  }
  await page.close();
}
await browser.close();
const toHex = (rgb) => {
  const m = rgb.match(/\d+(\.\d+)?/g);
  if (!m) return rgb;
  const [r, g, b, a] = m.map(Number);
  const hex = '#' + [r, g, b].map((n) => n.toString(16).padStart(2, '0')).join('').toUpperCase();
  return a !== undefined && a < 1 ? `${hex} @${a}` : hex;
};
const sorted = {};
for (const [group, values] of Object.entries(tally)) {
  let entries = Object.entries(values);
  if (['color', 'background', 'border'].includes(group)) {
    const merged = {};
    for (const [v, n] of entries) merged[toHex(v)] = (merged[toHex(v)] || 0) + n;
    entries = Object.entries(merged);
  }
  sorted[group] = entries.sort((x, y) => y[1] - x[1]);
}
mkdirSync('docs/data', { recursive: true });
writeFileSync('docs/data/live-styles.json', JSON.stringify(sorted, null, 2));
const lines = ['# Styles in use on the live site', '', `Source: ${base} (${list.join(', ')}) at 1440 and 390 px. Count = elements using the value.`, ''];
for (const [group, entries] of Object.entries(sorted)) {
  lines.push(`## ${group}`, '', '| Value | Count |', '| --- | --- |', ...entries.slice(0, 40).map(([v, n]) => `| ${v} | ${n} |`), '');
}
writeFileSync('docs/data/live-styles.md', lines.join('\n'));
console.log('Wrote docs/data/live-styles.json and docs/data/live-styles.md. Near-duplicate values are merge questions for the designer or client, never silent changes.');
