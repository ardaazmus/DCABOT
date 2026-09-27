import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("ayarlar bölümleri gezilir", async ({ page }) => {
  await page.goto("/settings/connection");
  await expect(page.getByRole("heading", { name: "Ayarlar", level: 1 })).toBeVisible();
  const tabs: [string, string][] = [
    ["Risk", "Kill switch"],
    ["Veri", "Veri setleri"],
    ["Sistem", "Yedekler"],
    ["Tercihler", "Tercihler"],
  ];
  for (const [tab, heading] of tabs) {
    await page.getByRole("link", { name: tab, exact: true }).click();
    await expect(page.getByRole("heading", { name: heading }).first()).toBeVisible();
  }
});

test("kill switch açılır ve kapatılır (sonda kapalı)", async ({ page }) => {
  try {
    await page.goto("/settings/risk");
    await expect(page.getByText("Kapalı").first()).toBeVisible({ timeout: 15000 });

    await page.getByRole("button", { name: "Kill switch'i aç" }).click();
    const reason = page.getByPlaceholder("Neden açıyorsun?");
    await expect(reason).toBeVisible();
    const confirm = page.getByRole("button", { name: "Onayla" });
    await expect(confirm).toBeDisabled();
    await reason.fill("e2e deneme");
    await expect(confirm).toBeEnabled();
    await confirm.click();
    await expect(page.getByText("Devrede").first()).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: "tests/e2e/screenshots/risk-on.png" });

    await page.getByRole("button", { name: "Kill switch'i kapat" }).click();
    await page.getByRole("button", { name: "Onayla" }).click();
    await expect(page.getByText("Kapalı").first()).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: "tests/e2e/screenshots/risk-off.png" });
  } finally {
    // Test nerede koparsa kopsun anahtar kapalı bırakılır.
    await page.request.post("/api/risk/kill-switch", { data: { engaged: false } });
  }
});

test("yedek alınır ve listede görünür", async ({ page }) => {
  await page.goto("/settings/system");
  await expect(page.getByRole("heading", { name: "Yedekler" })).toBeVisible({
    timeout: 15000,
  });
  // Sayfada olay tablosu da var; yedek tablosu "Dosya" sütunuyla ayırt edilir.
  const table = page
    .getByRole("table")
    .filter({ has: page.getByRole("columnheader", { name: "Dosya", exact: true }) });
  await expect(
    table.or(page.getByText("Henüz yedek yok")),
  ).toBeVisible({ timeout: 15000 });
  const nameCells = table.locator("tbody tr td:first-child");
  const before = new Set(
    await nameCells.allTextContents().catch(() => [] as string[]),
  );
  await page.getByRole("button", { name: "Yedek al" }).click();
  // Yeni yedeğin dosya adı listede belirir (satır sayısına bağlı değil).
  await expect
    .poll(
      async () => {
        const names = await nameCells.allTextContents().catch(() => [] as string[]);
        return names.find((name) => !before.has(name)) ?? "";
      },
      { timeout: 30000 },
    )
    .not.toBe("");
  await page.screenshot({ path: "tests/e2e/screenshots/system-page.png" });
});

test("veri bölümü veri setini gösterir", async ({ page }) => {
  await page.goto("/settings/data");
  await expect(
    page
      .getByRole("table")
      .getByText("binance-spot-klines-v1-btcusdt-1h-2025-01-01"),
  ).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: "tests/e2e/screenshots/data-page.png" });
});

test("erişilebilirlik: kritik ihlal yok", async ({ page }) => {
  for (const path of ["/settings/risk", "/settings/data"]) {
    await page.goto(path);
    await expect(page.getByText("Paper")).toBeVisible({ timeout: 15000 });
    const results = await new AxeBuilder({ page }).analyze();
    const critical = results.violations.filter(
      (violation) => violation.impact === "critical",
    );
    expect(critical).toEqual([]);
  }
});
