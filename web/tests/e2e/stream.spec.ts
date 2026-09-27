import { expect, test } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

const DENGELI = {
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

test("SSE: akış canlı, bot kurma ve arşivleme listeye anında yansır", async ({ page }) => {
  await page.goto("/bots");
  // Bot listesinde yoklama yok; görünme/kaybolma yalnız SSE ile olur.
  await expect(page.locator("span[data-stream]")).toHaveAttribute("data-stream", "live", {
    timeout: 15000,
  });

  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name: "E2E stream", mode: "PAPER", budget: "1000", strategy: DENGELI },
  });
  const botId = ((await created.json()) as { data: { bot_id: string } }).data.bot_id;
  await expect(page.getByRole("link", { name: "E2E stream" })).toBeVisible({ timeout: 10000 });

  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  const revision = ((await detail.json()) as { data: { revision: number } }).data.revision;
  const archived = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision },
  });
  expect(archived.ok()).toBe(true);
  await expect(page.getByRole("link", { name: "E2E stream" })).toBeHidden({ timeout: 15000 });
});
