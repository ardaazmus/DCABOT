import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const PREFILL =
  "symbol=BTCUSDT&base_order=25&safety_order=25&max_so=6&max_active_so=2" +
  "&deviation=1.5&vol_scale=1.5&step_scale=1.2&tp=2&budget=1000" +
  "&interval=1h&start=2026-09-01&end=2026-09-14";

async function runBacktest(page: Page) {
  // e2e canlı Binance kullanır; tekil yukarı-akım isteği düşerse ürün
  // dürüst-hata gösterir (PUBLIC_UPSTREAM_UNAVAILABLE). Geçici aksaklıkla
  // gerçek kırığı ayırt etmek için hata görülürse sayfa BİR kez yenilenip
  // yeniden çalıştırılır; ikinci denemede de sonuç yoksa yüksek sesle düşer.
  for (let attempt = 1; attempt <= 2; attempt++) {
    if (attempt === 2) {
      await page.reload();
      await expect(page.getByTestId("backtest-run")).toBeEnabled({ timeout: 20000 });
    }
    await page.getByTestId("backtest-run").click();
    const results = page.getByTestId("backtest-results");
    const upstreamError = page.getByText("PUBLIC_UPSTREAM_UNAVAILABLE");
    await expect(results.or(upstreamError)).toBeVisible({ timeout: 60000 });
    if (!(await upstreamError.isVisible())) {
      await expect(results).toBeVisible({ timeout: 60000 });
      return;
    }
    if (attempt === 2) {
      throw new Error("Backtest iki denemede de PUBLIC_UPSTREAM_UNAVAILABLE verdi.");
    }
  }
}

test("BTCUSDT Dengeli 1h 14 gün: sonuç kartları ve grafikler", async ({ page }) => {
  await page.goto(`/backtest?${PREFILL}`);
  await expect(page.getByRole("heading", { name: "Backtest stüdyosu", level: 1 })).toBeVisible();
  await expect(page.getByTestId("backtest-estimate")).toContainText("336");
  await runBacktest(page);
  const results = page.getByTestId("backtest-results");
  await expect(results.getByText("Net kâr")).toBeVisible();
  await expect(results.getByText("Kazanma oranı")).toBeVisible();
  await expect(results.getByText("Profit Factor")).toBeVisible();
  await expect(page.getByTestId("trades-chart").locator("canvas").first()).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByTestId("equity-chart").locator("canvas").first()).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByTestId("drawdown-chart").locator("canvas").first()).toBeVisible({
    timeout: 15000,
  });
  await expect(results.getByText("Aylık getiri")).toBeVisible();
  await expect(results.getByText("SO kullanım dağılımı")).toBeVisible();
  await expect(results.getByText("Varsayımlar")).toBeVisible();
});

test("ikinci koşuda Yerel önbellekten rozeti", async ({ page }) => {
  await page.goto(`/backtest?${PREFILL}`);
  await expect(page.getByTestId("backtest-run")).toBeEnabled({ timeout: 20000 });
  await runBacktest(page);
  await runBacktest(page);
  await expect(page.getByText("Yerel önbellekten")).toBeVisible({ timeout: 15000 });
});

test("15m + 1 yıl: aralık uyarısı, çalıştırma yok", async ({ page }) => {
  await page.goto("/backtest?symbol=BTCUSDT&interval=15m&start=2025-09-01&end=2026-09-01");
  await expect(page.getByRole("heading", { name: "Backtest stüdyosu", level: 1 })).toBeVisible();
  await expect(
    page.getByText("Daha büyük zaman dilimi seçin ya da aralığı kısaltın."),
  ).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("backtest-run")).toBeHidden();
});

test("Bu ayarlarla bot kur: sihirbaz dolu gelir", async ({ page }) => {
  await page.goto(`/backtest?${PREFILL}`);
  await expect(page.getByTestId("backtest-run")).toBeEnabled({ timeout: 20000 });
  await runBacktest(page);
  await page.getByRole("link", { name: "Bu ayarlarla bot kur" }).click();
  await expect(page).toHaveURL(/\/bots\/new\?/);
  await expect(page.getByTestId("wizard-symbol")).toHaveValue("BTCUSDT");
  await expect(page.getByTestId("wizard-budget")).toHaveValue("1000");
});

test("Önce backtest et: stüdyo dolu gelir", async ({ page }) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "Önce backtest et" }).click();
  await expect(page).toHaveURL(/\/backtest\?/);
  await expect(page.getByTestId("wizard-symbol")).toHaveValue("BTCUSDT");
});

test("erişilebilirlik: kritik ihlal yok", async ({ page }) => {
  await page.goto(`/backtest?${PREFILL}`);
  await expect(page.getByTestId("backtest-run")).toBeEnabled({ timeout: 20000 });
  const formResults = await new AxeBuilder({ page }).analyze();
  expect(
    formResults.violations.filter((violation) => violation.impact === "critical"),
  ).toEqual([]);
  await runBacktest(page);
  const resultResults = await new AxeBuilder({ page }).analyze();
  expect(
    resultResults.violations.filter((violation) => violation.impact === "critical"),
  ).toEqual([]);
});

test("sonuç masaüstü: ekran görüntüsü ve görsel taban @visual", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`/backtest?${PREFILL}`);
  await expect(page.getByTestId("backtest-run")).toBeEnabled({ timeout: 20000 });
  await runBacktest(page);
  await expect(page.getByTestId("equity-chart").locator("canvas").first()).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({ path: "tests/e2e/screenshots/backtest-desktop.png", fullPage: true });
  await expect(page.locator("main")).toHaveScreenshot("backtest-desktop.png", {
    animations: "disabled",
    // Kaynak rozeti ilk koşuda VENUE olabilir; sayıların tamamı sabit aralıkta belirlidir.
    mask: [page.getByTestId("backtest-status")],
    maxDiffPixels: 800,
  });
});

test("sonuç mobil: ekran görüntüsü ve görsel taban @visual", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/backtest?${PREFILL}`);
  await expect(page.getByTestId("backtest-run")).toBeEnabled({ timeout: 20000 });
  await runBacktest(page);
  await page.screenshot({ path: "tests/e2e/screenshots/backtest-mobile.png", fullPage: true });
  await expect(page.locator("main")).toHaveScreenshot("backtest-mobile.png", {
    animations: "disabled",
    mask: [page.getByTestId("backtest-status")],
    maxDiffPixels: 800,
  });
});
