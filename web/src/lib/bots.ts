import type { BotAction } from "@/lib/api/queries";
import type { DcaStrategy, FuturesGridBotStrategy, GridBotStrategy } from "@/lib/api/schemas";

export type PresetId = "conservative" | "balanced" | "aggressive" | "custom";

/** Sihirbaz form durumu; sayılar metindir, doğrulama backend'indir. */
export type WizardForm = {
  symbol: string;
  /** Virgül/boşlukla ayrılmış ek semboller; boş metin = tek sembol. */
  extraSymbols: string;
  direction: "LONG" | "SHORT";
  market: "SPOT" | "FUTURES";
  leverage: string;
  cooldown: string;
  minPrice: string;
  maxPrice: string;
  baseOrder: string;
  safetyOrder: string;
  maxSafetyOrders: string;
  /** Boş metin = sınırsız (`null` gönderilir). */
  maxActiveSafetyOrders: string;
  /** Boş metin = paylaşımlı deal kapağı yok (`null` gönderilir). */
  maxActiveDeals: string;
  priceDeviation: string;
  volumeScale: string;
  stepScale: string;
  takeProfit: string;
  trailingEnabled: boolean;
  /** Bos metin = iz surme yok (acikken null gonderilir). */
  trailingTakeProfit: string;
  stopLossEnabled: boolean;
  /** Bos metin = birlesik hedef yok (`null` gonderilir). */
  comboTakeProfit: string;
  stopLoss: string;
  budget: string;
  name: string;
};

export type PresetValues = {
  baseOrder: string;
  safetyOrder: string;
  maxSafetyOrders: string;
  maxActiveSafetyOrders: string;
  priceDeviation: string;
  volumeScale: string;
  stepScale: string;
  takeProfit: string;
  trailingTakeProfit: string;
  stopLoss: string;
};

/**
 * Hazır ayar değerleri (koordinatör kararı; hepsi LONG, spot).
 * Stop loss her üçünde de kapalıdır; metin yalnız açıldığında kullanılır.
 */
export const PRESETS: Record<Exclude<PresetId, "custom">, PresetValues> = {
  conservative: {
    baseOrder: "20",
    safetyOrder: "20",
    maxSafetyOrders: "8",
    maxActiveSafetyOrders: "3",
    priceDeviation: "2",
    volumeScale: "1.2",
    stepScale: "1.3",
    takeProfit: "1.5",
    trailingTakeProfit: "1",
    stopLoss: "5",
  },
  balanced: {
    baseOrder: "25",
    safetyOrder: "25",
    maxSafetyOrders: "6",
    maxActiveSafetyOrders: "2",
    priceDeviation: "1.5",
    volumeScale: "1.5",
    stepScale: "1.2",
    takeProfit: "2",
    trailingTakeProfit: "1",
    stopLoss: "5",
  },
  aggressive: {
    baseOrder: "50",
    safetyOrder: "50",
    maxSafetyOrders: "5",
    maxActiveSafetyOrders: "2",
    priceDeviation: "1",
    volumeScale: "2",
    stepScale: "1",
    takeProfit: "3",
    trailingTakeProfit: "1",
    stopLoss: "5",
  },
};

export const PRESET_IDS: Exclude<PresetId, "custom">[] = [
  "conservative",
  "balanced",
  "aggressive",
];

const PRESET_KEYS: (keyof PresetValues)[] = [
  "baseOrder",
  "safetyOrder",
  "maxSafetyOrders",
  "maxActiveSafetyOrders",
  "priceDeviation",
  "volumeScale",
  "stepScale",
  "takeProfit",
];

/**
 * Hangi hazır ayarın seçili görüneceği. SL karşılaştırmaya girmez:
 * SL yalnız açma/kapama düğmesiyle değişir ve ayarı bozmaz.
 */
export function detectPreset(form: WizardForm): PresetId {
  for (const id of PRESET_IDS) {
    const preset = PRESETS[id];
    if (PRESET_KEYS.every((key) => form[key] === preset[key])) return id;
  }
  return "custom";
}

/**
 * 0..99 sayaç metni → tamsayı. `Number()` bu dizin dışında yasak
 * olduğu için basamak birikimiyle çevrilir (finans hesabı değil).
 */
export function parseCount(text: string): number | null {
  if (!/^\d{1,2}$/.test(text)) return null;
  let value = 0;
  for (const char of text) value = value * 10 + (char.charCodeAt(0) - 48);
  return value;
}

/**
 * Cooldown saniyesi (0..99999999, bos degil). `Number()` yasagi yuzunden
 * basamak birikimiyle cevrilir; ust sinir backend'indir.
 */
export function parseCooldown(text: string): number | null {
  if (!/^\d{1,8}$/.test(text)) return null;
  let value = 0;
  for (const char of text) value = value * 10 + (char.charCodeAt(0) - 48);
  return value;
}

