import { describe, expect, it } from "vitest";

import {
  anyGridStateEnvelopeSchema,
  botEnvelopeSchema,
  futuresGridPreviewEnvelopeSchema,
  gridPreviewEnvelopeSchema,
  gridStateEnvelopeSchema,
  isFuturesGridState,
  isFuturesGridStrategy,
  isGridStrategy,
} from "./schemas";

const GRID_BOT = {
  bot_id: "bot_grid1",
  name: "Grid test",
  type: "GRID",
  mode: "PAPER",
  status: "STOPPED",
  status_reason: null,
  symbol: "BTCUSDT",
  budget: "900",
  strategy: {
    symbol: "BTCUSDT",
    mode: "ARITHMETIC",
    lower_price: "80000",
    upper_price: "89000",
    interval_count: 9,
    fee_rate: "0.001",
    stop_loss_price: null,
    take_profit_pct: null,
    trailing_up_pct: null,
    trailing_down_pct: null,
  },
  revision: 1,
  created_at_us: 1,
  updated_at_us: 1,
  archived: false,
};

describe("grid şemaları", () => {
  it("grid botu birlikten geçer ve ayırt edilir", () => {
    const parsed = botEnvelopeSchema.parse({ data: GRID_BOT }).data;
    expect(parsed.type).toBe("GRID");
    expect(isGridStrategy(parsed.strategy)).toBe(true);
    if (!isGridStrategy(parsed.strategy)) return;
    expect(parsed.strategy.lower_price).toBe("80000");
  });

  it("grid stratejisi defaults ile okunur", () => {
    const parsed = botEnvelopeSchema.parse({
      data: {
        ...GRID_BOT,
        strategy: {
          symbol: "BTCUSDT",
          lower_price: "80000",
          upper_price: "89000",
          interval_count: 9,
        },
      },
    }).data;
    if (!isGridStrategy(parsed.strategy)) return;
    expect(parsed.strategy.mode).toBe("ARITHMETIC");
    expect(parsed.strategy.fee_rate).toBe("0.001");
    expect(parsed.strategy.stop_loss_price).toBeNull();
  });

  it("grid önizleme ve durum zarfları doğrulanır", () => {
    const preview = gridPreviewEnvelopeSchema.parse({
      data: {
        symbol: "BTCUSDT",
        reference_price: "84506.01",
        entry_position: "WITHIN",
        levels: ["80000", "81000"],
        interval_count: 1,
        investment_quote: "900",
        quote_per_grid: "900",
        base_step_size: "0.00001",
        fee_rate: "0.001",
        within_min_notional: true,
        stop_loss_price: null,
        take_profit_pct: null,
        trailing_up_pct: null,
        trailing_down_pct: null,
      },
    });
    expect(preview.data.quote_per_grid).toBe("900");
    const state = gridStateEnvelopeSchema.parse({
      data: {
        grid_status: "ACTIVE",
        entry_price: "81250",
        last_price: "81200",
        levels: ["80000", "81000"],
        pending: ["SELL"],
        locked_quote: ["0"],
        locked_base: ["0.00125"],
        quote_reserve: "0.5",
        base_free: "0",
        cycles_closed: 1,
        realized_profit_quote: "-798.25",
        fees_paid_quote: "0.9",
        equity_at_last: "901.5",
        fills_recent: [{ fill_id: "grid:9", side: "SELL", price: "81000", base_quantity: "0.00125" }],
        trailing_shifts: 0,
        last_bar_open_us: 1,
        updated_at_us: 2,
      },
    });
    expect(state.data.cycles_closed).toBe(1);
  });

  it("futures grid botu birlikten geçer ve ayırt edilir", () => {
    const parsed = botEnvelopeSchema.parse({
      data: {
        ...GRID_BOT,
        type: "FUTURES_GRID",
        strategy: { ...GRID_BOT.strategy, direction: "SHORT", leverage: 3 },
      },
    }).data;
    expect(isGridStrategy(parsed.strategy)).toBe(true);
    expect(isFuturesGridStrategy(parsed.strategy)).toBe(true);
    if (!isFuturesGridStrategy(parsed.strategy)) return;
    expect(parsed.strategy.leverage).toBe(3);
    expect(parsed.strategy.direction).toBe("SHORT");
  });

  it("spot grid futures değildir", () => {
    const parsed = botEnvelopeSchema.parse({ data: GRID_BOT }).data;
    expect(isFuturesGridStrategy(parsed.strategy)).toBe(false);
  });

  it("futures önizleme ve durum zarfları doğrulanır", () => {
    const preview = futuresGridPreviewEnvelopeSchema.parse({
      data: {
        symbol: "BTCUSDT",
        direction: "LONG",
        leverage: 5,
        reference_price: "84506.01",
        entry_position: "WITHIN",
        levels: ["80000", "81000"],
        interval_count: 1,
        investment_quote: "900",
        quote_per_grid: "900",
        notional_per_grid: "4500",
        base_step_size: "0.00001",
        fee_rate: "0.0005",
        within_min_notional: true,
        stop_loss_price: null,
        take_profit_pct: null,
        trailing_up_pct: null,
        trailing_down_pct: null,
      },
    });
    expect(preview.data.notional_per_grid).toBe("4500");
    const state = anyGridStateEnvelopeSchema.parse({
      data: {
        grid_status: "ACTIVE",
        direction: "LONG",
        leverage: 5,
        entry_price: "81250",
        last_price: "81200",
        levels: ["80000", "81000"],
        pending: ["SELL"],
        locked_margin: ["0"],
        wallet_free: "100",
        open_lots: [{ interval: 0, quantity: "0.001", entry_price: "81250", locked_margin: "16.25" }],
        cycles_closed: 1,
        realized_gross_pnl: "5",
        fees_paid_quote: "0.9",
        funding_cashflow: "-0.01",
        funding_events_count: 2,
        equity_at_last: "901.5",
        fills_recent: [{ fill_id: "fgrid:9", side: "SELL", price: "81000", quantity: "0.001" }],
        trailing_shifts: 0,
        liq_estimate_price: null,
        liq_estimate_tier: null,
        last_bar_open_us: 1,
        updated_at_us: 2,
      },
    });
    expect(isFuturesGridState(state.data)).toBe(true);
  });

  it("spot durum birleşim zarftan spot olarak okunur", () => {
    const state = anyGridStateEnvelopeSchema.parse({
      data: {
        grid_status: "ACTIVE",
        entry_price: "81250",
        last_price: "81200",
        levels: ["80000", "81000"],
        pending: ["SELL"],
        locked_quote: ["0"],
        locked_base: ["0.00125"],
        quote_reserve: "0.5",
        base_free: "0",
        cycles_closed: 1,
        realized_profit_quote: "-798.25",
        fees_paid_quote: "0.9",
        equity_at_last: "901.5",
        fills_recent: [{ fill_id: "grid:9", side: "SELL", price: "81000", base_quantity: "0.00125" }],
        trailing_shifts: 0,
        last_bar_open_us: 1,
        updated_at_us: 2,
      },
    });
    expect(isFuturesGridState(state.data)).toBe(false);
  });
});
