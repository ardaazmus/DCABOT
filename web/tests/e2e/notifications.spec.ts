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

test("bildirim: rozet belirir, okundu temizler, merkez listeler", async ({ page }) => {
  // Önceki speclerin olayları okundu sayılır; sayaç sıfırdan başlar.
  await page.request.post("/api/notifications/read", { data: { upto_seq: 999999 } });
  await page.goto("/bots");
  await expect(page.getByLabel("Bildirimler")).toBeVisible({ timeout: 15000 });

  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name: "E2E notify", mode: "PAPER", budget: "1000", strategy: DENGELI },
  });
  const botId = ((await created.json()) as { data: { bot_id: string } }).data.bot_id;

  // Rozet SSE ile, yeniden yüklemeden belirir.
  await expect(page.getByLabel("1 okunmamış bildirim")).toBeVisible({ timeout: 10000 });

  await page.getByLabel("1 okunmamış bildirim").click();
  await expect(page.getByText("Bot oluşturuldu (E2E notify).")).toBeVisible({ timeout: 10000 });
  await page.getByRole("button", { name: "Tümünü okundu işaretle" }).click();
  await expect(page.getByLabel("Bildirimler")).toBeVisible({ timeout: 10000 });

  // Merkez sayfası geçmişi listeler.
  await page.goto("/notifications");
  await expect(page.getByRole("heading", { name: "Bildirimler", level: 1 })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByText("Bot oluşturuldu (E2E notify).")).toBeVisible({ timeout: 10000 });

  // Okundu durumu yeniden yüklemede sürer (backend).
  await page.goto("/bots");
  await expect(page.getByLabel("Bildirimler")).toBeVisible({ timeout: 15000 });

  // Temizlik: arşivle, ardından rozeti sıfırda bırak.
  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  const revision = ((await detail.json()) as { data: { revision: number } }).data.revision;
  const archived = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision },
  });
  expect(archived.ok()).toBe(true);
  await page.request.post("/api/notifications/read", { data: { upto_seq: 999999 } });
});

test("telegram: kaydet → bağlı → unut (sahte kimlik, gerçek kasa) @vault", async ({ page }) => {
  await page.goto("/notifications");
  await expect(page.getByTestId("telegram-settings")).toBeVisible({ timeout: 15000 });

  await page.getByTestId("telegram-token").fill("999888777:AAHdryqXhFakeTokenForE2E1234567890ab");
  await page.getByTestId("telegram-chat").fill("123456789");
  await page.getByTestId("telegram-save").click();
  await expect(page.getByText("Bağlı").first()).toBeVisible({ timeout: 15000 });
  // Token ekrana asla geri gelmez.
  await expect(page.getByTestId("telegram-settings")).not.toContainText("AAHdryqXhFakeToken");

  // Temizlik: kasayı unut, rozet yapılandırılmadıya döner.
  await page.getByTestId("telegram-forget").click();
  await expect(page.getByText("Yapılandırılmadı")).toBeVisible({ timeout: 15000 });
});
