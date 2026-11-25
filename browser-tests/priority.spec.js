const {test, expect} = require("@playwright/test");

test("prioritises a busy approach after pedestrian clearance, then serves the others", async ({page}) => {
  await page.goto("/");
  await expect(page.locator("#priority-summary")).toContainText("Highest reported demand: East");
  await expect(page.locator("#priority-order li").first()).toContainText("Walk");
  await expect(page.locator("#priority-order li").nth(3)).toContainText("East · Queue threshold reached");
  await page.locator("#priority-threshold").fill("20");
  await page.getByRole("button", {name: "Compare and plan"}).click();
  await expect(page.locator("#priority-order li").nth(3)).toContainText("North · Regular service");
  await page.locator("#crossing-calls").fill("North crossing=16\nEast crossing=12");
  await page.getByRole("button", {name: "Compare and plan"}).click();
  await expect(page.locator("#priority-order li").nth(3)).toContainText("East crossing · Walk");
});
