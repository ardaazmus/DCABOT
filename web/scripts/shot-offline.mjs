/**
 * shot:offline — backend kapalıyken üst çubuk görüntüsü alır.
 * Suite dışı, rapor amaçlı tek seferlik betik; CI'da çalışmaz.
 *
 * Gerekir: `npm run dev` çalışıyor, backend KAPALI olmalı.
 * Kullanım: node scripts/shot-offline.mjs
 */
import { chromium } from "@playwright/test";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto("http://127.0.0.1:3770/");
await page.getByRole("status", { name: "Backend'e ulaşılamıyor" }).waitFor({ timeout: 30000 });
// Sorgular hata durumuna otursun (yeniden deneme + geri çekilme).
await page.waitForTimeout(8000);
await page.locator("header").screenshot({ path: "tests/e2e/screenshots/topbar-offline.png" });
await browser.close();
console.log("kaydedildi: tests/e2e/screenshots/topbar-offline.png");
