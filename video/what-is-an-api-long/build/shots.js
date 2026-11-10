const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const targets = [
    ['mdn_http_overview', 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview', 1600, 900],
    ['postman_state_2025', 'https://www.postman.com/state-of-api/2025/', 1600, 900],
  ];
  for (const [name, url, w, h] of targets) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: 'dark', deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    try {
      await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await p.waitForTimeout(3500);
      await p.screenshot({ path: `../hf/assets/shots/${name}.png` });
      console.log('ok', name);
    } catch (e) { console.log('fail', name, e.message.slice(0,120)); }
    await ctx.close();
  }
  await b.close();
})();
