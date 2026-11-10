const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.resolve(__dirname, 'index.html')); await p.waitForTimeout(400);
  await p.screenshot({ path: path.resolve(__dirname, '../thumbnail.png') }); await b.close();
})();
