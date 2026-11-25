const {test, expect} = require("@playwright/test");
const path = require("node:path");

test("runs actual inference via the local upload endpoint", async ({page}) => {
  test.skip(!process.env.QUEUE_REAL_INFERENCE, "Requires the local video dependencies and checkpoint");
  test.setTimeout(120000);
  await page.goto("/");
  await expect(page.locator("#source")).toContainText("Synthetic signal cycle");
  const video = process.env.QUEUE_TEST_VIDEO || path.join(__dirname, "../web/illustrative-cycle.mp4");
  const camera = {
    provenance: "Integration-test geometry for 640-pixel-wide fixtures",
    image_anchors: [[0, 200], [640, 200], [640, 299], [0, 299]],
    ground_anchors: [[0, 0], [10, 0], [10, 30], [0, 30]],
    lanes: [{id: "fixture", polygon: [[0, 202], [640, 202], [640, 299], [0, 299]],
             stop: [300, 202], visible_end: [300, 298]}],
  };
  await page.locator("#recording-file").setInputFiles(video);
  await page.locator("#camera-config").setInputFiles({
    name: "camera.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(camera)),
  });
  const result = page.waitForResponse(response => response.url().endsWith("/analyze"));
  await page.getByRole("button", {name: "Run local inference"}).click();
  const response = await result;
  expect(response.ok()).toBeTruthy();
  const rows = await response.json();
  expect(rows.length).toBeGreaterThan(1);
  expect(rows[0]).toMatchObject({lane: "fixture", recording: "local-upload", time: 0});
  expect(rows.every(row => row.count === null || Number.isInteger(row.count))).toBe(true);
  await expect(page.getByRole("status")).toHaveText("Analysis complete.");
});
