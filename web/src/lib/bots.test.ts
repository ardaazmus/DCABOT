import { describe, expect, it } from "vitest";

import {
  PRESETS,
  allowedActions,
  detectPreset,
  formToStrategy,
  isDecimalText,
  looksLikeThousandsSeparator,
  parseCooldown,
  parseCount,
  parseExtraSymbols,
  problemFieldTarget,
  type WizardForm,
} from "./bots";

function formWith(overrides: Partial<WizardForm>): WizardForm {
  return {
    symbol: "BTCUSDT",
    extraSymbols: "",
    direction: "LONG",
    market: "SPOT",
    leverage: "",
    cooldown: "",
    minPrice: "",
    maxPrice: "",
    baseOrder: PRESETS.balanced.baseOrder,
    safetyOrder: PRESETS.balanced.safetyOrder,
    maxSafetyOrders: PRESETS.balanced.maxSafetyOrders,
    maxActiveSafetyOrders: PRESETS.balanced.maxActiveSafetyOrders,
    maxActiveDeals: "",
    priceDeviation: PRESETS.balanced.priceDeviation,
    volumeScale: PRESETS.balanced.volumeScale,
    stepScale: PRESETS.balanced.stepScale,
    takeProfit: PRESETS.balanced.takeProfit,
    comboTakeProfit: "",
    trailingEnabled: false,
    trailingTakeProfit: PRESETS.balanced.trailingTakeProfit,
    stopLossEnabled: false,
    stopLoss: PRESETS.balanced.stopLoss,
    budget: "600",
    name: "",
    ...overrides,
  };
}

describe("hazır ayarlar", () => {
  it("brief tablosundaki değerleri taşır", () => {
    expect(PRESETS.conservative).toMatchObject({
      baseOrder: "20",
      safetyOrder: "20",
      maxSafetyOrders: "8",
      maxActiveSafetyOrders: "3",
      priceDeviation: "2",
      volumeScale: "1.2",
      stepScale: "1.3",
      takeProfit: "1.5",
    });
    expect(PRESETS.balanced).toMatchObject({
      baseOrder: "25",
      safetyOrder: "25",
      maxSafetyOrders: "6",
      maxActiveSafetyOrders: "2",
      priceDeviation: "1.5",
      volumeScale: "1.5",
      stepScale: "1.2",
      takeProfit: "2",
    });
    expect(PRESETS.aggressive).toMatchObject({
      baseOrder: "50",
      safetyOrder: "50",
      maxSafetyOrders: "5",
      maxActiveSafetyOrders: "2",
      priceDeviation: "1",
      volumeScale: "2",
      stepScale: "1",
      takeProfit: "3",
    });
  });

  it("hazır ayar değerleri ayarı gösterir", () => {
    expect(detectPreset(formWith({}))).toBe("balanced");
    expect(
      detectPreset(formWith({ ...PRESETS.conservative, stopLossEnabled: true })),
    ).toBe("conservative");
  });

  it("bir alan elle değişince Özel'e geçer", () => {
    expect(detectPreset(formWith({ baseOrder: "26" }))).toBe("custom");
    expect(detectPreset(formWith({ maxActiveSafetyOrders: "" }))).toBe("custom");
  });
});

describe("cooldown ayrıştırma", () => {
  it("0..99999999 arası tamsayı", () => {
    expect(parseCooldown("0")).toBe(0);
    expect(parseCooldown("300")).toBe(300);
    expect(parseCooldown("31536000")).toBe(31536000);
  });

  it("bozuk metin null", () => {
    expect(parseCooldown("")).toBeNull();
    expect(parseCooldown("3.5")).toBeNull();
    expect(parseCooldown("-1")).toBeNull();
    expect(parseCooldown("abc")).toBeNull();
    expect(parseCooldown("123456789")).toBeNull();
  });
});

