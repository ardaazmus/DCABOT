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

async function createBot(
    page: Page,
    name: string,
    symbol = "BTCUSDT",
  ): Promise<{ bot_id: string; revision: number }> {
  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name, mode: "PAPER", budget: "1000", strategy: { ...DASHBOARD_BOT, symbol } },
  });
  return ((await created.json()) as { data: { bot_id: string; revision: number } }).data;
}

async function archiveBot(page: Page, botId: string, revision: number): Promise<void> {
  const archived = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision },
  });
  expect(archived.ok()).toBe(true);
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

  test("bot korelasyon kartı matris ya da dürüst hata gösterir", async ({ page }) => {
    const btc = await createBot(page, "E2E korelasyon btc", "BTCUSDT");
    const eth = await createBot(page, "E2E korelasyon eth", "ETHUSDT");
    try {
      await page.goto("/");
      const card = page.getByTestId("dashboard-correlation");
      await expect(card).toBeVisible();
      await expect(card.getByText("Bot korelasyonu")).toBeVisible();
      // Canlı klines tekil düşerse kart dürüst-hata gösterir; bir kez yenile.
      const table = card.locator("table");
      const alert = card.getByRole("alert");
      await expect(table.or(alert)).toBeVisible({ timeout: 30000 });
      if (await alert.isVisible()) {
        await page.reload();
        await expect(card).toBeVisible();
        await expect(table.or(alert)).toBeVisible({ timeout: 30000 });
      }
      if (await table.isVisible()) {
        await expect(table.getByRole("columnheader", { name: "BTCUSDT" })).toBeVisible();
        await expect(table.getByRole("rowheader", { name: "ETHUSDT" })).toBeVisible();
      }
    } finally {
      // Liste ekran görüntülerini kirletmemek için kendi botlarını arşivle.
      await archiveBot(page, btc.bot_id, btc.revision);
      await archiveBot(page, eth.bot_id, eth.revision);
    }
  });

  test("equity aralık seçimi grafiği korur", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Özsermaye")).toBeVisible();
    await page.getByRole("button", { name: "7G" }).click();
    await expect(page.getByText("Özsermaye")).toBeVisible();
  });
});
