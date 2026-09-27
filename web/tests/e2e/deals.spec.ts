import { expect, test, type Page } from "@playwright/test";
import { postWithUpstreamRetry } from "./market-ready";

const NAME = "E2E W-F6 slow";

async function createPaperBot(page: Page): Promise<{ botId: string; revision: number }> {
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
  const body = (await response.json()) as { data: { bot_id: string; revision: number } };
  return { botId: body.data.bot_id, revision: body.data.revision };
}

async function stopAndArchive(page: Page, botId: string): Promise<void> {
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

test("deal listesi: sekmeler açılır", async ({ page }) => {
  // Diğer spec'ler deal bırakabilir; içerik değil sekmeler doğrulanır.
  await page.goto("/deals");
  await expect(page.getByRole("heading", { name: "Deal'ler" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Aktif" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("deals-active")).toBeVisible();
  await page.getByRole("tab", { name: "Geçmiş" }).click();
  await expect(page.getByTestId("deals-history")).toBeVisible();
});

test("deal detayı: bilinmeyen kimlikte bulunamadı", async ({ page }) => {
  await page.goto("/deals/bot_yok:1");
  await expect(page.getByRole("heading", { name: "Deal bulunamadı" })).toBeVisible();
  await page.goto("/deals/bozuk-kimlik");
  await expect(page.getByRole("heading", { name: "Deal bulunamadı" })).toBeVisible();
});

test.setTimeout(240_000);

test(
  "deal aksiyonları: fon ekle → piyasadan kapat → geçmişte görünür @slow",
  { tag: "@slow" },
  async ({ page }) => {
    const { botId, revision } = await createPaperBot(page);
    const start = await page.request.post(`/api/v2/bots/${botId}/start`, {
      data: { revision },
    });
    expect(start.ok()).toBe(true);

    // İlk deal bir sonraki kapanan 1 dakikalık mumda açılır.
    let opened = false;
    for (let i = 0; i < 24; i++) {
      const active = await page.request.get("/api/v2/deals?status=active&limit=100");
      const rows = ((await active.json()) as { data: { bot_id: string }[] }).data;
      if (rows.some((row) => row.bot_id === botId)) {
        opened = true;
        break;
      }
      await page.waitForTimeout(10_000);
    }
    expect(opened).toBe(true);

    await page.goto(`/deals/${botId}:1`);
    await expect(page.getByRole("heading", { name: "Deal #1" })).toBeVisible();
    await expect(page.getByTestId("deal-chart")).toBeVisible();

    await page.getByRole("button", { name: "Fon ekle" }).click();
    await page.getByTestId("add-funds-amount").fill("25");
    await page.getByRole("button", { name: "Al", exact: true }).click();
    await expect(page.getByTestId("deal-fills")).toContainText("Manuel #1");

    await page.getByRole("button", { name: "Piyasadan kapat" }).click();
    await page.getByRole("button", { name: "Deal'i kapat" }).click();
    await expect(page.getByTestId("deal-fills")).toContainText("Satış");

    // F10a: kapanan deal brüt/net/ücret dökümü.
    await page.goto(`/deals/${botId}:1`);
    await expect(page.getByRole("heading", { name: "Deal #1" })).toBeVisible();
    const grossRow = page.getByText("Brüt kâr", { exact: true }).locator("..");
    const feesRow = page.getByText("Ücretler", { exact: true }).locator("..");
    await expect(grossRow).not.toContainText("—");
    await expect(feesRow).not.toContainText("—");
    await expect(feesRow).toContainText("USDT");

    await page.goto("/deals");
    await page.getByRole("tab", { name: "Geçmiş" }).click();
    const history = page.getByTestId("deals-history");
    const row = history.getByRole("row").filter({ hasText: NAME });
    await expect(row).toContainText("Manuel kapatma");
    await expect(row).toContainText("#1");

    await stopAndArchive(page, botId);
  },
);