describe("form → strateji", () => {
  it("Dengeli form backend gövdesine çevrilir", () => {
    expect(formToStrategy(formWith({}))).toEqual({
      symbol: "BTCUSDT",
      symbols: null,
      base_order: "25",
      safety_order: "25",
      max_safety_orders: 6,
      max_active_safety_orders: 2,
      max_active_deals: null,
      price_deviation: "1.5",
      safety_order_volume_scale: "1.5",
      safety_order_step_scale: "1.2",
      take_profit: "2",
      combined_take_profit: null,
      trailing_take_profit: null,
      stop_loss: null,
      direction: "LONG",
      market_type: "SPOT",
      leverage: null,
      cooldown_seconds: 0,
      min_price: null,
      max_price: null,
    });
  });

  it("boş max active sınırsız (null), kapalı SL null gönderilir", () => {
    const strategy = formToStrategy(
      formWith({ maxActiveSafetyOrders: "  " }),
    );
    expect(strategy?.max_active_safety_orders).toBeNull();
    expect(strategy?.stop_loss).toBeNull();
  });

  it("SHORT yönü aynen taşınır", () => {
    expect(formToStrategy(formWith({ direction: "SHORT" }))?.direction).toBe("SHORT");
  });

  it("futures pazarı ve kaldıraç taşınır", () => {
    const strategy = formToStrategy(formWith({ market: "FUTURES", leverage: "7" }));
    expect(strategy?.market_type).toBe("FUTURES");
    expect(strategy?.leverage).toBe(7);
  });

  it("bozuk kaldıraç gövdeyi kurdurmaz", () => {
    expect(formToStrategy(formWith({ leverage: "3.5" }))).toBeNull();
    expect(formToStrategy(formWith({ leverage: "-1" }))).toBeNull();
  });

  it("giriş kapıları aynen taşınır", () => {
    const strategy = formToStrategy(formWith({ cooldown: "300", minPrice: "80000", maxPrice: "90000" }));
    expect(strategy?.cooldown_seconds).toBe(300);
    expect(strategy?.min_price).toBe("80000");
    expect(strategy?.max_price).toBe("90000");
  });

  it("boş kapılar kapalı/sınırsız gider", () => {
    const strategy = formToStrategy(formWith({}));
    expect(strategy?.cooldown_seconds).toBe(0);
    expect(strategy?.min_price).toBeNull();
    expect(strategy?.max_price).toBeNull();
  });

  it("bozuk kapı gövdeyi kurdurmaz", () => {
    expect(formToStrategy(formWith({ cooldown: "3.5" }))).toBeNull();
    expect(formToStrategy(formWith({ cooldown: "-1" }))).toBeNull();
    expect(formToStrategy(formWith({ minPrice: "abc" }))).toBeNull();
    expect(formToStrategy(formWith({ maxPrice: "90.0.1" }))).toBeNull();
  });


  it("ek semboller liste olur, ana sembol baştadır", () => {
    const strategy = formToStrategy(formWith({ extraSymbols: "ethusdt, SOLUSDT" }));
    expect(strategy?.symbols).toEqual(["BTCUSDT", "ETHUSDT", "SOLUSDT"]);
  });

  it("ana sembol tekrarı ve çiftler elenir", () => {
    const strategy = formToStrategy(formWith({ extraSymbols: "BTCUSDT, ethusdt,ETHUSDT" }));
    expect(strategy?.symbols).toEqual(["BTCUSDT", "ETHUSDT"]);
  });

  it("tek sembolde symbols null kalır", () => {
    expect(formToStrategy(formWith({ extraSymbols: "  " }))?.symbols).toBeNull();
    expect(formToStrategy(formWith({ extraSymbols: "BTCUSDT" }))?.symbols).toBeNull();
  });

  it("bozuk ek sembol formu geçersiz kılar", () => {
    expect(formToStrategy(formWith({ extraSymbols: "BTC" }))).toBeNull();
    expect(formToStrategy(formWith({ extraSymbols: "ETHUSDT!" }))).toBeNull();
  });

  it("max active deals sayıya çevrilir, boş null", () => {
    expect(formToStrategy(formWith({ maxActiveDeals: "3" }))?.max_active_deals).toBe(3);
    expect(formToStrategy(formWith({}))?.max_active_deals).toBeNull();
    expect(formToStrategy(formWith({ maxActiveDeals: "3.5" }))).toBeNull();
  });

  it("birlesik TP tasinir, bos null, bozuk gecersiz", () => {
    expect(formToStrategy(formWith({ comboTakeProfit: "1.5" }))?.combined_take_profit).toBe("1.5");
    expect(formToStrategy(formWith({}))?.combined_take_profit).toBeNull();
    expect(formToStrategy(formWith({ comboTakeProfit: "1,5" }))).toBeNull();
    expect(formToStrategy(formWith({ comboTakeProfit: "abc" }))).toBeNull();
  });

  it("açık trailing metni taşınır, kapalı null, bozuk geçersiz", () => {
    expect(
      formToStrategy(formWith({ trailingEnabled: true, trailingTakeProfit: "1" }))?.trailing_take_profit,
    ).toBe("1");
    expect(formToStrategy(formWith({}))?.trailing_take_profit).toBeNull();
    expect(formToStrategy(formWith({ trailingEnabled: true, trailingTakeProfit: "1,5" }))).toBeNull();
    expect(formToStrategy(formWith({ trailingEnabled: true, trailingTakeProfit: "" }))).toBeNull();
  });

  it("açık SL metni aynen taşınır", () => {
    const strategy = formToStrategy(
      formWith({ stopLossEnabled: true, stopLoss: "5" }),
    );
    expect(strategy?.stop_loss).toBe("5");
  });

  it("biçimi bozuk alan gövdeyi kurdurmaz", () => {
    expect(formToStrategy(formWith({ baseOrder: "abc" }))).toBeNull();
    expect(formToStrategy(formWith({ maxSafetyOrders: "6.5" }))).toBeNull();
    expect(formToStrategy(formWith({ symbol: "  " }))).toBeNull();
    expect(
      formToStrategy(formWith({ stopLossEnabled: true, stopLoss: "" })),
    ).toBeNull();
  });
});