const SYMBOL_PATTERN = /^[A-Z0-9]{5,20}$/;

/**
 * Ek sembol metni → büyük harf sembol listesi. Virgül/boşlukla ayrılır,
 * boş metin boş listedir; biçimi bozuk jeton `null` döndürür.
 */
export function parseExtraSymbols(text: string): string[] | null {
  const trimmed = text.trim();
  if (trimmed === "") return [];
  const parts = trimmed.split(/[\s,]+/);
  const out: string[] = [];
  for (const part of parts) {
    const upper = part.toUpperCase();
    if (!SYMBOL_PATTERN.test(upper)) return null;
    if (!out.includes(upper)) out.push(upper);
  }
  return out;
}

const DECIMAL_PATTERN = /^(0|[1-9][0-9]*)(\.[0-9]+)?$/;

/** İstemci yalnız biçim denetler (`0` geçerli biçimdir; değer backend'indir). */
export function isDecimalText(text: string): boolean {
  return DECIMAL_PATTERN.test(text);
}

const THOUSANDS_PATTERN = /\d\.\d{3}(\D|$)/;

/**
 * Binlik ayırıcı şüphesi ("1.000", "1.000,5"). Dört basamaklı
 * ondalıklar ("0.0001") eşleşmez. Uyarı amaçlıdır, değer backend'e
 * aynen gider.
 */
export function looksLikeThousandsSeparator(text: string): boolean {
  return THOUSANDS_PATTERN.test(text);
}

/**
 * Form → önizleme/oluşturma gövdesi. Biçimi bozuk alan varsa `null`
 * döner; ayrıntılı doğrulama backend'indir.
 */
export function formToStrategy(form: WizardForm): DcaStrategy | null {
  const texts = [
    form.baseOrder,
    form.safetyOrder,
    form.priceDeviation,
    form.volumeScale,
    form.stepScale,
    form.takeProfit,
  ];
  if (!texts.every((text) => DECIMAL_PATTERN.test(text))) return null;
  if (form.symbol.trim() === "") return null;
  const maxSafetyOrders = parseCount(form.maxSafetyOrders);
  if (maxSafetyOrders === null) return null;
  let maxActive: number | null = null;
  if (form.maxActiveSafetyOrders.trim() !== "") {
    maxActive = parseCount(form.maxActiveSafetyOrders);
    if (maxActive === null) return null;
  }
  let stopLoss: string | null = null;
  if (form.stopLossEnabled) {
    if (!DECIMAL_PATTERN.test(form.stopLoss)) return null;
    stopLoss = form.stopLoss;
  }
  let trailingTakeProfit: string | null = null;
  if (form.trailingEnabled) {
    if (!DECIMAL_PATTERN.test(form.trailingTakeProfit)) return null;
    trailingTakeProfit = form.trailingTakeProfit;
  }
  // Bos kaldirac backend default'una birakilir (null); bos cooldown
  // kapali (0), bos bant sinirsiz (null) demektir.
  let leverage: number | null = null;
  if (form.leverage.trim() !== "") {
    const parsedLeverage = parseCount(form.leverage.trim());
    if (parsedLeverage === null) return null;
    leverage = parsedLeverage;
  }
  let cooldown = 0;
  if (form.cooldown.trim() !== "") {
    const parsed = parseCooldown(form.cooldown.trim());
    if (parsed === null) return null;
    cooldown = parsed;
  }
  let minPrice: string | null = null;
  if (form.minPrice.trim() !== "") {
    if (!DECIMAL_PATTERN.test(form.minPrice.trim())) return null;
    minPrice = form.minPrice.trim();
  }
  let maxPrice: string | null = null;
  if (form.maxPrice.trim() !== "") {
    if (!DECIMAL_PATTERN.test(form.maxPrice.trim())) return null;
    maxPrice = form.maxPrice.trim();
  }
  const extras = parseExtraSymbols(form.extraSymbols);
  if (extras === null) return null;
  const symbol = form.symbol.trim().toUpperCase();
  const deduped = extras.filter((extra) => extra !== symbol);
  const symbols = deduped.length === 0 ? null : [symbol, ...deduped];
  let maxActiveDeals: number | null = null;
  if (form.maxActiveDeals.trim() !== "") {
    maxActiveDeals = parseCount(form.maxActiveDeals.trim());
    if (maxActiveDeals === null) return null;
  }
  let combinedTakeProfit: string | null = null;
  if (form.comboTakeProfit.trim() !== "") {
    if (!DECIMAL_PATTERN.test(form.comboTakeProfit.trim())) return null;
    combinedTakeProfit = form.comboTakeProfit.trim();
  }
  return {
    symbol,
    symbols,
    base_order: form.baseOrder,
    safety_order: form.safetyOrder,
    max_safety_orders: maxSafetyOrders,
    max_active_safety_orders: maxActive,
    max_active_deals: maxActiveDeals,
    combined_take_profit: combinedTakeProfit,
    price_deviation: form.priceDeviation,
    safety_order_volume_scale: form.volumeScale,
    safety_order_step_scale: form.stepScale,
    take_profit: form.takeProfit,
    trailing_take_profit: trailingTakeProfit,
    stop_loss: stopLoss,
    direction: form.direction,
    market_type: form.market,
    leverage,
    cooldown_seconds: cooldown,
    min_price: minPrice,
    max_price: maxPrice,
  };
}

