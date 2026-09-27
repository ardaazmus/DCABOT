import {
  isDecimalText,
  parseCooldown,
  parseCount,
  strategyFieldKey,
  type WizardForm,
} from "./bots";

export const BACKTEST_INTERVALS = ["15m", "30m", "1h", "4h", "1d"] as const;
export type BacktestInterval = (typeof BACKTEST_INTERVALS)[number];

/** Backend üst sınırı (mum). Asıl sınır backend'indir; bu yalnız gösterim. */
export const MAX_BACKTEST_BARS = 20_000;

const INTERVAL_MINUTES: Record<BacktestInterval, number> = {
  "15m": 15,
  "30m": 30,
  "1h": 60,
  "4h": 240,
  "1d": 1440,
};

export function isBacktestInterval(value: string): value is BacktestInterval {
  return (BACKTEST_INTERVALS as readonly string[]).includes(value);
}

const DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Basamak metni → tamsayı. `Number()` çizim dizini dışında yasak
 * olduğu için basamak birikimiyle çevrilir (takvim hesabı).
 */
function toInt(digits: string): number {
  let value = 0;
  for (const char of digits) value = value * 10 + (char.charCodeAt(0) - 48);
  return value;
}

function parseDateUtc(text: string): number | null {
  const match = DATE_PATTERN.exec(text);
  if (match === null) return null;
  const year = toInt(match[1] ?? "");
  const month = toInt(match[2] ?? "");
  const day = toInt(match[3] ?? "");
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  const time = Date.UTC(year, month - 1, day);
  const check = new Date(time);
  if (
    check.getUTCFullYear() !== year ||
    check.getUTCMonth() !== month - 1 ||
    check.getUTCDate() !== day
  ) {
    return null;
  }
  return time;
}

/**
 * Tahmini mum sayısı. Bitiş günü dahildir; tam sayı bölmesidir
 * (finansal hesap değil). Tarih geçersizse `null`.
 */
export function estimateBarCount(
  interval: BacktestInterval,
  startDate: string,
  endDate: string,
): number | null {
  const start = parseDateUtc(startDate);
  const end = parseDateUtc(endDate);
  if (start === null || end === null || end < start) return null;
  const days = Math.floor((end - start) / 86_400_000) + 1;
  return Math.floor((days * 1440) / INTERVAL_MINUTES[interval]);
}

function toDateString(time: number): string {
  return new Date(time).toISOString().slice(0, 10);
}

/** Varsayılan aralık: son 90 gün, bitiş dün (UTC). */
export function defaultBacktestRange(nowMs: number = Date.now()): {
  start: string;
  end: string;
} {
  const today = new Date(nowMs);
  const end = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()) - 86_400_000;
  return { start: toDateString(end - 89 * 86_400_000), end: toDateString(end) };
}

export const QUICK_RANGES = [
  { id: "30d", days: 30 },
  { id: "90d", days: 90 },
  { id: "180d", days: 180 },
  { id: "1y", days: 365 },
] as const;

/** Hızlı çip: bitiş sabit, başlangıç gün sayısına göre geri alınır. */
export function quickRangeStart(endDate: string, days: number): string | null {
  const end = parseDateUtc(endDate);
  if (end === null) return null;
  return toDateString(end - (days - 1) * 86_400_000);
}

export type BacktestPrefill = Partial<WizardForm> & {
  interval?: BacktestInterval;
  startDate?: string;
  endDate?: string;
};

const PARAM_KEYS: [string, keyof WizardForm][] = [
  ["symbol", "symbol"],
  ["extra_symbols", "extraSymbols"],
  ["direction", "direction"],
  ["market", "market"],
  ["leverage", "leverage"],
  ["cooldown", "cooldown"],
  ["min_price", "minPrice"],
  ["max_price", "maxPrice"],
  ["base_order", "baseOrder"],
  ["safety_order", "safetyOrder"],
  ["max_so", "maxSafetyOrders"],
  ["max_active_so", "maxActiveSafetyOrders"],
  ["max_deals", "maxActiveDeals"],
  ["deviation", "priceDeviation"],
  ["vol_scale", "volumeScale"],
  ["step_scale", "stepScale"],
  ["tp", "takeProfit"],
  ["combo_tp", "comboTakeProfit"],
  ["trailing_tp", "trailingTakeProfit"],
  ["sl", "stopLoss"],
  ["budget", "budget"],
  ["name", "name"],
];

