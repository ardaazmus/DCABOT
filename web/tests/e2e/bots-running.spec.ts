import { expect, test, type Page } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

test.setTimeout(240_000);

const NAME = "E2E W-F5b slow";

async function createPaperBot(page: Page): Promise<string> {
  const response = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: {
      name: NAME,
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
  const body = (await response.json()) as { data: { bot_id: string } };
  return body.data.bot_id;
}

async function stopAndArchive(page: Page, botId: string) {
  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  if (!detail.ok()) return;
  let bot = ((await detail.json()) as { data: { status: string; revision: number } }).data;
  if (bot.status !== "STOPPED") {
    const stop = await page.request.post(`/api/v2/bots/${botId}/stop`, {
      data: { revision: bot.revision },
    });
    if (!stop.ok()) return;
    bot = ((await stop.json()) as { data: { status: string; revision: number } }).data;
  }
  await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision: bot.revision },
  });
}

test(
  "çalışan bot: Başlat → aktif deal → DEAL_STARTED olayı → durdur",
  { tag: "@slow" },
  async ({ page }) => {
    const botId = await createPaperBot(page);
    try {
      await page.goto(`/bots/${botId}`);
      await expect(page.getByRole("heading", { name: NAME, level: 1 })).toBeVisible({
        timeout: 15000,
      });
      await page.getByRole("button", { name: "Başlat" }).click();
      await expect(page.getByText("Çalışıyor").first()).toBeVisible({ timeout: 15000 });
      // İlk deal bir sonraki kapanan 1 dakikalık mumda açılır (≤150 sn).
      const dealCard = page.getByTestId("active-deal");
      await expect(dealCard.getByText("Ort. fiyat")).toBeVisible({ timeout: 150_000 });
      await page.getByRole("tab", { name: "Olay kaydı" }).click();
      await expect(page.getByTestId("events-timeline").getByText("Deal #1 açıldı")).toBeVisible({
        timeout: 30000,
      });
    } finally {
      await stopAndArchive(page, botId);
    }
  },
);
