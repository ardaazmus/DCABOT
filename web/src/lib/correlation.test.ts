import { describe, expect, it } from "vitest";

import type { Bot, MatrixCell } from "@/lib/api/schemas";

import { botMatrixSymbols, matrixLookup } from "./correlation";

function bot(symbol: string, symbols: string[] | null = null): Bot {
  return {
    bot_id: symbol,
    name: symbol,
    type: "DCA",
    mode: "PAPER",
    status: "STOPPED",
    status_reason: null,
    symbol,
    budget: "1000",
    strategy: {
      symbol,
      base_order: "25",
      safety_order: "25",
      max_safety_orders: 6,
      max_active_safety_orders: 2,
      price_deviation: "1.5",
      safety_order_volume_scale: "1.5",
      safety_order_step_scale: "1.2",
      take_profit: "2",
      stop_loss: null,
      direction: "LONG",
      market_type: "SPOT",
      leverage: null,
      cooldown_seconds: 0,
      min_price: null,
      max_price: null,
      symbols,
      max_active_deals: null,
      combined_take_profit: null,
      trailing_take_profit: null,
    },
    revision: 1,
    created_at_us: 0,
    updated_at_us: 0,
    archived: false,
  };
}

describe("korelasyon sembol seçimi", () => {
  it("tekil sıralar, çoklu-pariteyi açar, 10'da keser", () => {
    const { symbols, truncated } = botMatrixSymbols([
      bot("ETHUSDT"),
      bot("BTCUSDT", ["ETHUSDT", "SOLUSDT"]),
    ]);
    expect(symbols).toEqual(["BTCUSDT", "ETHUSDT", "SOLUSDT"]);
    expect(truncated).toBe(false);
    const many = botMatrixSymbols(
      Array.from({ length: 12 }, (_, i) => bot(`S${i}USDT`)),
    );
    expect(many.symbols).toHaveLength(10);
    expect(many.truncated).toBe(true);
  });
});

describe("matris yansıması", () => {
  const cells: MatrixCell[] = [
    { x: "A", y: "B", coefficient: "0.9100", verdict: "BREACH", detail: null, samples: 31 },
    { x: "A", y: "C", coefficient: null, verdict: "INSUFFICIENT", detail: "INSUFFICIENT_HISTORY", samples: 5 },
  ];

  it("simetrik okur, eksik çifti boş bırakır", () => {
    const lookup = matrixLookup(cells);
    expect(lookup.get("A B")?.verdict).toBe("BREACH");
    expect(lookup.get("B A")?.coefficient).toBe("0.9100");
    expect(lookup.get("C A")?.detail).toBe("INSUFFICIENT_HISTORY");
    expect(lookup.get("B C")).toBeUndefined();
  });
});
