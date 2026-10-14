import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const NAV_ITEMS = [
  { name: "Kontrol merkezi", heading: "Kontrol merkezi" },
  { name: "Botlar", heading: "Botlar" },
  { name: "Deal'ler", heading: "Deal'ler" },
  { name: "Backtest", heading: "Backtest" },
  { name: "Piyasa", heading: "Piyasa" },
  { name: "Ayarlar", heading: "Ayarlar" },
];

test("kabuk: 6 menü öğesi gezilir, her sayfa açılır", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Paper", { exact: true })).toBeVisible({ timeout: 15000 });
  for (const item of NAV_ITEMS) {
    await page.getByRole("link", { name: item.name }).click();
    await expect(
      page.getByRole("heading", { name: item.heading, level: 1 }),
    ).toBeVisible();
  }
});

test("ayarlar/sistem: bağlantı kartı backend durumunu gösterir", async ({
  page,
}) => {
  await page.goto("/settings/system");
  await expect(page.getByText("Bağlı")).toBeVisible({ timeout: 15000 });
  await expect(page.getByText("SIMULATED")).toBeVisible();
});

test("/settings bağlantıya yönlenir", async ({ page }) => {
  await page.goto("/settings");
  await expect(page).toHaveURL("/settings/connection");
});

test("kabuk masaüstü 1440px: kontrol merkezi açılır", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByText("Paper", { exact: true })).toBeVisible({ timeout: 15000 });
  // `/` veri-güdümlüdür (anlık görüntüler koşudan koşuya değişir);
  // piksel tabanı yerine yapısal iddia. Belge görüntüsü yazılmaya
  // devam eder.
  await expect(
    page.getByRole("heading", { name: "Kontrol merkezi", level: 1 }),
  ).toBeVisible();
  await page.screenshot({ path: "tests/e2e/screenshots/shell-desktop.png" });
});

test("kabuk mobil 390px: çekmece menü ve ekran görüntüsü @visual", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("Paper", { exact: true })).toBeVisible({ timeout: 15000 });
  // Dar ekranda menü çekmecededir.
  await expect(page.getByRole("link", { name: "Botlar" })).toBeHidden();
  await page.getByRole("button", { name: "Menüyü aç" }).click();
  await expect(page.getByRole("link", { name: "Botlar" })).toBeVisible();
  await page.getByRole("link", { name: "Botlar" }).click();
  await expect(
    page.getByRole("heading", { name: "Botlar", level: 1 }),
  ).toBeVisible();
  await page.screenshot({ path: "tests/e2e/screenshots/shell-mobile.png" });
  await expect(page).toHaveScreenshot("shell-390.png", {
    animations: "disabled",
    // Okunmam�� rozet ko�u durumuna g�re de�i�ir; taban yerle�imi korur.
    mask: [page.getByTestId("notifications-bell")],
    maxDiffPixels: 500,
  });
});

test("erişilebilirlik: kritik ihlal yok", async ({ page }) => {
  for (const path of ["/", "/design"]) {
    await page.goto(path);
    await expect(page.getByText("Paper", { exact: true })).toBeVisible({ timeout: 15000 });
    const results = await new AxeBuilder({ page }).analyze();
    const critical = results.violations.filter(
      (violation) => violation.impact === "critical",
    );
    expect(critical).toEqual([]);
  }
});
