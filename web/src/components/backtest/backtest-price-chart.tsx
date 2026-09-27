"use client";

import {
  LineSeries,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import { useLocale } from "next-intl";
import { useTheme } from "next-themes";
import { useEffect, useMemo, useRef } from "react";

import { downsampleMinMax, type SamplePoint } from "@/lib/chart/downsample";
import {
  baseChartOptions,
  createDayTickFormatter,
  readPalette,
} from "@/lib/chart/theme";

const MAX_CHART_POINTS = 2000;

function BacktestPriceChartInner({
  points,
  markers,
  height,
  label,
  testId,
}: {
  points: SamplePoint[];
  markers: SeriesMarker<Time>[];
  height: number;
  label: string;
  testId: string;
}) {
  const locale = useLocale();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (element === null) return;
    const palette = readPalette();
    const chart = createChart(element, {
      ...baseChartOptions(height, palette, locale),
      width: element.clientWidth,
      timeScale: { tickMarkFormatter: createDayTickFormatter() },
    });
    chartRef.current = chart;
    lineRef.current = chart.addSeries(LineSeries, {
      color: palette.accent,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    lineRef.current.setData(points);
    const resize = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      if (width > 0) chart.applyOptions({ width });
    });
    resize.observe(element);
    return () => {
      resize.disconnect();
      chart.remove();
      chartRef.current = null;
      lineRef.current = null;
      markersRef.current = null;
    };
    // Grafik tema/dil değişiminde dış anahtarla yeniden kurulur.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    lineRef.current?.setData(points);
    const series = lineRef.current;
    if (series === null) return;
    if (markersRef.current === null) {
      markersRef.current = createSeriesMarkers(series, markers);
    } else {
      markersRef.current.setMarkers(markers);
    }
    chartRef.current?.applyOptions({
      timeScale: { tickMarkFormatter: createDayTickFormatter() },
    });
  }, [points, markers]);

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

/**
 * Backtest fiyat + işlem grafiği: koşulan barların kapanış çizgisi
 * üstünde deal giriş/çıkış işaretleri (giriş altta yeşil, çıkış
 * üstte; kârlı çıkış yeşil, diğer kırmızı). İşaretler zaman
 * eksenine basılır; çizgi seyrelse bile kaybolmaz.
 */
export function BacktestPriceChart(props: {
  points: SamplePoint[];
  markers: SeriesMarker<Time>[];
  height?: number;
  label: string;
  testId: string;
}) {
  const { resolvedTheme } = useTheme();
  const locale = useLocale();
  const points = useMemo(
    () => downsampleMinMax(props.points, MAX_CHART_POINTS),
    [props.points],
  );
  return (
    <BacktestPriceChartInner
      key={`${resolvedTheme ?? "dark"}-${locale}`}
      points={points}
      markers={props.markers}
      height={props.height ?? 240}
      label={props.label}
      testId={props.testId}
    />
  );
}
