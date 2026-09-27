/**
 * shot:running-bot — çalışan bot detay sekmelerinin rapor görüntüleri.
 * Suite dışı, rapor amaçlı betik; CI'da çalışmaz.
 *
 * Gerekir: dev web (3770) + dev API (8770) çalışıyor, BOT_ID çalışır durumda.
 * Kullanım: BOT_ID=bot_xxx node scripts/shot-running-bot.mjs
 *
 * Duraklatma ve kill switch sonda eski haline döndürülür (devam + kapalı).
 */
import { chromium } from "@playwright/test";

const BOT_ID = process.env.BOT_ID;
if (!BOT_ID) throw new Error("BOT_ID gerekli (örn. BOT_ID=bot_xxx node scripts/shot-running-bot.mjs)");
const WEB = process.env.DCABOT_WEB_URL ?? "http://127.0.0.1:3770";
const API = process.env.DCABOT_API_URL ?? "http://127.0.0.1:8770";
const OUT = "tests/e2e/screenshots";

async function api(method, path, body) {
  const response = await fetch(`${API}${path}`, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`API ${method} ${path} -> HTTP ${response.status}`);
  return response.json();
}

const browser = await chromium.launch();

async function shootTabs(width, height, suffix) {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.goto(`${WEB}/bots/${BOT_ID}`);
  await page.getByTestId("active-deal").waitFor({ timeout: 30000 });
  await page.screenshot({ path: `${OUT}/bot-overview-${suffix}.png`, fullPage: true });
  await page.getByRole("tab", { name: "Deal'ler" }).click();
  await page.getByTestId("deals-table").waitFor({ timeout: 15000 });
  await page.screenshot({ path: `${OUT}/bot-deals-${suffix}.png`, fullPage: true });
  await page.getByRole("tab", { name: "İstatistik" }).click();
  await page.getByTestId("so-histogram").waitFor({ timeout: 15000 });
  await page.screenshot({ path: `${OUT}/bot-stats-${suffix}.png`, fullPage: true });
  await page.getByRole("tab", { name: "Olay kaydı" }).click();
  await page.getByTestId("events-timeline").locator("li").first().waitFor({ timeout: 30000 });
  await page.screenshot({ path: `${OUT}/bot-events-${suffix}.png`, fullPage: true });
  await page.close();
}

await shootTabs(1440, 900, "desktop");
await shootTabs(390, 844, "mobile");

// Duraklatılmış hali.
{
  const bot = (await api("GET", `/api/v2/bots/${BOT_ID}`)).data;
  if (bot.status === "RUNNING") {
    await api("POST", `/api/v2/bots/${BOT_ID}/pause`, { revision: bot.revision });
  }
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${WEB}/bots/${BOT_ID}`);
  await page.getByText("Duraklatıldı").first().waitFor({ timeout: 15000 });
  await page.screenshot({ path: `${OUT}/bot-paused-desktop.png` });
  await page.close();
  const current = (await api("GET", `/api/v2/bots/${BOT_ID}`)).data;
  if (current.status === "PAUSED") {
    await api("POST", `/api/v2/bots/${BOT_ID}/resume`, { revision: current.revision });
  }
  console.log("devam ettirildi");
}

// Kill switch'li hali (sonda kapatılır).
{
  await api("POST", "/api/risk/kill-switch", { engaged: true, reason: "W-F5b ekran görüntüsü" });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto(`${WEB}/bots/${BOT_ID}`);
    // Gerekçe mum kapanışında işlenir; en fazla ~80 sn beklenir.
    for (let attempt = 0; attempt < 4; attempt++) {
      try {
        await page.getByText("Kill switch açık").first().waitFor({ timeout: 20000 });
        break;
      } catch {
        if (attempt === 3) throw new Error("kill switch gerekçesi görünmedi");
        await page.reload();
      }
    }
    await page.screenshot({ path: `${OUT}/bot-killswitch-desktop.png` });
    await page.close();
  } finally {
    await api("POST", "/api/risk/kill-switch", { engaged: false });
    console.log("kill switch kapatıldı");
  }
}

await browser.close();
console.log("kaydedildi: tests/e2e/screenshots/bot-*.png");
