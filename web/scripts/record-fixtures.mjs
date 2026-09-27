/**
 * record:fixtures — çalışan backend'den gerçek yanıtları tests/fixtures/api/
 * altına kaydeder. Testler yalnız bu dosyaları kullanır; elle fixture yazılmaz.
 *
 * Kullanım: npm run record:fixtures
 * Gerekir: backend http://127.0.0.1:8770 adresinde çalışıyor olmalı
 * (ya da DCABOT_API_URL tanımlı olmalı).
 *
 * NOT: bazı kayıtlar gerçek yazma işlemidir (yedek alır, kill switch
 * açıp kapatır, indirme başlatır). Kill switch kayıt sonunda kapalı
 * bırakılır; alınan yedek dosyaları data/backups/ altında kalır.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT_DIR = join(ROOT, "tests", "fixtures", "api");
const BASE = process.env.DCABOT_API_URL ?? "http://127.0.0.1:8770";

const GET_ENDPOINTS = {
  "health.json": "/api/health",
  "capabilities.json": "/api/capabilities",
  "system-status.json": "/api/system/status",
  "risk-canary.json": "/api/risk/canary",
  "events.json": "/api/events?limit=20",
  "events-limit-200.json": "/api/events?limit=200",
  "exchange-symbols.json": "/api/public/exchange-symbols",
  "v2-bots.json": "/api/v2/bots",
  // W-F2: Piyasa ekranı.
  "tickers-24h.json":
    "/api/public/tickers-24h?symbols=BTCUSDT,ETHUSDT,SOLUSDT,USDCUSDT,ETHBTC",
  "ticker-24h-btcusdt.json": "/api/public/ticker-24h?symbol=BTCUSDT",
  "klines-btcusdt-1h-300.json":
    "/api/public/klines?symbol=BTCUSDT&interval=1h&limit=300",
  "depth-btcusdt-20.json": "/api/public/depth?symbol=BTCUSDT&limit=20",
  // W-F2.1: bot kur düğmesi.
  "symbol-rules-btcusdt.json": "/api/public/symbol-rules?symbol=BTCUSDT",
  "symbol-rules-btcusdc.json": "/api/public/symbol-rules?symbol=BTCUSDC",
  // W-F8: Ayarlar.
  "datasets.json": "/api/datasets",
  "backups.json": "/api/admin/backups",
};

mkdirSync(OUT_DIR, { recursive: true });

function save(file, text) {
  JSON.parse(text); // Geçerli JSON olduğunu doğrula, baytları aynen sakla.
  writeFileSync(join(OUT_DIR, file), text.endsWith("\n") ? text : `${text}\n`);
  console.log(`kaydedildi: tests/fixtures/api/${file}`);
}

async function call(method, path, body) {
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return response;
}

async function recordOk(file, method, path, body) {
  const response = await call(method, path, body);
  if (!response.ok) {
    throw new Error(`Kayıt başarısız: ${path} -> HTTP ${response.status}`);
  }
  save(file, await response.text());
  return response;
}

/** Bilerek hatalı istek: beklenen durum + beklenen hata biçimini doğrular. */
async function recordError(file, method, path, body, expectedStatus, expectedType) {
  const response = await call(method, path, body);
  if (response.status !== expectedStatus) {
    throw new Error(
      `Kayıt başarısız: ${path} -> beklenen ${expectedStatus}, alınan HTTP ${response.status}`,
    );
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes(expectedType)) {
    throw new Error(`Kayıt başarısız: ${path} içerik türü ${contentType}`);
  }
  save(file, await response.text());
}

for (const [file, path] of Object.entries(GET_ENDPOINTS)) {
  await recordOk(file, "GET", path);
}

// Sembol listesi büyük (binlerce kayıt); inceleme ve olası hafif testler
// için ilk 50 kayıt ayrı bir örnek dosyaya alınır.
{
  const response = await fetch(`${BASE}/api/public/exchange-symbols`);
  if (!response.ok) {
    throw new Error(
      `Kayıt başarısız: /api/public/exchange-symbols -> HTTP ${response.status}`,
    );
  }
  const body = await response.json();
  const symbols = Array.isArray(body.symbols) ? body.symbols : [];
  save(
    "exchange-symbols-sample.json",
    JSON.stringify({ ...body, symbols: symbols.slice(0, 50) }),
  );
}

