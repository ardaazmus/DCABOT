import { expect, test } from "@playwright/test";
import { gotoMarketSymbol } from "./market-ready";

test("grafik tuvali görünür, aralık değişimi yeni istek atar", async ({
  page,
}) => {
  await gotoMarketSymbol(page, "/market/BTCUSDT");
  const chip4h = page.getByRole("button", { name: "4h", exact: true });
  const [response] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().includes("/api/public/klines") &&
        response.url().includes("interval=4h") &&
        response.ok(),
    ),
    chip4h.click(),
  ]);
  expect(response.status()).toBe(200);
});

test("indikatör çipi açılınca istek gider, paneller açılır", async ({
  page,
}) => {
  await gotoMarketSymbol(page, "/market/BTCUSDT");
  const [request] = await Promise.all([
    page.waitForRequest(
      (request) =>
        request.url().includes("/api/indicators/sma") &&
        request.method() === "POST",
    ),
    page.getByRole("button", { name: "SMA 20" }).click(),
  ]);
  expect(request.method()).toBe("POST");
  await page.getByRole("button", { name: "MACD" }).click();
  await expect(
    page.getByTestId("macd-panel").locator("canvas").first(),
  ).toBeVisible({ timeout: 20000 });
});

test("emir defterinde 20 + 20 satır", async ({ page }) => {
  await gotoMarketSymbol(page, "/market/BTCUSDT");
  await expect(page.getByTestId("depth-bids").locator("tbody tr")).toHaveCount(20, {
    timeout: 20000,
  });
  await expect(page.getByTestId("depth-asks").locator("tbody tr")).toHaveCount(20);
});

test("bilinmeyen sembol dürüst hata + Piyasaya dön", async ({ page }) => {
  await page.goto("/market/XXXXXX");
  await expect(page.getByText("Bu parite bulunamadı")).toBeVisible({
    timeout: 20000,
  });
  await page.getByRole("link", { name: "Piyasaya dön" }).click();
  await expect(page).toHaveURL("/market");
});

test("/market/BTCUSDT indikatörsüz: ekran görüntüsü ve görsel taban @visual", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await gotoMarketSymbol(page, "/market/BTCUSDT");
  await expect(page.getByTestId("depth-bids").locator("tbody tr")).toHaveCount(20);
  await page.screenshot({
    path: "tests/e2e/screenshots/symbol-off.png",
    fullPage: true,
  });
  await expect(page).toHaveScreenshot("symbol-desktop-off.png", {
    animations: "disabled",
    mask: [
      page.getByTestId("symbol-stats"),
      page.getByTestId("price-chart"),
      page.getByTestId("depth-bids"),
      page.getByTestId("depth-asks"),
      page.getByTestId("regime-card"),
      page.getByTestId("notifications-bell"),
    ],
    maxDiffPixels: 800,
  });
});

test("/market/BTCUSDT indikatörlü: ekran görüntüsü ve görsel taban @visual", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await gotoMarketSymbol(page, "/market/BTCUSDT");
  for (const name of ["SMA 20", "EMA 50", "BB 20/2", "MACD", "StochRSI"]) {
    await page.getByRole("button", { name }).click();
  }
  await expect(
    page.getByTestId("macd-panel").locator("canvas").first(),
  ).toBeVisible({ timeout: 20000 });
  await expect(
    page.getByTestId("stoch-panel").locator("canvas").first(),
  ).toBeVisible({ timeout: 20000 });
  await page.screenshot({
    path: "tests/e2e/screenshots/symbol-on.png",
    fullPage: true,
  });
  await expect(page).toHaveScreenshot("symbol-desktop-on.png", {
    animations: "disabled",
    mask: [
      page.getByTestId("symbol-stats"),
      page.getByTestId("price-chart"),
      page.getByTestId("macd-panel"),
      page.getByTestId("stoch-panel"),
      page.getByTestId("depth-bids"),
      page.getByTestId("depth-asks"),
      page.getByTestId("regime-card"),
      page.getByTestId("notifications-bell"),
    ],
    maxDiffPixels: 800,
  });
});

test("/market/BTCUSDT mobil: ekran görüntüsü ve görsel taban @visual", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoMarketSymbol(page, "/market/BTCUSDT");
  await page.screenshot({ path: "tests/e2e/screenshots/symbol-mobile.png" });
  await expect(page).toHaveScreenshot("symbol-mobile.png", {
    animations: "disabled",
    mask: [
      page.getByTestId("symbol-stats"),
      page.getByTestId("price-chart"),
      page.getByTestId("notifications-bell"),
    ],
    maxDiffPixels: 500,
  });
});

test("USDC paritesinde bot kur düğmesi devre dışı", async ({ page }) => {
  await gotoMarketSymbol(page, "/market/BTCUSDC");
  const button = page.getByRole("button", { name: "Bu paritede bot kur" });
  await expect(button).toBeDisabled({ timeout: 20000 });
  await expect(button).toHaveAttribute(
    "title",
    "Şimdilik yalnız USDT pariteleriyle bot kurulabilir.",
    { timeout: 15000 },
  );
  await page.screenshot({ path: "tests/e2e/screenshots/symbol-usdc.png" });
});