describe("sayaç ve sayı biçimi", () => {
  it("parseCount yalnız 0..99 kabul eder", () => {
    expect(parseCount("6")).toBe(6);
    expect(parseCount("50")).toBe(50);
    expect(parseCount("0")).toBe(0);
    expect(parseCount("")).toBeNull();
    expect(parseCount("6.5")).toBeNull();
    expect(parseCount("abc")).toBeNull();
    expect(parseCount("100")).toBeNull();
  });

  it("binlik ayırıcı şüphesi yakalanır", () => {
    expect(looksLikeThousandsSeparator("1.000")).toBe(true);
    expect(looksLikeThousandsSeparator("1.000,5")).toBe(true);
    expect(looksLikeThousandsSeparator("12.345.678")).toBe(true);
    expect(looksLikeThousandsSeparator("1.5")).toBe(false);
    expect(looksLikeThousandsSeparator("1.50")).toBe(false);
    expect(looksLikeThousandsSeparator("0.0001")).toBe(false);
    expect(looksLikeThousandsSeparator("25")).toBe(false);
  });

  it("isDecimalText backend deseniyle aynıdır", () => {
    expect(isDecimalText("25")).toBe(true);
    expect(isDecimalText("1.5")).toBe(true);
    expect(isDecimalText("0")).toBe(true);
    expect(isDecimalText("")).toBe(false);
    expect(isDecimalText("01")).toBe(false);
    expect(isDecimalText("-3")).toBe(false);
  });

  it("parseExtraSymbols virgül/boşluk ayırır, büyük harfe çevirir", () => {
    expect(parseExtraSymbols("")).toEqual([]);
    expect(parseExtraSymbols("   ")).toEqual([]);
    expect(parseExtraSymbols("ethusdt solusdt")).toEqual(["ETHUSDT", "SOLUSDT"]);
    expect(parseExtraSymbols("ETHUSDT,ETHUSDT")).toEqual(["ETHUSDT"]);
    expect(parseExtraSymbols("BTC")).toBeNull();
    expect(parseExtraSymbols("ETHUSDT!")).toBeNull();
  });
});

describe("Problem Details field → form alanı", () => {
  it("her alan doğru adıma gider", () => {
    expect(problemFieldTarget("strategy.symbol")).toEqual({ step: 1, key: "symbol" });
    expect(problemFieldTarget("strategy.symbols")).toEqual({ step: 1, key: "extraSymbols" });
    expect(problemFieldTarget("strategy.direction")).toEqual({ step: 3, key: "direction" });
    expect(problemFieldTarget("strategy.market_type")).toEqual({ step: 3, key: "market" });
    expect(problemFieldTarget("strategy.leverage")).toEqual({ step: 3, key: "leverage" });
    expect(problemFieldTarget("strategy.cooldown_seconds")).toEqual({ step: 3, key: "cooldown" });
    expect(problemFieldTarget("strategy.min_price")).toEqual({ step: 3, key: "minPrice" });
    expect(problemFieldTarget("strategy.max_price")).toEqual({ step: 3, key: "maxPrice" });
    expect(problemFieldTarget("strategy.max_active_deals")).toEqual({ step: 3, key: "maxActiveDeals" });
    expect(problemFieldTarget("strategy.base_order")).toEqual({ step: 3, key: "baseOrder" });
    expect(problemFieldTarget("strategy.safety_order")).toEqual({ step: 4, key: "safetyOrder" });
    expect(problemFieldTarget("strategy.max_safety_orders")).toEqual({ step: 4, key: "maxSafetyOrders" });
    expect(problemFieldTarget("strategy.max_active_safety_orders")).toEqual({
      step: 4,
      key: "maxActiveSafetyOrders",
    });
    expect(problemFieldTarget("strategy.price_deviation")).toEqual({ step: 4, key: "priceDeviation" });
    expect(problemFieldTarget("strategy.safety_order_volume_scale")).toEqual({ step: 4, key: "volumeScale" });
    expect(problemFieldTarget("strategy.safety_order_step_scale")).toEqual({ step: 4, key: "stepScale" });
    expect(problemFieldTarget("strategy.take_profit")).toEqual({ step: 5, key: "takeProfit" });
    expect(problemFieldTarget("strategy.combined_take_profit")).toEqual({ step: 5, key: "comboTakeProfit" });
    expect(problemFieldTarget("strategy.trailing_take_profit")).toEqual({ step: 5, key: "trailingTakeProfit" });
    expect(problemFieldTarget("strategy.stop_loss")).toEqual({ step: 5, key: "stopLoss" });
    expect(problemFieldTarget("budget")).toEqual({ step: 6, key: "budget" });
  });

  it("genel strateji hatası özet adımına gider", () => {
    expect(problemFieldTarget("strategy")).toEqual({ step: 7, key: null });
    expect(problemFieldTarget("bilinmeyen")).toEqual({ step: 7, key: null });
  });
});

describe("durum → izinli eylemler", () => {
  it("tüm durumlar brief tablosuna uyar", () => {
    expect(allowedActions("RUNNING")).toEqual(["pause", "stop"]);
    expect(allowedActions("PAUSED")).toEqual(["resume", "stop"]);
    expect(allowedActions("STOPPED")).toEqual(["start", "archive"]);
    expect(allowedActions("ERROR")).toEqual(["stop"]);
    expect(allowedActions("BILINMEYEN")).toEqual([]);
  });
});