const STRATEGY_FIELD_KEYS: Record<string, keyof WizardForm> = {
  symbol: "symbol",
  symbols: "extraSymbols",
  base_order: "baseOrder",
  safety_order: "safetyOrder",
  max_safety_orders: "maxSafetyOrders",
  max_active_safety_orders: "maxActiveSafetyOrders",
  max_active_deals: "maxActiveDeals",
  combined_take_profit: "comboTakeProfit",
  price_deviation: "priceDeviation",
  safety_order_volume_scale: "volumeScale",
  safety_order_step_scale: "stepScale",
  take_profit: "takeProfit",
  trailing_take_profit: "trailingTakeProfit",
  stop_loss: "stopLoss",
  direction: "direction",
  market_type: "market",
  leverage: "leverage",
  cooldown_seconds: "cooldown",
  min_price: "minPrice",
  max_price: "maxPrice",
};

/** `strategy.<alan>` → form anahtarı (sihirbaz ve backtest ortak). */
export function strategyFieldKey(field: string): keyof WizardForm | null {
  if (!field.startsWith("strategy.")) return null;
  return STRATEGY_FIELD_KEYS[field.slice("strategy.".length)] ?? null;
}

/** Problem Details `field` → sihirbaz adımı ve form alanı. */
export type FieldTarget = { step: number; key: keyof WizardForm | null };

export function problemFieldTarget(field: string): FieldTarget {
  switch (field) {
    case "strategy.symbol":
      return { step: 1, key: "symbol" };
    case "strategy.symbols":
      return { step: 1, key: "extraSymbols" };
    case "strategy.direction":
      return { step: 3, key: "direction" };
    case "strategy.market_type":
      return { step: 3, key: "market" };
    case "strategy.leverage":
      return { step: 3, key: "leverage" };
    case "strategy.cooldown_seconds":
      return { step: 3, key: "cooldown" };
    case "strategy.min_price":
      return { step: 3, key: "minPrice" };
    case "strategy.max_price":
      return { step: 3, key: "maxPrice" };
    case "strategy.base_order":
      return { step: 3, key: "baseOrder" };
    case "strategy.safety_order":
      return { step: 4, key: "safetyOrder" };
    case "strategy.max_safety_orders":
      return { step: 4, key: "maxSafetyOrders" };
    case "strategy.max_active_safety_orders":
      return { step: 4, key: "maxActiveSafetyOrders" };
    case "strategy.max_active_deals":
      return { step: 3, key: "maxActiveDeals" };
    case "strategy.price_deviation":
      return { step: 4, key: "priceDeviation" };
    case "strategy.safety_order_volume_scale":
      return { step: 4, key: "volumeScale" };
    case "strategy.safety_order_step_scale":
      return { step: 4, key: "stepScale" };
    case "strategy.take_profit":
      return { step: 5, key: "takeProfit" };
    case "strategy.combined_take_profit":
      return { step: 5, key: "comboTakeProfit" };
    case "strategy.trailing_take_profit":
      return { step: 5, key: "trailingTakeProfit" };
    case "strategy.stop_loss":
      return { step: 5, key: "stopLoss" };
    case "budget":
      return { step: 6, key: "budget" };
    default:
      return { step: 7, key: null };
  }
}

/**
 * Durum → izinli eylemler. Backend geçiş tablosunun aynasıdır;
 * Running/Paused satırları bugün boş kalır (çalıştırıcı yok) ama
 * tablo geleceğe hazırdır.
 */
export function allowedActions(status: string): BotAction[] {
  switch (status) {
    case "RUNNING":
      return ["pause", "stop"];
    case "PAUSED":
      return ["resume", "stop"];
    case "STOPPED":
      return ["start", "archive"];
    case "ERROR":
      return ["stop"];
    default:
      return [];
  }
}

export const BOT_STATUSES = ["RUNNING", "PAUSED", "STOPPED", "ERROR"] as const;

