import { expect, test, type Page } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

const DASHBOARD_BOT = {
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
};

async function createBot(page: Page, name: string): Promise<void> {
  await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name, mode: "PAPER", budget: "1000", strategy: DASHBOARD_BOT },
  });
}

test.describe("kontrol merkezi", () => {
  test("bot kırılımı ve KPI bölümleri görünür", async ({ page }) => {
    // Sabit isim: liste ekran görüntüleri koşudan koşuya aynı kalır.
    const name = "E2E panel";
    await createBot(page, name);
    await page.goto("/");
    await expect(page.getByTestId("dashboard-kpis")).toBeVisible();
    await expect(page.getByText("Özsermaye")).toBeVisible();
    await expect(page.getByText("Günlük kâr")).toBeVisible();
    // Kendi botu kırılımda adı ve sıfır kârıyla görünür.
    const row = page.getByRole("link", { name });
    await expect(row).toBeVisible();
    await expect(page.getByText("Aktif deal'ler")).toBeVisible();
  });

  test("equity aralık seçimi grafiği korur", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Özsermaye")).toBeVisible();
    await page.getByRole("button", { name: "7G" }).click();
    await expect(page.getByText("Özsermaye")).toBeVisible();
  });
});
