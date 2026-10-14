import { expect, test, type Page } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

const GRID = {
  symbol: "BTCUSDT",
  mode: "ARITHMETIC",
  lower_price: "20000",
  upper_price: "150000",
  interval_count: 10,
  fee_rate: "0.001",
  stop_loss_price: null,
  take_profit_pct: null,
  trailing_up_pct: null,
  trailing_down_pct: null,
};

async function createGridBot(page: Page, name: string): Promise<string> {
  const response = await postWithUpstreamRetry(page.request, "/api/v2/grid-bots", {
    data: { name, mode: "PAPER", budget: "1000", strategy: GRID },
  });
  const body = (await response.json()) as { data: { bot_id: string } };
  return body.data.bot_id;
}

const FUTURES_GRID = {
  ...GRID,
  upper_price: "95000",
  direction: "LONG",
  leverage: 5,
  fee_rate: "0.0005",
};

async function createFuturesGridBot(page: Page, name: string): Promise<string> {
  const response = await postWithUpstreamRetry(page.request, "/api/v2/futures-grid-bots", {
    data: { name, mode: "PAPER", budget: "1000", strategy: FUTURES_GRID },
  });
  const body = (await response.json()) as { data: { bot_id: string } };
  return body.data.bot_id;
}

async function archiveBot(page: Page, botId: string): Promise<void> {
  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  const bot = ((await detail.json()) as { data: { revision: number } }).data;
  const archive = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision: bot.revision },
  });
  expect(archive.ok()).toBe(true);
}

test("grid sihirbaz: tür seç → aralık → önizleme → oluştur → detay", async ({ page }) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  await page.getByTestId("wizard-type-grid").click();
  const next = page.getByRole("button", { name: "Devam" });
  await expect(next).toBeEnabled({ timeout: 15000 });
  await next.click();

  await page.getByTestId("grid-lower").fill("20000");
  await page.getByTestId("grid-upper").fill("150000");
  await page.getByTestId("grid-count").fill("10");
  await page.getByTestId("grid-budget").fill("1000");
  await page.getByTestId("grid-name").fill("E2E grid wizard");
  const preview = page.getByTestId("grid-preview-panel");
  await expect(preview.getByText("Grid başına")).toBeVisible({ timeout: 20000 });
  await expect(preview.getByText("100 USDT")).toBeVisible();

  await next.click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible();
  await page.getByTestId("wizard-create").click();
  await expect(page).toHaveURL(/\/bots\/bot_/, { timeout: 20000 });
  await expect(page.getByRole("heading", { name: "E2E grid wizard", level: 1 })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByRole("heading", { name: "Strateji" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Seviyeler" })).toBeVisible();
  await expect(page.getByTestId("grid-levels")).toBeVisible();

  const botId = page.url().split("/bots/")[1]?.split("?")[0] ?? "";
  expect(botId.startsWith("bot_")).toBe(true);
  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  const bot = ((await detail.json()) as { data: { revision: number } }).data;
  const archive = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision: bot.revision },
  });
  expect(archive.ok()).toBe(true);
});

test("futures grid sihirbaz: tür seç → yön+kaldıraç → önizleme → oluştur → detay @venue", async ({
  page,
}) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  await page.getByTestId("wizard-type-futures_grid").click();
  await page.getByTestId("grid-direction-short").click();
  const next = page.getByRole("button", { name: "Devam" });
  await expect(next).toBeEnabled({ timeout: 15000 });
  await next.click();

  await page.getByTestId("grid-lower").fill("20000");
  await page.getByTestId("grid-upper").fill("95000");
  await page.getByTestId("grid-count").fill("10");
  await page.getByTestId("grid-budget").fill("1000");
  await page.getByTestId("grid-leverage").fill("5");
  await page.getByTestId("grid-name").fill("E2E futures grid wizard");
  const preview = page.getByTestId("grid-preview-panel");
  await expect(preview.getByText("Grid başına", { exact: true })).toBeVisible({ timeout: 20000 });
  await expect(preview.getByText("100 USDT")).toBeVisible();
  await expect(preview.getByText("500 USDT")).toBeVisible();

  await next.click();
  await expect(page.getByTestId("wizard-step-3")).toBeVisible();
  await page.getByTestId("wizard-create").click();
  await expect(page).toHaveURL(/\/bots\/bot_/, { timeout: 20000 });
  await expect(page.getByRole("heading", { name: "E2E futures grid wizard", level: 1 })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByText("Vadeli Grid", { exact: true }).first()).toBeVisible();
  await expect(page.getByTestId("grid-levels")).toBeVisible();

  const botId = page.url().split("/bots/")[1]?.split("?")[0] ?? "";
  expect(botId.startsWith("bot_")).toBe(true);
  await archiveBot(page, botId);
});

test("grid yaşam döngüsü: başlat → durdur → arşivle", async ({ page }) => {
  const botId = await createGridBot(page, "E2E grid runner");
  await page.goto(`/bots/${botId}`);
  await expect(page.getByRole("heading", { name: "E2E grid runner", level: 1 })).toBeVisible({
    timeout: 15000,
  });
  await page.getByRole("button", { name: "Başlat" }).click();
  await expect(page.getByText("Çalışıyor").first()).toBeVisible({ timeout: 20000 });
  await expect(page.getByTestId("grid-levels")).toBeVisible();
  await page.getByRole("button", { name: "Durdur" }).click();
  await expect(page.getByText("Durdu").first()).toBeVisible({ timeout: 20000 });

  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  const bot = ((await detail.json()) as { data: { revision: number } }).data;
  const archive = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision: bot.revision },
  });
  expect(archive.ok()).toBe(true);
});

test("futures grid yaşam döngüsü: başlat → durdur → arşivle @venue", async ({ page }) => {
  const botId = await createFuturesGridBot(page, "E2E futures grid runner");
  await page.goto(`/bots/${botId}`);
  await expect(page.getByRole("heading", { name: "E2E futures grid runner", level: 1 })).toBeVisible({
    timeout: 15000,
  });
  await page.getByRole("button", { name: "Başlat" }).click();
  await expect(page.getByText("Çalışıyor").first()).toBeVisible({ timeout: 20000 });
  await expect(page.getByTestId("grid-levels")).toBeVisible();
  await page.getByRole("button", { name: "Durdur" }).click();
  await expect(page.getByText("Durdu").first()).toBeVisible({ timeout: 20000 });
  await archiveBot(page, botId);
});