/**
 * Sihirbaz/backtest köprüsü: form URL parametrelerine yazılır, karşı
 * sayfa aynı anahtarları okur. Yöntem bilinçli seçimdir: sayfa
 * yenilemede kaybolmaz, bağlantı olarak paylaşılır.
 */
export function wizardFormToSearchParams(
  form: WizardForm,
  extra?: { interval?: BacktestInterval; startDate?: string; endDate?: string },
): URLSearchParams {
  const params = new URLSearchParams();
  for (const [param, key] of PARAM_KEYS) {
    const value = form[key];
    if (typeof value === "string" && value !== "") params.set(param, value);
  }
  if (form.stopLossEnabled) params.set("sl_enabled", "1");
  if (form.trailingEnabled) params.set("trailing_enabled", "1");
  if (extra?.interval !== undefined) params.set("interval", extra.interval);
  if (extra?.startDate !== undefined) params.set("start", extra.startDate);
  if (extra?.endDate !== undefined) params.set("end", extra.endDate);
  return params;
}

export type BacktestFieldKey =
  | keyof WizardForm
  | "interval"
  | "startDate"
  | "endDate";

/**
 * Problem Details `field` → backtest form alanı. Bilinmeyen ve
 * genel hatalar `null` döner (form üstünde gösterilir).
 */
export function backtestFieldTarget(field: string): BacktestFieldKey | null {
  switch (field) {
    case "budget":
      return "budget";
    case "interval":
      return "interval";
    case "start_date":
      return "startDate";
    case "end_date":
      return "endDate";
    default:
      return strategyFieldKey(field);
  }
}

/** URL parametrelerinden form ön doldurması; biçimi bozuk değer atlanır. */
export function parseBacktestPrefill(search: URLSearchParams): BacktestPrefill {
  const prefill: BacktestPrefill = {};
  const symbol = search.get("symbol");
  if (symbol !== null && symbol !== "") prefill.symbol = symbol.toUpperCase();
  const direction = search.get("direction");
  if (direction === "LONG" || direction === "SHORT") prefill.direction = direction;
  const market = search.get("market");
  if (market === "SPOT" || market === "FUTURES") prefill.market = market;
  for (const [param, key] of PARAM_KEYS) {
    if (key === "symbol" || key === "name") continue;
    const raw = search.get(param);
    if (raw === null || raw === "") continue;
    if (key === "maxSafetyOrders" || key === "maxActiveSafetyOrders" || key === "maxActiveDeals") {
      if (parseCount(raw) !== null) (prefill as Record<string, string>)[key] = raw;
    } else if (key === "leverage") {
      if (parseCount(raw) !== null) (prefill as Record<string, string>)[key] = raw;
    } else if (key === "extraSymbols") {
      if (/^[A-Za-z0-9, ]{1,200}$/.test(raw)) (prefill as Record<string, string>)[key] = raw.toUpperCase();
    } else if (key === "cooldown") {
      if (parseCooldown(raw) !== null) (prefill as Record<string, string>)[key] = raw;
    } else if (isDecimalText(raw)) {
      (prefill as Record<string, string>)[key] = raw;
    }
  }
  const name = search.get("name");
  if (name !== null && name !== "") prefill.name = name;
  if (search.get("sl_enabled") === "1") prefill.stopLossEnabled = true;
  if (search.get("trailing_enabled") === "1") prefill.trailingEnabled = true;
  const interval = search.get("interval");
  if (interval !== null && isBacktestInterval(interval)) prefill.interval = interval;
  const start = search.get("start");
  if (start !== null && parseDateUtc(start) !== null) prefill.startDate = start;
  const end = search.get("end");
  if (end !== null && parseDateUtc(end) !== null) prefill.endDate = end;
  return prefill;
}
