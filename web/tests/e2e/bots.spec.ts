import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
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

async function createBot(page: Page, name: string): Promise<string> {
  const response = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name, mode: "PAPER", budget: "1000", strategy: DENGELI },
  });
  const body = (await response.json()) as { data: { bot_id: string } };
  return body.data.bot_id;
}

async function archiveBot(page: Page, botId: string) {
  // Arşiv STOPPED ister; çalışan/duraklatılmış bot önce durdurulur.
  // Her yazma revizyonu artırır, taze revizyonla devam edilir.
  const detail = await page.request.get(`/api/v2/bots/${botId}`);
  expect(detail.ok()).toBe(true);
  let bot = ((await detail.json()) as { data: { status: string; revision: number } }).data;
  if (bot.status !== "STOPPED") {
    const stop = await page.request.post(`/api/v2/bots/${botId}/stop`, {
      data: { revision: bot.revision },
    });
    expect(stop.ok()).toBe(true);
    bot = ((await stop.json()) as { data: { status: string; revision: number } }).data;
  }
  const response = await page.request.post(`/api/v2/bots/${botId}/archive`, {
    data: { revision: bot.revision },
  });
  expect(response.ok()).toBe(true);
}

test("sihirbaz BTCUSDT Dengeli: önizleme → oluştur → detay", async ({ page }) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();

  // Parite ön dolu; Dengeli vurgulu; giriş + borsa minimumu aynı sayfada.
  await expect(page.getByTestId("wizard-symbol")).toHaveValue("BTCUSDT");
  await expect(page.getByRole("radio", { name: "Dengeli" })).toHaveAttribute(
    "aria-checked",
    "true",
  );
  await expect(page.getByTestId("wizard-base-order")).toHaveValue("25");
  await expect(page.getByText("En az 5 USDT")).toBeVisible({ timeout: 15000 });

  // Bütçe + isim; önizleme kartları ve grafik çizgileri gelir.
  await page.getByTestId("wizard-budget").fill("1000");
  await page.getByTestId("wizard-name").fill("E2E W-F4 wizard");
  const preview = page.getByTestId("preview-panel");
  await expect(preview.getByText("Gereken sermaye")).toBeVisible({ timeout: 20000 });
  await expect(preview.getByText("Fiyat kapsamı")).toBeVisible();
  await expect(preview.getByText("Emir planı")).toBeVisible();
  await expect(page.getByTestId("plan-chart").locator("canvas").first()).toBeVisible({
    timeout: 20000,
  });

  // Özet → oluştur → detay sayfası.
  await page.getByTestId("wizard-create").click();
  await expect(page).toHaveURL(/\/bots\/bot_/, { timeout: 20000 });
  await expect(
    page.getByRole("heading", { name: "E2E W-F4 wizard", level: 1 }),
  ).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("heading", { name: "Strateji" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Güncel plan" })).toBeVisible();
});

test("base order 3: alan altında borsa minimumu hatası", async ({ page }) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  // Bütçeyi önce doldur ki önizleme gövdesi tamamlansın.
  await page.getByTestId("wizard-budget").fill("1000");
  const base = page.getByTestId("wizard-base-order");
  await base.fill("3");
  const entrySection = page.locator("section", {
    has: page.getByRole("heading", { name: "Giriş" }),
  });
  await expect(entrySection.getByText("Base order borsa minimumunun altında")).toBeVisible({
    timeout: 20000,
  });
});

test("USDC paritesi seçilemez", async ({ page }) => {
  await page.goto("/bots/new");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();
  const box = page.getByTestId("wizard-symbol");
  await box.click();
  await box.fill("BTCUSDC");
  await page.getByRole("option", { name: /BTCUSDC/ }).first().click();
  await expect(page.getByText("Bu pariteyle bot kurulamaz")).toBeVisible({
    timeout: 15000,
  });
  await page.getByTestId("wizard-create").click();
  await expect(page).toHaveURL(/\/bots\/new/);
  await expect(page.getByText("Bu pariteyle bot kurulamaz")).toBeVisible();
});

