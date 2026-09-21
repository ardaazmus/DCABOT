import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CandleChart, LiveTickStrip, type CandleMarker } from "./CandleChart";
import type { HistoricalChartBar } from "./datasetCatalog";

const bars: HistoricalChartBar[] = [
  { bar_index: 1, open_time_us: 1, close_time_us: 2, open: "100", high: "102", low: "99", close: "101", base_volume: "10" },
  { bar_index: 2, open_time_us: 3, close_time_us: 4, open: "101", high: "103", low: "100", close: "102", base_volume: "20" },
  { bar_index: 3, open_time_us: 5, close_time_us: 6, open: "102", high: "102", low: "98", close: "99", base_volume: "30" },
];

describe("CandleChart", () => {
  it("renders one candle per bar with volume", () => {
    render(<CandleChart bars={bars} status="ready" error="" />);
    expect(screen.getByRole("img", { name: /mum grafiği/i })).toBeInTheDocument();
    expect(document.querySelectorAll("[data-candle]").length).toBe(3);
    expect(document.querySelectorAll("[data-volume]").length).toBe(3);
  });

  it("marks up and down candles distinctly (not color-only: doji cross for flat)", () => {
    render(<CandleChart bars={bars} status="ready" error="" />);
    expect(document.querySelectorAll('[data-candle="up"]').length).toBe(2);
    expect(document.querySelectorAll('[data-candle="down"]').length).toBe(1);
    const flat: HistoricalChartBar[] = [
      { bar_index: 1, open_time_us: 1, close_time_us: 2, open: "100", high: "101", low: "99", close: "100", base_volume: "5" },
    ];
    const { unmount } = render(<CandleChart bars={flat} status="ready" error="" />);
    expect(document.querySelectorAll('[data-candle="flat"]').length).toBe(1);
    unmount();
  });

  it("shows trade markers on their bars", () => {
    const markers: CandleMarker[] = [{ barIndex: 2, kind: "buy" }];
    render(<CandleChart bars={bars} status="ready" error="" markers={markers} />);
    expect(document.querySelectorAll("[data-marker]").length).toBe(1);
  });

  it("draws a live price line when a live print arrives", () => {
    render(<CandleChart bars={bars} status="ready" error="" livePrice="101.5" />);
    expect(document.querySelectorAll("[data-live-price]").length).toBe(1);
  });

  it("selects a bar by keyboard and mouse", () => {
    const onSelect = vi.fn();
    render(<CandleChart bars={bars} status="ready" error="" onSelectBarIndex={onSelect} />);
    const buttons = screen.getAllByRole("button", { name: /bar 2/i });
    fireEvent.click(buttons[0]);
    expect(onSelect).toHaveBeenCalledWith(2);
  });

  it("fails closed on invalid decimals", () => {
    const bad: HistoricalChartBar[] = [
      { bar_index: 1, open_time_us: 1, close_time_us: 2, open: "abc", high: "102", low: "99", close: "101", base_volume: "10" },
    ];
    render(<CandleChart bars={bad} status="ready" error="" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(document.querySelectorAll("[data-candle]").length).toBe(0);
  });

  it("shows loading and error states", () => {
    const { unmount } = render(<CandleChart bars={[]} status="loading" error="" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    unmount();
    render(<CandleChart bars={[]} status="error" error="kaput" />);
    expect(screen.getByRole("alert")).toHaveTextContent("kaput");
  });

  it("exposes an accessible text summary", () => {
    render(<CandleChart bars={bars} status="ready" error="" />);
    expect(screen.getByText(/3 bar/)).toBeInTheDocument();
  });
});

describe("LiveTickStrip", () => {
  it("plots live prints as ticks with last price", () => {
    render(<LiveTickStrip ticks={[{ price: "100" }, { price: "101.5" }, { price: "99" }]} label="Canlı baskılar" />);
    expect(screen.getByRole("img", { name: /3 baskı, son fiyat 99/ })).toBeInTheDocument();
    expect(document.querySelectorAll("[data-ticks]").length).toBe(1);
    expect(document.querySelectorAll("[data-live-dot]").length).toBe(1);
  });

  it("fails closed on invalid tick prices", () => {
    render(<LiveTickStrip ticks={[{ price: "zzz" }]} label="Canlı baskılar" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows an empty state without ticks", () => {
    render(<LiveTickStrip ticks={[]} label="Canlı baskılar" />);
    expect(screen.getByRole("status")).toHaveTextContent("Henüz baskı yok");
  });
});
