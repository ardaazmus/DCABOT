import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  RebalancePanel,
  isRebalanceValuation,
  parsePairLines,
  type RebalanceValuation,
} from "./RebalancePanel";

const valuation: RebalanceValuation = {
  valuation_asset: "USDT",
  total_equity: "600",
  positions: [
    { asset: "BTC", qty: "0.01", price: "50000", value: "500" },
    { asset: "USDT", qty: "100", price: "1", value: "100" },
  ],
};

describe("isRebalanceValuation", () => {
  it("geçerli değerlemeyi kabul eder, sayı tipini reddeder", () => {
    expect(isRebalanceValuation(valuation)).toBe(true);
    expect(isRebalanceValuation({ ...valuation, total_equity: 600 })).toBe(false);
    expect(isRebalanceValuation(null)).toBe(false);
  });
});

describe("parsePairLines", () => {
  it("boş satırları atlar, çiftleri korur", () => {
    expect(parsePairLines("BTC 0.01\n\nUSDT 100\n")).toEqual({
      rows: [
        ["BTC", "0.01"],
        ["USDT", "100"],
      ],
      error: "",
    });
  });

  it("bozuk satırda satır numarasıyla hata verir", () => {
    const result = parsePairLines("BTC 0.01 FOO\nETH 1\n");
    expect(result.rows).toEqual([]);
    expect(result.error).toMatch(/Satır 1/);
  });
});

describe("RebalancePanel", () => {
  it("değerleme sonucunu tabloyla gösterir, hesap yapmaz", () => {
    render(
      <RebalancePanel
        valuation={valuation}
        status="ready"
        error=""
        holdingsText="BTC 0.01"
        pricesText="BTC 50000"
        onHoldingsChange={() => {}}
        onPricesChange={() => {}}
        onCalculate={() => {}}
      />,
    );
    expect(screen.getByText("600")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText(/salt okunur projeksiyon/)).toBeInTheDocument();
  });

  it("hesapla düğmesi yalnızca onCalculate çağırır", () => {
    const onCalculate = vi.fn();
    render(
      <RebalancePanel
        valuation={null}
        status="idle"
        error=""
        holdingsText=""
        pricesText=""
        onHoldingsChange={() => {}}
        onPricesChange={() => {}}
        onCalculate={onCalculate}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Değerlemeyi hesapla/ }));
    expect(onCalculate).toHaveBeenCalledTimes(1);
  });

  it("hatayı gösterir, eski sonucu gizler", () => {
    render(
      <RebalancePanel
        valuation={null}
        status="error"
        error="Fiyat eksik."
        holdingsText="BTC 0.01"
        pricesText=""
        onHoldingsChange={() => {}}
        onPricesChange={() => {}}
        onCalculate={() => {}}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Fiyat eksik.");
  });
});
