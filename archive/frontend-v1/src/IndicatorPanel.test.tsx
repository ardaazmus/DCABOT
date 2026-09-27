import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  INDICATOR_ROUTES,
  IndicatorPanel,
  indicatorRequestBody,
  isBollingerResponse,
  isIndicatorResponse,
  isIndicatorSeries,
  isMacdResponse,
  isStochRsiResponse,
  type IndicatorSeries,
} from "./IndicatorPanel";

const series: IndicatorSeries = {
  kind: "sma",
  points: [
    { index: 19, value: "97000", exact: true },
    { index: 20, value: "97100.5", exact: true },
  ],
};

describe("IndicatorPanel", () => {
  it("AA.2c: son değeri + kesinlik rozetini gösterir", () => {
    render(<IndicatorPanel kind="sma" series={series} status="ready" error="" barCount={21} onSelect={vi.fn()} onRetry={vi.fn()} />);
    expect(screen.getByText("97100.5")).toBeInTheDocument();
    expect(screen.getByText("#20")).toBeInTheDocument();
    expect(screen.getByText("EXACT")).toBeInTheDocument();
    expect(screen.getByText("21 bar")).toBeInTheDocument();
  });

  it("AA.2c: çip seçimi + boş-veri + hata", () => {
    const onSelect = vi.fn();
    const { unmount } = render(<IndicatorPanel kind="sma" series={null} status="idle" error="" barCount={0} onSelect={onSelect} onRetry={vi.fn()} />);
    expect(screen.getByText("Hesaplanacak grafik verisi yok — veri kataloğundan bir dataset grafiği yükleyin.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "EMA 50" }));
    expect(onSelect).toHaveBeenCalledWith("ema");
    unmount();
    render(<IndicatorPanel kind="ema" series={null} status="error" error="uç 422" barCount={21} onSelect={vi.fn()} onRetry={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent("uç 422");
  });

  it("AA.2c: guard sözleşmesi", () => {
    expect(isIndicatorSeries(series)).toBe(true);
    expect(isIndicatorSeries({ points: [{ index: 1, value: "1" }] })).toBe(false);
    expect(isIndicatorResponse({ data: series })).toBe(true);
    expect(isIndicatorResponse({ data: { points: [] } })).toBe(true);
    expect(isIndicatorResponse({})).toBe(false);
  });

  it("AA.2d: 3 yeni uç guard + rota + kanonik gövde", () => {
    expect(isMacdResponse({ data: { points: [{ index: 0, macd: "1", signal: null, histogram: "0.5" }] } })).toBe(true);
    expect(isMacdResponse({ data: { points: [{ index: 0, macd: 1 }] } })).toBe(false);
    expect(isStochRsiResponse({ data: { points: [{ index: 0, rsi: "70", stoch_rsi: null }] } })).toBe(true);
    expect(isStochRsiResponse({ data: {} })).toBe(false);
    expect(isBollingerResponse({ data: { points: [{ index: 0, middle: "100", middle_exact: true, variance: "4", variance_exact: true, upper: "104", lower: "96", percent_b: "0.75" }] } })).toBe(true);
    expect(isBollingerResponse({ data: { points: [{ index: 0, middle: "100" }] } })).toBe(false);
    expect(INDICATOR_ROUTES).toEqual({ sma: "sma", ema: "ema", macd: "macd", stoch_rsi: "stoch-rsi", bollinger: "bollinger" });
    expect(indicatorRequestBody("macd", ["1", "2"])).toEqual({ closes: ["1", "2"], fast: 3, slow: 6, signal: 3, scale: 8 });
    expect(indicatorRequestBody("stoch_rsi", ["1", "2"])).toEqual({ closes: ["1", "2"], rsi_window: 5, stoch_window: 5, scale: 8 });
    expect(indicatorRequestBody("bollinger", ["1", "2"])).toEqual({ closes: ["1", "2"], window: 3, num_std: "2" });
  });

  it("AA.2d: 5 çip + türe-göre son-değer + grafik", () => {
    const onSelect = vi.fn();
    render(<IndicatorPanel kind="macd" series={{ kind: "macd", points: [{ index: 9, macd: "1.5", signal: "1.2", histogram: null }] }} status="ready" error="" barCount={10} onSelect={onSelect} onRetry={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "StochRSI 5/5" }));
    expect(onSelect).toHaveBeenCalledWith("stoch_rsi");
    fireEvent.click(screen.getByRole("button", { name: "BB 3·2σ" }));
    expect(onSelect).toHaveBeenCalledWith("bollinger");
    expect(screen.getByText("1.5")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /İndikatör grafiği: 3 çizgi/ })).toBeInTheDocument();
  });
});
