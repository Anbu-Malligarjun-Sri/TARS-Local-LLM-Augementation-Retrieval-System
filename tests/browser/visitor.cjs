// Run against a loopback visitor preview with playwright-core and a Chromium executable.
const assert = require("node:assert/strict");
const { chromium } = require("playwright-core");

async function main() {
  const browser = await chromium.launch({ executablePath: process.env.VISITOR_BROWSER, headless: true });
  const url = "http://visitor.localhost:8091/";
  const errors = [];
  const urls = new Set();
  function observe(page) {
    page.on("pageerror", error => errors.push(error.message));
    page.on("request", request => urls.add(request.url()));
  }
  async function complete(page, scene) {
    await page.locator("#scenes button").nth(scene).click();
    await page.locator("#stop").waitFor({ state: "hidden" });
    return page.locator(".line:not(.user) span").last().textContent();
  }
  try {
    const desktop = await browser.newContext({ viewport: { width: 1152, height: 800 } });
    const page = await desktop.newPage();
    observe(page);
    await page.goto(url);
    await page.getByRole("button", { name: "Start visit" }).click();
    await page.locator("#composer").waitFor();
    assert.equal(await page.locator("#quota").innerText(), "5 turns left");

    // Hold the prepare response until Stop has been clicked. The server has already assigned an ID.
    await page.evaluate(() => {
      const original = window.fetch;
      const held = new Promise(resolve => { window.releasePrepare = resolve; });
      window.fetch = async (...args) => {
        const response = await original(...args);
        if (args[0] === "/demo/turns") {
          window.fetch = original;
          window.prepareArrived = true;
          await held;
        }
        return response;
      };
    });
    await page.locator("#scenes button").nth(1).click();
    await page.waitForFunction(() => window.prepareArrived);
    await page.getByRole("button", { name: "Stop", exact: true }).click();
    await page.evaluate(() => window.releasePrepare());
    await page.locator("#stop").waitFor({ state: "hidden" });
    assert.match(await complete(page, 2), /haven't/);
    await complete(page, 1);
    await page.reload();
    await page.locator("#composer").waitFor();
    assert.equal(await page.locator(".line").count(), 0);
    assert.equal(await page.locator("#quota").innerText(), "2 turns left");
    await page.locator("#language").selectOption("ta");
    assert.match(await complete(page, 2), /உன் திட்டத்தின் பெயர் Firefly/);
    await page.locator("#language").selectOption("tanglish");
    assert.match(await complete(page, 2), /Un project peru Firefly/);
    assert.ok(await page.locator("#message").isDisabled());
    const sibling = await desktop.newPage();
    await sibling.goto(url);
    await sibling.locator("#composer").waitFor();
    await sibling.getByRole("button", { name: "End visit" }).click();
    await page.locator("#welcome").waitFor();
    assert.equal(await page.locator(".line").count(), 0);

    const mobile = await browser.newContext({ viewport: { width: 360, height: 740 }, isMobile: true });
    const phone = await mobile.newPage();
    observe(phone);
    await phone.clock.install();
    await phone.goto(url);
    await phone.locator("#start").click();
    assert.match(await complete(phone, 2), /haven't/);
    await phone.locator("#scenes button").nth(1).click();
    await phone.waitForSelector('#robot[data-state="replying"]');
    await phone.locator("#stop").click();
    await phone.locator("#stop").waitFor({ state: "hidden" });
    assert.match(await complete(phone, 2), /haven't/);
    await phone.locator("#message").fill("<b>hello</b>");
    await phone.locator("#send").click();
    await phone.locator("#stop").waitFor({ state: "hidden" });
    assert.match(await phone.locator(".line:not(.user) span").last().innerText(), /three scripted scenes/);
    assert.equal(await phone.locator(".line.user span b").count(), 0);
    assert.ok(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await phone.locator("#end").click();

    // A failed stream request leaves a prepared turn on the server. Refresh finds it
    // and Stop releases it without committing its pending memory or refunding the turn.
    await phone.locator("#start").click();
    await phone.route("**/stream", route => route.abort(), { times: 1 });
    await phone.locator("#scenes button").nth(1).click();
    await phone.locator("#recheck").waitFor();
    await phone.reload();
    await phone.locator("#stop").click();
    await phone.locator("#stop").waitFor({ state: "hidden" });
    assert.equal(await phone.locator("#quota").innerText(), "4 turns left");
    assert.match(await complete(phone, 2), /haven't/);
    await phone.clock.fastForward(901000);
    // Date may advance while the page is suspended between timer ticks.
    await phone.locator("#welcome").waitFor();
    assert.equal(await phone.locator(".line").count(), 0);
    assert.deepEqual(errors, []);
    assert.ok([...urls].every(resource => new URL(resource).origin === new URL(url).origin));
    console.log("Passed desktop and mobile viewport, scoped memory, Stop, refresh, quotas, Unicode and same-origin requests.");
  } finally { await browser.close(); }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
