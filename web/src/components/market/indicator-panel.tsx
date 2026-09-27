"use client";

import {
  HistogramSeries,
  LineSeries,
  createChart,
  type HistogramData,
  type IChartApi,
  type LineData,
  type Time,
} from "lightweight-charts";
import { useLocale } from "next-intl";
import { useTheme } from "next-themes";
import { useEffect, useRef } from "react";

import { baseChartOptions, readPalette } from "@/lib/chart/theme";

export type PanelLine = {
  id: string;
  color: "profit" | "loss" | "safety" | "entry" | "accent" | "muted";
  segments: LineData<Time>[][];
};

function PanelInner({
  lines,
  histogram,
  height,
  label,
  testId,
}: {
  lines: PanelLine[];
  histogram?: HistogramData<Time>[];
  height: number;
  label: string;
  testId: string;
}) {
  const locale = useLocale();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (element === null) return;
    const palette = readPalette();
    const chart: IChartApi = createChart(element, {
      ...baseChartOptions(height, palette, locale),
      width: element.clientWidth,
    });
    if (histogram !== undefined) {
      const bars = chart.addSeries(HistogramSeries, {
        priceLineVisible: false,
        lastValueVisible: false,
      });
      bars.setData(histogram);
    }
    for (const line of lines) {
      for (const segment of line.segments) {
        const series = chart.addSeries(LineSeries, {
          color: palette[line.color],
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        series.setData(segment);
      }
    }
    const resize = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      if (width > 0) chart.applyOptions({ width });
    });
    resize.observe(element);
    return () => {
      resize.disconnect();
      chart.remove();
    };
    // Panel verisi değişiminde dış anahtar yeniden kurar (seyrek değişir).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

/** MACD / StochRSI alt paneli. Veri kimliği değişince yeniden kurulur. */
export function IndicatorPanel(props: {
  lines: PanelLine[];
  histogram?: HistogramData<Time>[];
  height?: number;
  label: string;
  testId: string;
  /** Veri değiştikçe değişmesi beklenen kimlik (örn. mum aralığı + sayısı). */
  dataKey: string;
}) {
  const { resolvedTheme } = useTheme();
  const locale = useLocale();
  return (
    <PanelInner
      key={`${resolvedTheme ?? "dark"}-${locale}-${props.dataKey}`}
      lines={props.lines}
      histogram={props.histogram}
      height={props.height ?? 180}
      label={props.label}
      testId={props.testId}
    />
  );
}
