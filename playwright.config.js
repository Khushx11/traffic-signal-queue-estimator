const {defineConfig} = require("@playwright/test");

const compare = process.env.QUEUE_COMPARE_WEIGHTS ? ' --compare-weights "$QUEUE_COMPARE_WEIGHTS"' : "";

module.exports = defineConfig({
  testDir: "./browser-tests",
  use: {
    baseURL: "http://127.0.0.1:8019",
    launchOptions: process.env.QUEUE_CHROMIUM
      ? {executablePath: process.env.QUEUE_CHROMIUM}
      : {},
  },
  webServer: {
    command: process.env.QUEUE_REAL_INFERENCE
      ? '"$QUEUE_VIDEO_PYTHON" scripts/serve.py --weights "$QUEUE_VIDEO_WEIGHTS" --port 8019' + compare
      : "python3 -m http.server --bind 127.0.0.1 --directory web 8019",
    timeout: 30000,
    url: "http://127.0.0.1:8019",
    reuseExistingServer: false,
  },
});
