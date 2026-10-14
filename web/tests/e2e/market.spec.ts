import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { gotoMarketList, gotoMarketSymbol } from "./market-ready";

test("/market açılır, arama ETH → satır → parite sayfası", async ({ page }) => {
  await gotoMarketList(page);
  await page.getByRole("searchbox", { name: "Parite ara…" }).fill("ETH");
  const row = page.getByRole("link", { name: "ETHUSDT", exact: true });
  // Liste 15 sn'de tazelenir; tek bozuk yukarı-akım yükü bir çevrimde iyileşir.
  await expect(row).toBeVisible({ timeout: 20000 });
  await row.click();
  await expect(page).toHaveURL("/market/ETHUSDT");
  await expect(
    page.getByRole("heading", { name: "ETHUSDT", level: 1 }),
  ).toBeVisible();
});

test("erişilebilirlik: kritik ihlal yok", async ({ page }) => {
  await gotoMarketList(page);
  const marketResults = await new AxeBuilder({ page }).analyze();
  expect(
    marketResults.violations.filter((violation) => violation.impact === "critical"),
  ).toEqual([]);

  await gotoMarketSymbol(page, "/market/BTCUSDT");
  const symbolResults = await new AxeBuilder({ page }).analyze();
  expect(
    symbolResults.violations.filter((violation) => violation.impact === "critical"),
  ).toEqual([]);
});

test("/market masaüstü: ekran görüntüsü ve görsel taban @visual", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await gotoMarketList(page);
  await page.screenshot({ path: "tests/e2e/screenshots/market-desktop.png" });
  await expect(page).toHaveScreenshot("market-desktop.png", {
    animations: "disabled",
    // Canlı fiyatlar maskelenir; taban yerleşimi korur.
    mask: [page.locator("table tbody"), page.getByTestId("notifications-bell")],
    maxDiffPixels: 500,
  });
});

test("/market mobil: ekran görüntüsü ve görsel taban @visual", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoMarketList(page);
  await page.screenshot({ path: "tests/e2e/screenshots/market-mobile.png" });
  await expect(page).toHaveScreenshot("market-mobile.png", {
    animations: "disabled",
    mask: [page.locator("main ol"), page.getByTestId("notifications-bell")],
    maxDiffPixels: 500,
  });
});

test("mobil üst çubukta kill switch görünür", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/market");
  await expect(page.getByText("Paper")).toBeVisible({ timeout: 15000 });
  const badge = page.getByRole("img", { name: /Kill Switch/ });
  await expect(badge).toBeVisible();
  await page
    .locator("header")
    .screenshot({ path: "tests/e2e/screenshots/topbar-mobile.png" });
});
