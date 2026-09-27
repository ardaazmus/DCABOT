import { useEffect, useRef } from "react";
import {
  createChart,
  createSeriesMarkers,
  CandlestickSeries,
  HistogramSeries,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type IPriceLine,
  type ISeriesMarkersPluginApi,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import type { HistoricalChartBar } from "./datasetCatalog";

export type ChartStatus = "idle" | "loading" | "ready" | "error";

/**
 * A horizontal price-line overlay. `price` is an exact Decimal string from
 * the backend (e.g. `preview.levels[i].price`, never recomputed client-side
 * -- per Arda's instruction, DCABOT's own exact math is the only source of
 * truth for these values; this component only converts to a plain number at
 * the render boundary, which lightweight-charts' API requires).
 */
export type ChartPriceLine = {
  id: string;
  price: string;
  color: string;
  title: string;
  lineStyle?: "solid" | "dashed";
  lineWidth?: 1 | 2 | 3 | 4;
};

export type ChartMarker = {
  barIndex: number;
  kind: "buy" | "sell" | "info";
  label?: string;
};

export type TradingChartProps = {
  bars: HistoricalChartBar[];
  status: ChartStatus;
  error: string;
  priceLines?: ChartPriceLine[];
  markers?: ChartMarker[];
  height?: number;
};

const MAX_BARS = 2000;

function toUnixSeconds(openTimeUs: number): UTCTimestamp {
  return Math.floor(openTimeUs / 1_000_000) as UTCTimestamp;
}

function toNumber(text: string): number {
  const value = Number(text);
  return Number.isFinite(value) ? value : 0;
}

/**
 * Real TradingView Lightweight Charts integration (Faz 16.1) -- replaces the
 * hand-rolled SVG candle renderer for any view that needs genuine chart
 * interaction (zoom/pan/crosshair) and price-line overlays. Consumes the
 * same `chart-data` bar contract as the rest of the app; draws no new
 * economic values, only positions already-exact backend numbers on a canvas.
 */
export function TradingChart({ bars, status, error, priceLines = [], markers = [], height = 360 }: TradingChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const priceLineHandlesRef = useRef<IPriceLine[]>([]);
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    // Canvas colors follow qwen's chart options verbatim (RG-QWEN-HTML
    // `baseChartOpts` + candle series): emerald up / rose down, ptitle-gray
    // text, 5%-alpha grid. Only the data contract is DCABOT's own.
    const chart = createChart(container, {
      autoSize: true,
      layout: { background: { color: "transparent" }, textColor: "#7d8ba3", fontFamily: '"JetBrains Mono", monospace', fontSize: 10 },
      grid: {
        vertLines: { color: "rgba(148,163,184,.05)" },
        horzLines: { color: "rgba(148,163,184,.05)" },
      },
      rightPriceScale: { borderColor: "rgba(148,163,184,.12)" },
      timeScale: { borderColor: "rgba(148,163,184,.12)", timeVisible: true },
      crosshair: { mode: 0 },
    });
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#34d399",
      downColor: "#fb7185",
      borderVisible: false,
      wickUpColor: "rgba(52,211,153,.9)",
      wickDownColor: "rgba(251,113,133,.9)",
    });
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    chartRef.current = chart;
    candleRef.current = candleSeries;
    volumeRef.current = volumeSeries;
    return () => {
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      priceLineHandlesRef.current = [];
      markersPluginRef.current = null;
    };
  }, []);

  useEffect(() => {
    const candleSeries = candleRef.current;
    const volumeSeries = volumeRef.current;
    if (!candleSeries || !volumeSeries) return;
    if (status !== "ready" || bars.length === 0) {
      candleSeries.setData([]);
      volumeSeries.setData([]);
      return;
    }
    const sliced = bars.length > MAX_BARS ? bars.slice(bars.length - MAX_BARS) : bars;
    // lightweight-charts requires strictly-ascending time per point; sub-minute
    // intervals could in principle collide at 1-second resolution. Drop any
    // bar that wouldn't strictly advance rather than let the library throw
    // and take the whole chart down.
    let lastSeconds = -Infinity;
    const windowed = sliced.filter((bar) => {
      const seconds = toUnixSeconds(bar.open_time_us);
      if (seconds <= lastSeconds) return false;
      lastSeconds = seconds;
      return true;
    });
    candleSeries.setData(
      windowed.map((bar) => ({
        time: toUnixSeconds(bar.open_time_us),
        open: toNumber(bar.open),
        high: toNumber(bar.high),
        low: toNumber(bar.low),
        close: toNumber(bar.close),
      })),
    );
    volumeSeries.setData(
      windowed.map((bar) => ({
        time: toUnixSeconds(bar.open_time_us),
        value: toNumber(bar.base_volume),
        color: toNumber(bar.close) >= toNumber(bar.open) ? "rgba(52,211,153,.5)" : "rgba(251,113,133,.5)",
      })),
    );
    const markerByBarIndex = new Map(markers.map((marker) => [marker.barIndex, marker]));
    const seriesMarkers = windowed
      .map((bar, index) => {
        const marker = markerByBarIndex.get(bar.bar_index);
        if (!marker) return null;
        return {
          time: toUnixSeconds(bar.open_time_us),
          position: marker.kind === "sell" ? ("aboveBar" as const) : ("belowBar" as const),
          color: marker.kind === "sell" ? "#fb7185" : marker.kind === "buy" ? "#34d399" : "#7d8ba3",
          shape: marker.kind === "sell" ? ("arrowDown" as const) : marker.kind === "buy" ? ("arrowUp" as const) : ("circle" as const),
          text: marker.label,
        };
      })
      .filter((value): value is NonNullable<typeof value> => value !== null);
    const plugin = markersPluginRef.current ?? createSeriesMarkers(candleSeries, []);
    markersPluginRef.current = plugin;
    plugin.setMarkers(seriesMarkers);
    chartRef.current?.timeScale().fitContent();
  }, [bars, status, markers]);

  useEffect(() => {
    const candleSeries = candleRef.current;
    if (!candleSeries) return;
    for (const handle of priceLineHandlesRef.current) candleSeries.removePriceLine(handle);
    priceLineHandlesRef.current = priceLines.map((line) =>
      candleSeries.createPriceLine({
        price: toNumber(line.price),
        color: line.color,
        lineWidth: line.lineWidth ?? 1,
        lineStyle: line.lineStyle === "dashed" ? LineStyle.Dashed : LineStyle.Solid,
        axisLabelVisible: true,
        title: line.title,
      }),
    );
  }, [priceLines]);

  if (status === "error") {
    return <div className="empty-state error" role="alert">{error || "Grafik yüklenemedi."}</div>;
  }
  if (status === "idle" || bars.length === 0) {
    return <div className="empty-state" role="status">Grafik için veri seçilmedi.</div>;
  }

  return <div ref={containerRef} className="trading-chart" style={{ width: "100%", height }} role="img" aria-label={`TradingView grafiği: ${bars.length} bar.`} />;
}
