import { expect, test } from "@playwright/test";

test("/design koyu tema: galeri ve görsel taban @visual", async ({ page }) => {
  await page.goto("/design");
  await expect(page.getByText("Paper")).toBeVisible({ timeout: 15000 });
  await expect(
    page.getByRole("heading", { name: "Bileşen galerisi", level: 1 }),
  ).toBeVisible();
  await page.screenshot({
    path: "tests/e2e/screenshots/design-dark.png",
    fullPage: true,
  });
  await expect(page).toHaveScreenshot("design-dark.png", {
    fullPage: true,
    animations: "disabled",
    // Okunmamış rozet koşu durumuna göre değişir; taban yerleşimi korur.
    mask: [page.getByTestId("notifications-bell")],
    maxDiffPixels: 800,
  });
});

test("/design açık tema: galeri ve görsel taban @visual", async ({ page }) => {
  await page.goto("/design");
  await expect(page.getByText("Paper")).toBeVisible({ timeout: 15000 });
  await page.getByRole("button", { name: "Tema değiştir" }).click();
  await expect(page.locator("html.light")).toBeAttached();
  await page.screenshot({
    path: "tests/e2e/screenshots/design-light.png",
    fullPage: true,
  });
  await expect(page).toHaveScreenshot("design-light.png", {
    fullPage: true,
    animations: "disabled",
    // Okunmamış rozet koşu durumuna göre değişir; taban yerleşimi korur.
    mask: [page.getByTestId("notifications-bell")],
    maxDiffPixels: 800,
  });
});
