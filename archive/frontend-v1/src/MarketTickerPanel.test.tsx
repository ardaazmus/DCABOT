import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  isVenueTicker24h,
  MarketTickerPanel,
  type VenueTicker24h,
} from "./MarketTickerPanel";

const ticker: VenueTicker24h = {
  environment: "BINANCE_SPOT",
  symbol: "BTCUSDT",
  last_price: "97500.00",
  price_change_percent: "1.25",
  quote_volume: "1234567.89",
  observed_at_us: 1787450000000000,
  read_only: true,
  credential_required: false,
};

describe("MarketTickerPanel", () => {
  it("AA.2b: hazır ticker değerlerini gösterir", () => {
    render(<MarketTickerPanel ticker={ticker} symbol="BTCUSDT" status="ready" error="" onRetry={vi.fn()} />);
    expect(screen.getByText("97500.00")).toBeInTheDocument();
    expect(screen.getByText("1.25")).toBeInTheDocument();
    expect(screen.getByText("1234567.89")).toBeInTheDocument();
    expect(screen.getByText("Güncel")).toBeInTheDocument();
  });

  it("AA.2b: sembol-uyuşmazlığında bayat ticker gösterilmez", () => {
    render(<MarketTickerPanel ticker={ticker} symbol="ETHUSDT" status="loading" error="" onRetry={vi.fn()} />);
    expect(screen.queryByText("97500.00")).not.toBeInTheDocument();
    expect(screen.getByText("Piyasa özeti okunuyor…")).toBeInTheDocument();
  });

  it("AA.2b: hata ve boş durumları", () => {
    const onRetry = vi.fn();
    const { unmount } = render(<MarketTickerPanel ticker={null} symbol="BTCUSDT" status="error" error="venue 502" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("venue 502");
    fireEvent.click(screen.getByRole("button", { name: "Tekrar dene" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
    unmount();
    render(<MarketTickerPanel ticker={null} symbol="BTCUSDT" status="idle" error="" onRetry={vi.fn()} />);
    expect(screen.getByText("Piyasa özeti henüz yüklenmedi.")).toBeInTheDocument();
  });

  it("AA.2b: guard sözleşmesi", () => {
    expect(isVenueTicker24h(ticker)).toBe(true);
    expect(isVenueTicker24h({ ...ticker, environment: "BINANCE_FUTURES" })).toBe(false);
    expect(isVenueTicker24h({ ...ticker, price_change_percent: 1.25 })).toBe(false);
    expect(isVenueTicker24h({ ...ticker, read_only: false })).toBe(false);
    expect(isVenueTicker24h(null)).toBe(false);
    expect(isVenueTicker24h("BTCUSDT")).toBe(false);
  });
});
