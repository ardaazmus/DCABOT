import { expect, test, type Page } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

/**
 * W-F4.1 düzeltme 1: 390 px'te hiçbir rota yatay taşma yapmaz.
 * `scrollWidth <= innerWidth` bütün rotalarda zorunludur.
 */
const ROUTES: string[] = [
  "/",
  "/bots",
  "/bots/new?symbol=BTCUSDT",
  "/market",
  "/market/BTCUSDT",
  "/deals",
  "/backtest",
  "/design",
  "/settings/connection",
  "/settings/risk",
  "/settings/data",
  "/settings/system",
  "/settings/preferences",
];

async function expectNoOverflow(page: Page, path: string) {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(path);
  // Mobil çekmecedeki gizli bağlantılar değil, ana alandaki başlık beklenir.
  await expect(page.locator("main").getByRole("heading").first()).toBeVisible({
    timeout: 20000,
  });
  // Geç yüklenen grafikler yerleşsin diye kısa bekleme.
  await page.waitForTimeout(1500);
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  expect(
    overflow.scrollWidth,
    `${path}: scrollWidth ${overflow.scrollWidth} > innerWidth ${overflow.innerWidth}`,
  ).toBeLessThanOrEqual(overflow.innerWidth);
}

for (const route of ROUTES) {
  test(`taşma yok: ${route}`, async ({ page }) => {
    await expectNoOverflow(page, route);
  });
}

test("taşma yok: sihirbaz yüklü önizlemeyle", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();
  await page.getByTestId("wizard-budget").fill("1000");
  await expect(page.getByTestId("preview-panel").getByText("Gereken sermaye")).toBeVisible({
    timeout: 20000,
  });
  await expect(page.getByTestId("plan-chart").locator("canvas").first()).toBeVisible({
    timeout: 20000,
  });
  await page.waitForTimeout(1500);
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  expect(
    overflow.scrollWidth,
    `sihirbaz yüklü: scrollWidth ${overflow.scrollWidth} > innerWidth ${overflow.innerWidth}`,
  ).toBeLessThanOrEqual(overflow.innerWidth);
});

test("taşma yok: bot detayı", async ({ page }) => {
  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: {
      name: "E2E overflow",
      mode: "PAPER",
      budget: "1000",
      strategy: {
        symbol: "BTCUSDT",
        base_order: "25",
        safety_order: "25",
        max_safety_orders: 6,
        max_active_safety_orders: 2,
        price_deviation: "1.5",
        safety_order_volume_scale: "1.5",
        safety_order_step_scale: "1.2",
        take_profit: "2",
        stop_loss: null,
      },
    },
  });
  const body = (await created.json()) as { data: { bot_id: string; revision: number } };
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/bots/${body.data.bot_id}`);
    await expect(page.getByRole("heading", { name: "E2E overflow", level: 1 })).toBeVisible({
      timeout: 20000,
    });
    await expect(page.getByTestId("preview-panel").getByText("Gereken sermaye")).toBeVisible({
      timeout: 20000,
    });
    await page.waitForTimeout(1500);
    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    expect(
      overflow.scrollWidth,
      `bot detayı: scrollWidth ${overflow.scrollWidth} > innerWidth ${overflow.innerWidth}`,
    ).toBeLessThanOrEqual(overflow.innerWidth);
  } finally {
    await page.request.post(`/api/v2/bots/${body.data.bot_id}/archive`, {
      data: { revision: body.data.revision },
    });
  }
});
