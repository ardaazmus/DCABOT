import { describe, expect, it } from "vitest";

import {
  backtestFieldTarget,
  defaultBacktestRange,
  estimateBarCount,
  parseBacktestPrefill,
  quickRangeStart,
  wizardFormToSearchParams,
  type BacktestInterval,
} from "./backtest";
import { PRESETS, type WizardForm } from "./bots";

describe("tahmini mum sayısı (tam sayı bölmesi)", () => {
  it("14 gün 1h = 336 mum", () => {
    expect(estimateBarCount("1h", "2026-09-01", "2026-09-14")).toBe(336);
  });

  it("tek gün dahildir", () => {
    expect(estimateBarCount("1d", "2026-09-01", "2026-09-01")).toBe(1);
    expect(estimateBarCount("15m", "2026-09-01", "2026-09-01")).toBe(96);
  });

  it("15m + 1 yıl sınırı aşar", () => {
    const bars = estimateBarCount("15m", "2025-09-01", "2026-09-01");
    expect(bars).not.toBeNull();
    expect(bars as number).toBeGreaterThan(20_000);
  });

  it("geçersiz aralık null verir", () => {
    expect(estimateBarCount("1h", "2026-09-14", "2026-09-01")).toBeNull();
    expect(estimateBarCount("1h", "2026-13-45", "2026-09-01")).toBeNull();
    expect(estimateBarCount("1h", "2026-02-30", "2026-09-01")).toBeNull();
  });
});

describe("varsayılan aralık ve hızlı çipler", () => {
  it("bitiş dündür, 90 gün geriye gider", () => {
    const range = defaultBacktestRange(Date.UTC(2026, 8, 24, 12));
    expect(range).toEqual({ start: "2026-06-26", end: "2026-09-23" });
  });

  it("hızlı çip başlangıcı geri alır", () => {
    expect(quickRangeStart("2026-09-23", 30)).toBe("2026-08-25");
    expect(quickRangeStart("2026-09-23", 365)).toBe("2025-09-24");
    expect(quickRangeStart("bozuk", 30)).toBeNull();
  });
});

function wizardForm(): WizardForm {
  return {
    symbol: "BTCUSDT",
    direction: "LONG",
    market: "FUTURES",
    leverage: "7",
    cooldown: "300",
    minPrice: "80000",
    extraSymbols: "ETHUSDT",
    maxPrice: "",
    ...PRESETS.balanced,
    stopLossEnabled: true,
    trailingEnabled: true,
    maxActiveDeals: "2",
    comboTakeProfit: "1",
    budget: "1000",
    name: "X",
  };
}

describe("sihirbaz/backtest URL köprüsü", () => {
  it("form parametrelere yazılır ve geri okunur", () => {
    const params = wizardFormToSearchParams(wizardForm(), {
      interval: "1h",
      startDate: "2026-09-01",
      endDate: "2026-09-14",
    });
    const prefill = parseBacktestPrefill(params);
    expect(prefill).toMatchObject({
      symbol: "BTCUSDT",
      direction: "LONG",
      market: "FUTURES",
      extraSymbols: "ETHUSDT",
      leverage: "7",
      cooldown: "300",
      minPrice: "80000",
      baseOrder: "25",
      maxSafetyOrders: "6",
      maxActiveSafetyOrders: "2",
      stopLossEnabled: true,
      trailingEnabled: true,
      maxActiveDeals: "2",
      comboTakeProfit: "1",
      trailingTakeProfit: "1",
      stopLoss: "5",
      budget: "1000",
      interval: "1h",
      startDate: "2026-09-01",
      endDate: "2026-09-14",
    });
  });

  it("bozuk yön atlanır, SHORT taşınır", () => {
    expect(parseBacktestPrefill(new URLSearchParams("direction=SIDEWAYS")).direction).toBeUndefined();
    expect(parseBacktestPrefill(new URLSearchParams("direction=SHORT")).direction).toBe("SHORT");
  });

  it("bozuk pazar/kaldıraç atlanır", () => {
    expect(parseBacktestPrefill(new URLSearchParams("market=MARGIN")).market).toBeUndefined();
    expect(parseBacktestPrefill(new URLSearchParams("leverage=3.5")).leverage).toBeUndefined();
    expect(parseBacktestPrefill(new URLSearchParams("market=FUTURES")).market).toBe("FUTURES");
  });

  it("bozuk cooldown atlanır", () => {
    expect(parseBacktestPrefill(new URLSearchParams("cooldown=3.5")).cooldown).toBeUndefined();
    expect(parseBacktestPrefill(new URLSearchParams("cooldown=300")).cooldown).toBe("300");
  });

  it("biçimi bozuk değerler atlanır", () => {
    const prefill = parseBacktestPrefill(
      new URLSearchParams("base_order=abc&max_so=6.5&interval=7m&start=2026-13-45&sl_enabled=1"),
    );
    expect(prefill.baseOrder).toBeUndefined();
    expect(prefill.maxSafetyOrders).toBeUndefined();
    expect(prefill.interval).toBeUndefined();
    expect(prefill.startDate).toBeUndefined();
    expect(prefill.stopLossEnabled).toBe(true);
  });

  it("Problem Details field form alanına gider (gerçek kayıtlar)", () => {
    expect(backtestFieldTarget("start_date")).toBe("startDate");
    expect(backtestFieldTarget("end_date")).toBe("endDate");
    expect(backtestFieldTarget("interval")).toBe("interval");
    expect(backtestFieldTarget("budget")).toBe("budget");
    expect(backtestFieldTarget("strategy.base_order")).toBe("baseOrder");
    expect(backtestFieldTarget("strategy.symbol")).toBe("symbol");
    expect(backtestFieldTarget("strategy")).toBeNull();
    expect(backtestFieldTarget("bilinmeyen")).toBeNull();
  });

  it("aralık türü korunur", () => {
    const interval: BacktestInterval = parseBacktestPrefill(
      new URLSearchParams("interval=4h"),
    ).interval as BacktestInterval;
    expect(interval).toBe("4h");
  });
});
