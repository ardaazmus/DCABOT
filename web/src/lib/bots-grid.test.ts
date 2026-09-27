import { describe, expect, it } from "vitest";

import {
  formToFuturesGridStrategy,
  formToGridStrategy,
  gridProblemFieldTarget,
  parseGridCount,
  parseLeverage,
  type GridWizardForm,
} from "./bots";

function gridForm(): GridWizardForm {
  return {
    symbol: "BTCUSDT",
    mode: "ARITHMETIC",
    lowerPrice: "80000",
    upperPrice: "89000",
    intervalCount: "9",
    budget: "900",
    feeRate: "0.001",
    stopLossEnabled: false,
    stopLossPrice: "",
    takeProfitPct: "",
    trailingUpPct: "",
    trailingDownPct: "",
    name: "",
    direction: "LONG",
    leverage: "5",
  };
}

describe("grid sihirbaz yardımcıları", () => {
  it("sayı 1-1000 aralığında basamak birikimiyle okunur", () => {
    expect(parseGridCount("9")).toBe(9);
    expect(parseGridCount("1000")).toBe(1000);
    expect(parseGridCount("0")).toBeNull();
    expect(parseGridCount("1001")).toBeNull();
    expect(parseGridCount("1.5")).toBeNull();
    expect(parseGridCount("")).toBeNull();
  });

  it("form stratejiye çevrilir; boş opsiyoneller null gider", () => {
    const strategy = formToGridStrategy(gridForm());
    expect(strategy).toMatchObject({
      symbol: "BTCUSDT",
      mode: "ARITHMETIC",
      lower_price: "80000",
      interval_count: 9,
      stop_loss_price: null,
      take_profit_pct: null,
    });
  });

  it("boş sembol/sayı/yüzde gövdeyi kurmaz", () => {
    expect(formToGridStrategy({ ...gridForm(), symbol: "" })).toBeNull();
    expect(formToGridStrategy({ ...gridForm(), intervalCount: "0" })).toBeNull();
    expect(formToGridStrategy({ ...gridForm(), lowerPrice: "1,000" })).toBeNull();
    expect(formToGridStrategy({ ...gridForm(), takeProfitPct: "abc" })).toBeNull();
    expect(
      formToGridStrategy({ ...gridForm(), stopLossEnabled: true, stopLossPrice: "" }),
    ).toBeNull();
  });

  it("stop-loss açıkken fiyat gövdeye girer", () => {
    const strategy = formToGridStrategy({
      ...gridForm(),
      stopLossEnabled: true,
      stopLossPrice: "78000",
    });
    expect(strategy?.stop_loss_price).toBe("78000");
  });

  it("backend alanları grid adımlarına eşlenir", () => {
    expect(gridProblemFieldTarget("strategy.symbol")).toEqual({ step: 1, key: "symbol" });
    expect(gridProblemFieldTarget("strategy.mode")).toEqual({ step: 1, key: "mode" });
    expect(gridProblemFieldTarget("strategy.direction")).toEqual({ step: 1, key: "direction" });
    expect(gridProblemFieldTarget("strategy.lower_price")).toEqual({ step: 2, key: "lowerPrice" });
    expect(gridProblemFieldTarget("strategy.interval_count")).toEqual({ step: 2, key: "intervalCount" });
    expect(gridProblemFieldTarget("strategy.leverage")).toEqual({ step: 2, key: "leverage" });
    expect(gridProblemFieldTarget("budget")).toEqual({ step: 2, key: "budget" });
    expect(gridProblemFieldTarget("strategy")).toEqual({ step: 3, key: null });
  });

  it("kaldıraç 1-10 aralığında okunur", () => {
    expect(parseLeverage("1")).toBe(1);
    expect(parseLeverage("10")).toBe(10);
    expect(parseLeverage("0")).toBeNull();
    expect(parseLeverage("11")).toBeNull();
    expect(parseLeverage("5x")).toBeNull();
  });

  it("futures formu yön+kaldıraçla stratejiye çevrilir", () => {
    const strategy = formToFuturesGridStrategy({ ...gridForm(), direction: "SHORT", leverage: "3" });
    expect(strategy).toMatchObject({ direction: "SHORT", leverage: 3, symbol: "BTCUSDT", interval_count: 9 });
    expect(formToFuturesGridStrategy({ ...gridForm(), leverage: "11" })).toBeNull();
    expect(formToFuturesGridStrategy({ ...gridForm(), intervalCount: "0" })).toBeNull();
  });
});