// W-F2: indikatör ve rejim gövdeleri, yukarıda kaydedilen gerçek klines
// kapanışlarından kurulur (istemci hesap yapmaz, metni aynen gönderir).
{
  const klines = await (
    await fetch(`${BASE}/api/public/klines?symbol=BTCUSDT&interval=1h&limit=300`)
  ).json();
  const bars = klines.data.bars;
  const closes = bars.map((bar) => bar.close);

  await recordOk("indicators-sma-20.json", "POST", "/api/indicators/sma", {
    closes,
    window: 20,
  });
  await recordOk("indicators-ema-50.json", "POST", "/api/indicators/ema", {
    closes,
    window: 50,
  });
  await recordOk(
    "indicators-bollinger-20-2.json",
    "POST",
    "/api/indicators/bollinger",
    { closes, window: 20, num_std: "2" },
  );
  await recordOk("indicators-macd.json", "POST", "/api/indicators/macd", {
    closes,
    fast: 12,
    slow: 26,
    signal: 9,
    scale: 8,
  });
  await recordOk("indicators-stoch-rsi.json", "POST", "/api/indicators/stoch-rsi", {
    closes,
    rsi_window: 14,
    stoch_window: 14,
    scale: 8,
  });
  // W-F2.1: backend düzeltildi, 300 mum gönderilir.
  await recordOk("risk-regime-300.json", "POST", "/api/risk/regime", {
    bars: bars.map((bar) => ({ high: bar.high, low: bar.low, close: bar.close })),
    adx_window: 14,
    bb_window: 20,
    bb_num_std: "2",
    trend_threshold: "25",
    range_threshold: "20",
    squeeze_threshold: "0.05",
    min_di_separation: "0",
  });
}

// W-F4: sihirbaz grafiği 150 mum kullanır.
await recordOk(
  "klines-btcusdt-1h-150.json",
  "GET",
  "/api/public/klines?symbol=BTCUSDT&interval=1h&limit=150",
);

// W-F4: bot önizleme (Dengeli hazır ayarı) + her 422 kodu için bir örnek.
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
await recordOk("v2-preview-dengeli.json", "POST", "/api/v2/bots/preview", {
  budget: "600",
  strategy: DENGELI,
});
await recordOk(
  "v2-preview-within-budget-false.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "10", strategy: DENGELI },
);
await recordOk("v2-preview-sl.json", "POST", "/api/v2/bots/preview", {
  budget: "600",
  strategy: { ...DENGELI, stop_loss: "5" },
});
await recordError(
  "v2-preview-422-base-small.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "600", strategy: { ...DENGELI, base_order: "3" } },
  422,
  "application/problem+json",
);
await recordError(
  "v2-preview-422-quote.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "600", strategy: { ...DENGELI, symbol: "BTCUSDC" } },
  422,
  "application/problem+json",
);
await recordError(
  "v2-preview-422-range.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "600", strategy: { ...DENGELI, price_deviation: "150" } },
  422,
  "application/problem+json",
);
await recordError(
  "v2-preview-422-budget.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "0", strategy: DENGELI },
  422,
  "application/problem+json",
);
await recordError(
  "v2-preview-422-config.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "600", strategy: { ...DENGELI, safety_order: "1" } },
  422,
  "application/problem+json",
);
await recordError(
  "v2-bots-create-422-budget.json",
  "POST",
  "/api/v2/bots",
  { name: "X", mode: "PAPER", budget: "10", strategy: DENGELI },
  422,
  "application/problem+json",
);

// W-F4: bot yaşam döngüsü (gerçek yazma; kayıt botu sonda arşivlenir,
// liste boş kalır).
{
  const created = await call("POST", "/api/v2/bots", {
    name: "W-F4 fixture kaydı",
    mode: "PAPER",
    budget: "600",
    strategy: DENGELI,
  });
  if (created.status !== 201) {
    throw new Error(`Kayıt başarısız: bot oluşturma -> HTTP ${created.status}`);
  }
  const createText = await created.text();
  save("v2-bots-created.json", createText);
  const botId = JSON.parse(createText).data.bot_id;
  await recordOk("v2-bots-get.json", "GET", `/api/v2/bots/${botId}`);
  await recordOk("v2-bots-list-one.json", "GET", "/api/v2/bots");
  await recordError(
    "v2-bots-start-409.json",
    "POST",
    `/api/v2/bots/${botId}/start`,
    { revision: 1 },
    409,
    "application/problem+json",
  );
  await recordError(
    "v2-bots-archive-409-revision.json",
    "POST",
    `/api/v2/bots/${botId}/archive`,
    { revision: 99 },
    409,
    "application/problem+json",
  );
  await recordError(
    "v2-bots-pause-409-transition.json",
    "POST",
    `/api/v2/bots/${botId}/pause`,
    { revision: 1 },
    409,
    "application/problem+json",
  );
  await recordOk(
    "v2-bots-archive-200.json",
    "POST",
    `/api/v2/bots/${botId}/archive`,
    { revision: 1 },
  );
  const after = await (await fetch(`${BASE}/api/v2/bots`)).json();
  if (after.data.length !== 0) {
    throw new Error("Kayıt başarısız: arşiv sonrası liste boş değil");
  }
}

