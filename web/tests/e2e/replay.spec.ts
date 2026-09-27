import { expect, test, type Page } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

// 2880 mum + venue indirme: varsayılan 60 sn yetmez.
test.setTimeout(300_000);

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

const GRID = {
  symbol: "BTCUSDT",
  mode: "ARITHMETIC",
  lower_price: "80000",
  upper_price: "89000",
  interval_count: 9,
  fee_rate: "0.001",
  stop_loss_price: null,
  take_profit_pct: null,
  trailing_up_pct: null,
  trailing_down_pct: null,
};

function isoDaysAgo(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

async function archiveBot(page: Page, botId: string) {
  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  const bot = ((await detail.json()) as { data: { status: string; revision: number } }).data;
  const response = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision: bot.revision },
  });
  expect(response.ok()).toBe(true);
}

async function runReplay(page: Page, botId: string) {
  await page.goto(`/bots/${botId}`);
  await expect(page.getByRole("heading", { name: "Geçmişte çalıştır" })).toBeVisible({
    timeout: 20000,
  });
  await page.getByTestId("replay-start").fill(isoDaysAgo(2));
  await page.getByTestId("replay-end").fill(isoDaysAgo(1));
  // Canlı yukarı-akım teklemesi: backtest ile aynı tek-tekrar disiplini.
  for (let attempt = 1; attempt <= 2; attempt++) {
    await page.getByTestId("replay-run").click();
    const result = page.getByTestId("replay-result");
    const upstreamError = page.getByText("PUBLIC_UPSTREAM_UNAVAILABLE");
    await expect(result.or(upstreamError)).toBeVisible({ timeout: 120000 });
    if (!(await upstreamError.isVisible())) return result;
    if (attempt === 2) {
      throw new Error("Replay iki denemede de PUBLIC_UPSTREAM_UNAVAILABLE verdi.");
    }
    await page.reload();
    await expect(page.getByRole("heading", { name: "Geçmişte çalıştır" })).toBeVisible({
      timeout: 20000,
    });
    await page.getByTestId("replay-start").fill(isoDaysAgo(2));
    await page.getByTestId("replay-end").fill(isoDaysAgo(1));
  }
  throw new Error("Ulaşılamaz.");
}

test("DCA replay: 2 gün çalışır, deal'ler detaya düşer", async ({ page }) => {
  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name: "E2E replay DCA", mode: "PAPER", budget: "1000", strategy: DENGELI },
  });
  const botId = ((await created.json()) as { data: { bot_id: string } }).data.bot_id;
  try {
    const result = await runReplay(page, botId);
    const text = (await result.textContent()) ?? "";
    expect(text).toContain("2880 mum");
    expect(text).toMatch(/[1-9][0-9]* deal açıldı/);
    const deals = await page.request.get(`/api/v2/bots/${botId}/deals`);
    expect(deals.ok()).toBe(true);
    expect((((await deals.json()) as { data: unknown[] }).data).length).toBeGreaterThanOrEqual(1);
  } finally {
    await archiveBot(page, botId);
  }
});

test("grid replay: 2 gün çalışır, runtime yazılır", async ({ page }) => {
  const created = await postWithUpstreamRetry(page.request, "/api/v2/grid-bots", {
    data: { name: "E2E replay grid", mode: "PAPER", budget: "900", strategy: GRID },
  });
  const botId = ((await created.json()) as { data: { bot_id: string } }).data.bot_id;
  try {
    const result = await runReplay(page, botId);
    await expect(result).toContainText("2880 mum");
    const state = await page.request.get(`/api/v2/bots/${botId}/grid`);
    expect(state.ok()).toBe(true);
    expect(((await state.json()) as { data: { last_bar_open_us: number | null } }).data.last_bar_open_us).not.toBeNull();
  } finally {
    await archiveBot(page, botId);
  }
});
