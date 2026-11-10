// Bake computed CSS into inline attributes of an SVG and drop its <style> blocks.
// Why: a HyperFrames scene is mounted inside a larger page, and Mermaid's id-scoped <style> rules do not survive that.
// usage: node bake_svg_styles.js in.svg out.svg      (needs Playwright; resolves it from NODE_PATH or /opt/node-tools)
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }
const fs = require('fs');
(async () => {
  const [src, dst] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.setContent('<body style="margin:0;background:#000">' + fs.readFileSync(src, 'utf8') + '</body>');
  const out = await p.evaluate(() => {
    const svg = document.querySelector('svg');
    const props = ['fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-linecap', 'opacity', 'font-family', 'font-size', 'font-weight', 'text-anchor', 'filter', 'color', 'dominant-baseline'];
    svg.querySelectorAll('*').forEach(el => {
      if (el.closest('defs') && el.tagName !== 'marker' && !el.closest('marker')) return;
      const cs = getComputedStyle(el);
      props.forEach(pn => {
        const v = cs.getPropertyValue(pn);
        if (v && v !== 'normal' && v !== 'none' && !(pn === 'opacity' && v === '1')) el.style.setProperty(pn, v);
        else if (pn === 'fill' && v === 'none') el.style.setProperty('fill', 'none');
        else if (pn === 'stroke' && v === 'none') el.style.setProperty('stroke', 'none');
      });
      el.style.removeProperty('filter');           // drop-shadow filters read as glow halos on black; skip them
    });
    svg.querySelectorAll('style').forEach(s => s.remove());
    return svg.outerHTML;
  });
  fs.writeFileSync(dst, out);
  await b.close();
})();
