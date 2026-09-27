"use client";

import {
  CandlestickSeries,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type LineData,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import { useLocale } from "next-intl";
import { useTheme } from "next-themes";
import { useEffect, useRef } from "react";

import { baseChartOptions, readPalette } from "@/lib/chart/theme";
import type { Candle } from "@/lib/chart/klines";

export type ChartOverlay = {
  id: string;
  /** Token anahtarı, örn. "entry". */
  color: "profit" | "loss" | "safety" | "entry" | "accent";
  dashed?: boolean;
  dotted?: boolean;
  segments: LineData<Time>[][];
};

function PriceChartInner({
  candles,
  overlays,
  markers,
  height,
  label,
  testId,
}: {
  candles: Candle[];
  overlays: ChartOverlay[];
  markers: SeriesMarker<Time>[];
  height: number;
  label: string;
  testId: string;
}) {
  const locale = useLocale();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const overlayRefs = useRef<ISeriesApi<"Line">[]>([]);

  useEffect(() => {
    const element = containerRef.current;
    if (element === null) return;
    const palette = readPalette();
    const chart = createChart(element, {
      ...baseChartOptions(height, palette, locale),
      width: element.clientWidth,
    });
    chartRef.current = chart;
    candleRef.current = chart.addSeries(CandlestickSeries, {
      upColor: palette.profit,
      downColor: palette.loss,
      wickUpColor: palette.profit,
      wickDownColor: palette.loss,
      borderVisible: false,
    });
    candleRef.current.setData(candles);
    const resize = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      if (width > 0) chart.applyOptions({ width });
    });
    resize.observe(element);
    return () => {
      resize.disconnect();
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      markersRef.current = null;
      overlayRefs.current = [];
    };
    // Grafiğin kendisi tema/dil değişiminde dış anahtarla yeniden kurulur.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    candleRef.current?.setData(candles);
  }, [candles]);

  useEffect(() => {
    const series = candleRef.current;
    if (series === null) return;
    if (markersRef.current === null) {
      markersRef.current = createSeriesMarkers(series, markers);
    } else {
      markersRef.current.setMarkers(markers);
    }
  }, [markers, candles]);

  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null) return;
    const palette = readPalette();
    for (const series of overlayRefs.current) chart.removeSeries(series);
    overlayRefs.current = overlays.flatMap((overlay) =>
      overlay.segments.map((segment) => {
        const series = chart.addSeries(LineSeries, {
          color: palette[overlay.color],
          lineWidth: 1,
          lineStyle: overlay.dotted
            ? LineStyle.Dotted
            : overlay.dashed
              ? LineStyle.Dashed
              : LineStyle.Solid,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        series.setData(segment);
        return series;
      }),
    );
  }, [overlays]);

  return (
    <div
      ref={containerRef}
      role="img"
      aria-label={label}
      data-testid={testId}
      style={{ height }}
      className="w-full"
    />
  );
}

/** Mum grafiği + ana grafik indikatör katmanları + dolum işaretleri. */
export function PriceChart(props: {
  candles: Candle[];
  overlays: ChartOverlay[];
  markers?: SeriesMarker<Time>[];
  height?: number;
  label: string;
  testId?: string;
}) {
  const { resolvedTheme } = useTheme();
  const locale = useLocale();
  return (
    <PriceChartInner
      key={`${resolvedTheme ?? "dark"}-${locale}`}
      candles={props.candles}
      overlays={props.overlays}
      markers={props.markers ?? []}
      height={props.height ?? 360}
      label={props.label}
      testId={props.testId ?? "price-chart"}
    />
  );
}