/** Grid sihirbaz formu; sayılar metindir, doğrulama backend'indir. */
export type GridWizardForm = {
  symbol: string;
  mode: "ARITHMETIC" | "GEOMETRIC";
  lowerPrice: string;
  upperPrice: string;
  intervalCount: string;
  budget: string;
  feeRate: string;
  stopLossEnabled: boolean;
  stopLossPrice: string;
  takeProfitPct: string;
  trailingUpPct: string;
  trailingDownPct: string;
  name: string;
  direction: "LONG" | "SHORT";
  leverage: string;
};

/** Grid sayısı (1..1000); basamak birikimiyle çevrilir. */
export function parseGridCount(text: string): number | null {
  if (!/^\d{1,4}$/.test(text)) return null;
  let value = 0;
  for (const char of text) value = value * 10 + (char.charCodeAt(0) - 48);
  if (value < 1 || value > 1000) return null;
  return value;
}

/**
 * Grid formu → önizleme/oluşturma gövdesi. Boş yüzde/alanlar `null`
 * gider (özellik kapalı); biçim bozuksa `null` döner.
 */
export function formToGridStrategy(form: GridWizardForm): GridBotStrategy | null {
  const texts = [form.lowerPrice, form.upperPrice, form.feeRate];
  if (!texts.every((text) => DECIMAL_PATTERN.test(text))) return null;
  if (form.symbol.trim() === "") return null;
  const intervalCount = parseGridCount(form.intervalCount.trim());
  if (intervalCount === null) return null;
  let stopLossPrice: string | null = null;
  if (form.stopLossEnabled) {
    if (!DECIMAL_PATTERN.test(form.stopLossPrice)) return null;
    stopLossPrice = form.stopLossPrice;
  }
  const optional = (text: string): string | null => {
    const trimmed = text.trim();
    if (trimmed === "") return null;
    return DECIMAL_PATTERN.test(trimmed) ? trimmed : null;
  };
  const takeProfitPct = optional(form.takeProfitPct);
  const trailingUpPct = optional(form.trailingUpPct);
  const trailingDownPct = optional(form.trailingDownPct);
  if (
    (form.takeProfitPct.trim() !== "" && takeProfitPct === null) ||
    (form.trailingUpPct.trim() !== "" && trailingUpPct === null) ||
    (form.trailingDownPct.trim() !== "" && trailingDownPct === null)
  ) {
    return null;
  }
  return {
    symbol: form.symbol.trim(),
    mode: form.mode,
    lower_price: form.lowerPrice,
    upper_price: form.upperPrice,
    interval_count: intervalCount,
    fee_rate: form.feeRate,
    stop_loss_price: stopLossPrice,
    take_profit_pct: takeProfitPct,
    trailing_up_pct: trailingUpPct,
    trailing_down_pct: trailingDownPct,
  };
}

/** Kaldıraç (1..10); basamak birikimiyle çevrilir. */
export function parseLeverage(text: string): number | null {
  if (!/^\d{1,2}$/.test(text)) return null;
  let value = 0;
  for (const char of text) value = value * 10 + (char.charCodeAt(0) - 48);
  if (value < 1 || value > 10) return null;
  return value;
}

/**
 * Futures grid formu → önizleme/oluşturma gövdesi. Ortak alanlar spot
 * ile aynı kuralla çevrilir; biçim bozuksa `null` döner.
 */
export function formToFuturesGridStrategy(form: GridWizardForm): FuturesGridBotStrategy | null {
  const spot = formToGridStrategy(form);
  if (spot === null) return null;
  const leverage = parseLeverage(form.leverage.trim());
  if (leverage === null) return null;
  return { ...spot, direction: form.direction, leverage };
}

export type GridFieldTarget = { step: number; key: keyof GridWizardForm | null };

/** Backend grid hata alanı → sihirbaz adımı ve form anahtarı. */
export function gridProblemFieldTarget(field: string): GridFieldTarget {
  switch (field) {
    case "strategy.symbol":
      return { step: 1, key: "symbol" };
    case "strategy.mode":
      return { step: 1, key: "mode" };
    case "strategy.direction":
      return { step: 1, key: "direction" };
    case "strategy.leverage":
      return { step: 2, key: "leverage" };
    case "strategy.lower_price":
    case "strategy.upper_price":
      return { step: 2, key: "lowerPrice" };
    case "strategy.interval_count":
      return { step: 2, key: "intervalCount" };
    case "strategy.fee_rate":
      return { step: 2, key: "feeRate" };
    case "strategy.stop_loss_price":
      return { step: 2, key: "stopLossPrice" };
    case "strategy.take_profit_pct":
      return { step: 2, key: "takeProfitPct" };
    case "strategy.trailing_up_pct":
      return { step: 2, key: "trailingUpPct" };
    case "strategy.trailing_down_pct":
      return { step: 2, key: "trailingDownPct" };
    case "budget":
      return { step: 2, key: "budget" };
    default:
      return { step: 3, key: null };
  }
}