test("listede Başlat: bot çalışır, Durdur: durur", async ({ page }) => {
  await createBot(page, "E2E W-F4 runner");
  await page.goto("/bots");
  await expect(page.getByRole("link", { name: "E2E W-F4 runner" })).toBeVisible({
    timeout: 15000,
  });
  const row = page.locator("tr", { hasText: "E2E W-F4 runner" });
  await row.getByRole("button", { name: "Başlat" }).click();
  await expect(row.getByText("Çalışıyor")).toBeVisible({ timeout: 15000 });
  await row.getByRole("button", { name: "Durdur" }).click();
  await expect(row.getByText("Durdu")).toBeVisible({ timeout: 15000 });
});

test("arşivle: bot listeden kalkar", async ({ page }) => {
  await createBot(page, "E2E W-F4 archive");
  await page.goto("/bots");
  await expect(page.getByRole("link", { name: "E2E W-F4 archive" })).toBeVisible({
    timeout: 15000,
  });
  const row = page.locator("tr", { hasText: "E2E W-F4 archive" });
  await row.getByRole("button", { name: "Arşivle" }).click();
  await page.getByRole("button", { name: "Onayla" }).click();
  await expect(page.getByRole("link", { name: "E2E W-F4 archive" })).toBeHidden({
    timeout: 15000,
  });
});

test("erişilebilirlik: kritik ihlal yok", async ({ page }) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();
  await expect(page.getByTestId("wizard-create")).toBeVisible();
  const wizardResults = await new AxeBuilder({ page }).analyze();
  expect(
    wizardResults.violations.filter((violation) => violation.impact === "critical"),
  ).toEqual([]);

  await page.goto("/bots");
  await expect(
    page
      .getByRole("link", { name: "E2E W-F4 runner" })
      .or(page.getByText("İlk botunu kur")),
  ).toBeVisible({ timeout: 15000 });
  const listResults = await new AxeBuilder({ page }).analyze();
  expect(
    listResults.violations.filter((violation) => violation.impact === "critical"),
  ).toEqual([]);
});

test("sihirbaz masaüstü: ekran görüntüsü ve görsel taban @visual", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();
  await page.getByTestId("wizard-budget").fill("1000");
  const preview = page.getByTestId("preview-panel");
  await expect(preview.getByText("Gereken sermaye")).toBeVisible({ timeout: 20000 });
  await expect(page.getByTestId("plan-chart").locator("canvas").first()).toBeVisible({
    timeout: 20000,
  });
  await page.screenshot({ path: "tests/e2e/screenshots/wizard-desktop.png" });
  await expect(page).toHaveScreenshot("wizard-desktop.png", {
    animations: "disabled",
    mask: [preview, page.getByTestId("plan-chart"), page.getByTestId("notifications-bell")],
    maxDiffPixels: 500,
  });
});

test("sihirbaz mobil: ekran görüntüsü ve görsel taban @visual", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByRole("heading", { name: "DCA botu kur", level: 1 })).toBeVisible();
  await page.screenshot({ path: "tests/e2e/screenshots/wizard-mobile.png" });
  await expect(page).toHaveScreenshot("wizard-mobile.png", {
    animations: "disabled",
    mask: [page.getByTestId("preview-panel"), page.getByTestId("notifications-bell")],
    maxDiffPixels: 500,
  });
});

test("liste ve detay: ekran görüntüleri ve görsel taban @visual", async ({ page }) => {
  // Öz-yeterli: önceki testlerin botlarını arşivleyip kendi listesini kurar.
  const existing = (await (await page.request.get("/api/v2/bots")).json()) as {
    data: { bot_id: string; name: string; revision: number }[];
  };
  for (const bot of existing.data.filter((entry) => entry.name.startsWith("E2E"))) {
    await archiveBot(page, bot.bot_id);
  }
  await createBot(page, "E2E liste A");
  await createBot(page, "E2E liste B");
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/bots");
  await expect(page.getByRole("link", { name: "E2E liste A" })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByRole("link", { name: "E2E liste B" })).toBeVisible({
    timeout: 15000,
  });
  await page.screenshot({ path: "tests/e2e/screenshots/bots-list.png" });
  await expect(page.locator("main")).toHaveScreenshot("bots-list.png", {
    animations: "disabled",
    // Canlı bütçe/zaman hücreleri maskelenir; taban yerleşimi korur.
    mask: [page.locator("table")],
    maxDiffPixels: 500,
  });
  await page.getByRole("link", { name: "E2E liste A" }).click();
  await expect(page.getByRole("heading", { name: "Strateji" })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByTestId("preview-panel").getByText("Gereken sermaye")).toBeVisible({
    timeout: 20000,
  });
  await expect(page.getByTestId("plan-chart").locator("canvas").first()).toBeVisible({
    timeout: 20000,
  });
  await page.screenshot({ path: "tests/e2e/screenshots/bots-detail.png" });
  await expect(page.locator("main")).toHaveScreenshot("bots-detail.png", {
    animations: "disabled",
    mask: [page.getByTestId("preview-panel"), page.getByTestId("plan-chart")],
    maxDiffPixels: 500,
  });
});

