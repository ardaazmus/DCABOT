import { expect, test } from "@playwright/test";

test("Ctrl+K ile BTCUSDT aranır ve parite sayfasına gidilir", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByText("Paper")).toBeVisible({ timeout: 15000 });
  await page.keyboard.press("Control+k");
  const search = page.getByRole("combobox", { name: "Sayfa ya da parite ara…" });
  await expect(search).toBeVisible();
  await search.fill("BTCUSDT");
  await expect(
    page.getByRole("option", { name: "BTCUSDT TRADING", exact: true }),
  ).toBeVisible({ timeout: 15000 });
  await page.screenshot({ path: "tests/e2e/screenshots/palette-open.png" });
  await search.press("Enter");
  await expect(page).toHaveURL("/market/BTCUSDT");
  await expect(
    page.getByRole("heading", { name: "BTCUSDT", level: 1 }),
  ).toBeVisible();
});
