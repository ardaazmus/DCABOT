import { defineConfig, devices } from "@playwright/test";
import { join, resolve } from "node:path";

// e2e kendi API'sini (8771) ve web'i (3771) başlatır; geliştirme
// sunucuları (8770/3770) açık kalabilir. API durumu koşuya özel
// `web/.e2e-data-<runId>`'dedir; gerçek `data/` klasörüne dokunulmaz.
// (Playwright webServer'ı globalSetup'tan önce başlatır ve API kilit
// dosyasını açık tutar; sabit klasör koşu başında silinemez.)
const WEB_DIR = __dirname;
const REPO_ROOT = resolve(WEB_DIR, "..");
// Config her süreçte (ana + worker) yeniden değerlendirilir; koşu kimliği
// ilk değerlendirmede üretilip env ile miras bırakılır, hepsi aynı
// klasörü görür. Farklı çağrılar farklı kimlik alır (izolasyon).
let RUN_ID = process.env.DCABOT_E2E_RUN_ID;
if (!RUN_ID) {
  RUN_ID = `${Date.now()}-${process.pid}`;
  process.env.DCABOT_E2E_RUN_ID = RUN_ID;
}
const E2E_DATA = join(WEB_DIR, `.e2e-data-${RUN_ID}`);
process.env.DCABOT_E2E_DATA_DIR = E2E_DATA;

export default defineConfig({
  testDir: "./tests/e2e",
  globalSetup: "./tests/e2e/global-setup.ts",
  // Canlı backend yukarı-akım gecikmeli; testler tek işçide, uzun zaman
  // aşımıyla koşar. CI'da bir kez yeniden deneme yapılır.
  workers: 1,
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  // Taban görüntüler platform soneksizdir: CI (linux) ile yerel (win32)
  // aynı dosyayı karşılaştırır; yazı tipi pakette gömülü (Inter),
  // tolerans maxDiffPixels ile verilir.
  snapshotPathTemplate: "{testDir}/{testFileName}-snapshots/{arg}{ext}",
  webServer: [
    {
      command: "uv run --frozen uvicorn dcabot.server.api:app --host 127.0.0.1 --port 8771",
      cwd: REPO_ROOT,
      env: {
        PYTHONPATH: "src",
        DCABOT_DATA_DIR: E2E_DATA,
      },
      url: "http://127.0.0.1:8771/api/health",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      // Üretim derlemesi + start (dev sunucusuyla çakışmaz); env'i betik kurar.
      command: "node ./scripts/e2e-serve.mjs",
      cwd: WEB_DIR,
      url: "http://127.0.0.1:3771",
      // E2E_VERBOSE=1 kabul koşularında sunucu günlüğünü kanıt için akıtır.
      stdout: process.env.E2E_VERBOSE ? "pipe" : "ignore",
      stderr: process.env.E2E_VERBOSE ? "pipe" : "ignore",
      reuseExistingServer: false,
      timeout: 300_000,
    },
  ],
  use: {
    baseURL: "http://127.0.0.1:3771",
    trace: "retain-on-failure",
  },
  projects: [
    // Tohumlama: API uçlarıyla dataset + geçmiş koşu üretir.
    // Başarısız olursa chromium koşmaz (sessiz atlama yok).
    { name: "setup", testMatch: /tests\/e2e\/setup\/.*\.spec\.ts/ },
    {
      name: "chromium",
      testIgnore: /tests\/e2e\/setup\/.*\.spec\.ts/,
      dependencies: ["setup"],
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
