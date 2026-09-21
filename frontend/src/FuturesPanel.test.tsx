import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  FuturesPanel,
  isFuturesTrailingView,
  type FuturesFundingView,
  type FuturesGridView,
  type FuturesPnlView,
  type FuturesTrailingView,
} from "./FuturesPanel";

const grid: FuturesGridView = {
  levels: ["100", "150", "200"],
  arithmetic_step: "50",
  level_mode: "ARITHMETIC",
};

const pnl: FuturesPnlView = {
  effective_quantity: "1",
  position_value: "51000",
  unrealized_pnl: "1000",
  settlement_asset: "USDT",
};

const trailing: FuturesTrailingView = {
  status: "ACTIVE",
  activation_price: "100",
  distance: "5",
  high_water: "110",
  stop_price: "105",
};

const funding: FuturesFundingView = {
  amount: "-5.1",
  core_expense: "5.1",
  settlement_asset: "USDT",
};

function renderPanel(overrides = {}) {
  const handlers = {
    onGrid: vi.fn(),
    onPnl: vi.fn(),
    onTrailingArm: vi.fn(),
    onTrailingObserve: vi.fn(),
    onFunding: vi.fn(),
    ...overrides,
  };
  render(
    <FuturesPanel
      grid={grid}
      pnl={pnl}
      trailing={trailing}
      funding={funding}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("FuturesPanel", () => {
  it("grid, pnl, trailing ve funding gösterir", () => {
    renderPanel();
    expect(screen.getByText("100 · 150 · 200")).toBeInTheDocument();
    expect(screen.getByText("51000")).toBeInTheDocument();
    expect(screen.getByText("105")).toBeInTheDocument();
    expect(screen.getByText("-5.1")).toBeInTheDocument();
    expect(screen.getByText(/likidasyon yetkisi yok/)).toBeInTheDocument();
  });

  it("grid ve pnl gönderimleri typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Alt fiyat"), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText("Üst fiyat"), { target: { value: "200" } });
    fireEvent.click(screen.getByRole("button", { name: /Seviyeleri üret/ }));
    expect(handlers.onGrid).toHaveBeenCalledWith(
      expect.objectContaining({ lower_price: "100", upper_price: "200" }),
    );
    fireEvent.change(screen.getByLabelText("Mark fiyatı"), { target: { value: "51000" } });
    fireEvent.click(screen.getByRole("button", { name: /PnL hesapla/ }));
    expect(handlers.onPnl).toHaveBeenCalledWith(
      expect.objectContaining({ mark_price: "51000" }),
    );
  });

  it("trailing ve funding gönderimleri typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Aktivasyon"), { target: { value: "100" } });
    fireEvent.click(screen.getByRole("button", { name: /Trailing kur/ }));
    expect(handlers.onTrailingArm).toHaveBeenCalledWith(
      expect.objectContaining({ activation_price: "100" }),
    );
    fireEvent.change(screen.getByLabelText("Gözlenen fiyat"), { target: { value: "110" } });
    fireEvent.click(screen.getByRole("button", { name: /Gözlemi işle/ }));
    expect(handlers.onTrailingObserve).toHaveBeenCalledWith(
      expect.objectContaining({ price: "110" }),
    );
    fireEvent.change(screen.getByLabelText("Funding oranı"), { target: { value: "0.0001" } });
    fireEvent.click(screen.getByRole("button", { name: /Funding hesapla/ }));
    expect(handlers.onFunding).toHaveBeenCalledWith(
      expect.objectContaining({ funding_rate: "0.0001" }),
    );
  });
});

describe("isFuturesTrailingView", () => {
  it("SHORT tarafın low_water taşıyan, high_water'sız yanıtını kabul eder", () => {
    // POST /api/futures/trailing/arm|observe only includes the water-mark
    // field for the armed side: high_water for LONG, low_water for SHORT.
    expect(
      isFuturesTrailingView({
        status: "ACTIVE",
        activation_price: "100",
        distance: "5",
        stop_price: "95",
        low_water: "90",
      }),
    ).toBe(true);
  });

  it("LONG tarafın high_water taşıyan yanıtını kabul eder", () => {
    expect(isFuturesTrailingView(trailing)).toBe(true);
  });

  it("hem high_water hem low_water eksikse reddeder", () => {
    expect(
      isFuturesTrailingView({
        status: "ACTIVE",
        activation_price: "100",
        distance: "5",
        stop_price: "95",
      }),
    ).toBe(false);
  });
});