// Son test: e2e botları arşivlenir, kalıcı SQLite birikmez.
test("multi-pair sihirbaz: ek sembol, toplam önizleme, detayda semboller", async ({ page }) => {
  await page.goto("/bots/new?symbol=BTCUSDT");
  await expect(page.getByTestId("wizard-symbol")).toHaveValue("BTCUSDT");
  await page.getByTestId("wizard-extra-symbols").fill("ETHUSDT");
  await page.getByTestId("wizard-max-active-deals").fill("2");
  await page.getByTestId("wizard-combo-take-profit").fill("1");
  await page.getByTestId("wizard-budget").fill("2000");
  await page.getByTestId("wizard-name").fill("E2E M1 multi");
  const preview = page.getByTestId("preview-panel");
  await expect(preview.getByText("Toplam gereken sermaye")).toBeVisible({ timeout: 20000 });
  await expect(preview.getByText(/Birleşik hedef/)).toBeVisible();
  await page.getByTestId("wizard-create").click();
  await expect(page).toHaveURL(/\/bots\/bot_/, { timeout: 20000 });
  await expect(page.getByText("BTCUSDT, ETHUSDT")).toBeVisible({ timeout: 15000 });
  await expect(page.getByText("Birleşik take-profit")).toBeVisible();
});

test("bot kopyalama: detaydan kopya yeni bot açar", async ({ page }) => {
  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: { name: "E2E kopya kaynak", mode: "PAPER", budget: "1000", strategy: DENGELI },
  });
  const botId = ((await created.json()) as { data: { bot_id: string } }).data.bot_id;
  await page.goto(`/bots/${botId}`);
  await expect(page.getByRole("heading", { name: "E2E kopya kaynak" })).toBeVisible({ timeout: 20000 });
  await page.getByTestId("bot-copy").click();
  // Kopya detayına geçiş: başlık otomatik bekler (URL hemen eşleşirdi, yarışlıydı).
  await expect(page.getByRole("heading", { name: "E2E kopya kaynak (2)" })).toBeVisible({ timeout: 20000 });
  expect(page.url()).not.toContain(botId);
});

test("trailing TP: API ile kurulur, detayda satır görünür", async ({ page }) => {
  const created = await postWithUpstreamRetry(page.request, "/api/v2/bots", {
    data: {
      name: "E2E trailing",
      mode: "PAPER",
      budget: "1000",
      strategy: { ...DENGELI, trailing_take_profit: "1" },
    },
  });
  expect(created.ok()).toBe(true);
  const createdBody = (await created.json()) as {
    data: { bot_id: string; strategy: { trailing_take_profit: string | null } };
  };
  expect(createdBody.data.strategy.trailing_take_profit).toBe("1");
  await page.goto(`/bots/${createdBody.data.bot_id}`);
  await expect(page.getByRole("heading", { name: "E2E trailing" })).toBeVisible({ timeout: 20000 });
  await expect(page.getByText("Trailing (%)")).toBeVisible();
});

test("temizlik: e2e botları arşivlenir", async ({ page }) => {
  const list = await page.request.get("/api/v2/bots");
  expect(list.ok()).toBe(true);
  const body = (await list.json()) as {
    data: { bot_id: string; name: string; revision: number }[];
  };
  for (const bot of body.data.filter((entry) => entry.name.startsWith("E2E"))) {
    await archiveBot(page, bot.bot_id);
  }
  const after = await page.request.get("/api/v2/bots");
  const remaining = (
    (await after.json()) as { data: { name: string }[] }
  ).data.filter((entry) => entry.name.startsWith("E2E"));
  expect(remaining).toEqual([]);
});