// W-F3: backtest başarılı yanıt (kısa aralık) + her hata kodu için bir örnek.
await recordOk("backtest-btcusdt-1h-14d.json", "POST", "/api/v2/backtests", {
  budget: "1000",
  strategy: DENGELI,
  interval: "1h",
  start_date: "2026-08-01",
  end_date: "2026-08-14",
});
await recordError(
  "backtest-422-date.json",
  "POST",
  "/api/v2/backtests",
  {
    budget: "1000",
    strategy: DENGELI,
    interval: "1h",
    start_date: "2026-13-45",
    end_date: "2026-08-14",
  },
  422,
  "application/problem+json",
);
await recordError(
  "backtest-422-range.json",
  "POST",
  "/api/v2/backtests",
  {
    budget: "1000",
    strategy: DENGELI,
    interval: "1h",
    start_date: "2026-08-14",
    end_date: "2026-08-01",
  },
  422,
  "application/problem+json",
);
await recordError(
  "backtest-422-too-large.json",
  "POST",
  "/api/v2/backtests",
  {
    budget: "1000",
    strategy: DENGELI,
    interval: "15m",
    start_date: "2025-09-01",
    end_date: "2026-09-01",
  },
  422,
  "application/problem+json",
);
await recordError(
  "backtest-422-sector.json",
  "POST",
  "/api/v2/backtests",
  {
    budget: "1000",
    strategy: { ...DENGELI, base_order: "3" },
    interval: "1h",
    start_date: "2026-08-01",
    end_date: "2026-08-14",
  },
  422,
  "application/problem+json",
);

// v2 hata örneği: eksik stratejiyle önizleme 422 Problem Details döndürür.
await recordError(
  "v2-bots-preview-422.json",
  "POST",
  "/api/v2/bots/preview",
  { budget: "1", strategy: {} },
  422,
  "application/problem+json",
);

// W-F8: testnet yapılandırılmamış (409 Problem Details).
await recordError(
  "testnet-account-409.json",
  "GET",
  "/api/testnet/account",
  undefined,
  409,
  "application/problem+json",
);
await recordError(
  "testnet-open-orders-409.json",
  "GET",
  "/api/testnet/open-orders",
  undefined,
  409,
  "application/problem+json",
);

// W-F8: gerekçesiz kill switch (422 eski hata biçimi).
await recordError(
  "kill-switch-422.json",
  "POST",
  "/api/risk/kill-switch",
  { engaged: true },
  422,
  "application/json",
);

// W-F8: kill switch aç/kapa (gerçek yazma; sonda kapalı bırakılır).
await recordOk("kill-switch-on.json", "POST", "/api/risk/kill-switch", {
  engaged: true,
  reason: "W-F8 fixture kaydı",
});
await recordOk("kill-switch-off.json", "POST", "/api/risk/kill-switch", {
  engaged: false,
});

// W-F8: risk açıklaması.
await recordOk("risk-explain-empty.json", "POST", "/api/risk/explain", {});
await recordOk("risk-explain-pair.json", "POST", "/api/risk/explain", {
  bot_id: "nope",
  symbol: "BTCUSDT",
});

// W-F8: yedek al + doğrula (gerçek yazma; dosya data/backups/ altında kalır).
{
  const response = await call("POST", "/api/admin/backup", { store: "historical_runs" });
  if (!response.ok) {
    throw new Error(`Kayıt başarısız: /api/admin/backup -> HTTP ${response.status}`);
  }
  const text = await response.text();
  save("backup-taken.json", text);
  const backupFile = JSON.parse(text).data.manifest.backup_file;
  await recordOk("backup-verify.json", "POST", "/api/admin/backup/verify", {
    backup_file: backupFile,
  });
  console.log(`yedek dosyası: data/backups/${backupFile}`);
}

// W-F8: indirme başlat + durum + iptal.
{
  const started = await call("POST", "/api/dataset-downloads", {
    dataset_id: "binance-spot-klines-v1-btcusdt-1h-2025-01-01",
  });
  if (started.status !== 202) {
    throw new Error(`Kayıt başarısız: indirme başlatma -> HTTP ${started.status}`);
  }
  const startText = await started.text();
  save("download-start.json", startText);
  const jobId = JSON.parse(startText).job.job_id;
  let status = "";
  for (let i = 0; i < 15; i++) {
    const poll = await fetch(`${BASE}/api/dataset-downloads/${jobId}`);
    const pollText = await poll.text();
    status = JSON.parse(pollText).status;
    if (status !== "QUEUED" && status !== "RUNNING" && status !== "RETRYING") {
      save("download-status.json", pollText);
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  if (status === "QUEUED" || status === "RUNNING" || status === "RETRYING") {
    throw new Error("Kayıt başarısız: indirme 15 sn'de bitmedi");
  }
  await recordOk("download-cancel.json", "POST", `/api/dataset-downloads/${jobId}/cancel`);
}
