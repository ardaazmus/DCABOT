"use client";

import {
  AreaSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
} from "lightweight-charts";
import { useLocale } from "next-intl";
import { useTheme } from "next-themes";
import { useEffect, useMemo, useRef } from "react";

import { downsampleMinMax, textToNumber, type SamplePoint } from "@/lib/chart/downsample";
import {
  baseChartOptions,
  createDayTickFormatter,
  readPalette,
  withAlpha,
  type ChartPalette,
} from "@/lib/chart/theme";

const MAX_CHART_POINTS = 2000;

function TimeAreaChartInner({
  points,
  baseline,
  line,
  height,
  label,
  testId,
}: {
  points: SamplePoint[];
  baseline: SamplePoint[];
  line: keyof ChartPalette;
  height: number;
  label: string;
  testId: string;
}) {
  const locale = useLocale();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const areaRef = useRef<ISeriesApi<"Area"> | null>(null);
  const baseRef = useRef<ISeriesApi<"Line"> | null>(null);

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
    areaRef.current = chart.addSeries(AreaSeries, {
      lineColor: palette[line],
      topColor: withAlpha(palette[line], 0.25),
      bottomColor: withAlpha(palette[line], 0),
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });
    areaRef.current.setData(points);
    if (baseline.length > 0) {
      baseRef.current = chart.addSeries(LineSeries, {
        color: palette.muted,
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      baseRef.current.setData(baseline);
    }
    const resize = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      if (width > 0) chart.applyOptions({ width });
    });
    resize.observe(element);
    return () => {
      resize.disconnect();
      chart.remove();
      chartRef.current = null;
      areaRef.current = null;
      baseRef.current = null;
    };
    // Grafik tema/dil değişiminde dış anahtarla yeniden kurulur.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    areaRef.current?.setData(points);
    baseRef.current?.setData(baseline);
    // Etiket durumu veri değişince sıfırlanır.
    chartRef.current?.applyOptions({
      timeScale: { tickMarkFormatter: createDayTickFormatter() },
    });
  }, [points, baseline]);

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
 * Zaman serisi alan grafiği (equity, drawdown). 2000 noktayı aşan
 * seriler min/maks koruyarak seyreltilir (yalnız görüntü).
 */
export function TimeAreaChart(props: {
  points: SamplePoint[];
  /** Yatay başvuru çizgisi metni (başlangıç bütçesi). */
  baselineText?: string | null;
  line: keyof ChartPalette;
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
  const baseline = useMemo<SamplePoint[]>(() => {
    const value = textToNumber(props.baselineText ?? null);
    if (value === null || points.length < 2) return [];
    const first = points[0];
    const last = points[points.length - 1];
    if (first === undefined || last === undefined) return [];
    return [
      { time: first.time, value },
      { time: last.time, value },
    ];
  }, [props.baselineText, points]);
  return (
    <TimeAreaChartInner
      key={`${resolvedTheme ?? "dark"}-${locale}`}
      points={points}
      baseline={baseline}
      line={props.line}
      height={props.height ?? 240}
      label={props.label}
      testId={props.testId}
    />
  );
}
