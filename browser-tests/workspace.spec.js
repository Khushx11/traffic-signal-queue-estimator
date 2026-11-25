const {test, expect} = require("@playwright/test");
const fs = require("node:fs/promises");
const path = require("node:path");

test("loads sample, imports a recording and predictions, seeks and exports", async ({page}) => {
  await page.goto("/");
  await expect(page.locator("#source")).toContainText("Synthetic signal cycle");
  await expect(page.locator("#video")).toHaveJSProperty("videoWidth", 640);
  const fixture = path.join(__dirname, "../web/illustrative-cycle");
  await page.locator("#recording-file").setInputFiles(fixture + ".mp4");
  await expect(page.getByRole("status")).toContainText("Local video loaded");
  await page.locator("#predictions").setInputFiles(fixture + ".json");
  await expect(page.getByRole("status")).toHaveText("Predictions loaded.");
  const seek = page.getByRole("slider", {name: "Playback position"});
  await seek.focus();
  await seek.press("End");
  await expect(page.locator("#readout")).toContainText("6.0 s");
  expect(await page.locator("#video").evaluate(video => video.currentTime)).toBeCloseTo(6, 1);
  for (const format of ["CSV", "JSON"]) {
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", {name: "Export " + format}).click();
    const download = await downloadPromise;
    const text = await fs.readFile(await download.path(), "utf8");
    expect(download.suggestedFilename()).toBe("queue-counts." + format.toLowerCase());
    if (format === "CSV") expect(text).toContain("phase_source");
    else expect(JSON.parse(text)).toHaveLength(8);
  }
});

test("submits the selected recording and camera then loads the analysis", async ({page}) => {
  await page.route("**/analyze", async route => {
    expect(route.request().method()).toBe("POST");
    expect(JSON.parse(decodeURIComponent(route.request().headers()["x-camera-config"])).lanes).toEqual([]);
    expect(route.request().postDataBuffer().length).toBeGreaterThan(100);
    await route.fulfill({json: [{time: 0, lane: "A", state: "estimate", count: 3}]});
  });
  await page.goto("/");
  await expect(page.locator("#source")).toContainText("Synthetic signal cycle");
  await page.locator("#recording-file").setInputFiles(path.join(__dirname, "../web/illustrative-cycle.mp4"));
  await page.locator("#camera-config").setInputFiles({
    name: "camera.json", mimeType: "application/json", buffer: Buffer.from('{"lanes":[]}'),
  });
  await page.getByRole("button", {name: "Run local inference"}).click();
  await expect(page.getByRole("status")).toHaveText("Analysis complete.");
  await expect(page.locator("#readout")).toContainText("3 vehicles");
});
