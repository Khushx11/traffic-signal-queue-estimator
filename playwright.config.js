const {defineConfig} = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./browser-tests",
  use: {
    baseURL: "http://127.0.0.1:8019",
    launchOptions: process.env.QUEUE_CHROMIUM
      ? {executablePath: process.env.QUEUE_CHROMIUM}
      : {},
  },
  webServer: {
    command: "python3 -m http.server --bind 127.0.0.1 --directory web 8019",
    url: "http://127.0.0.1:8019",
    reuseExistingServer: false,
  },
});
