"use client";

import { useMemo } from "react";

import { TimeAreaChart } from "@/components/backtest/time-area-chart";
import { ChartCard } from "@/components/chart-card";
import type { BotDeal } from "@/lib/api/schemas";
import { textCurveToSamples } from "@/lib/chart/downsample";

/**
 * Kümülatif kâr eğrisi (x: kapanış, y: kümülatif). Açık deal'ler
 * (kapanışsız) grafiğe girmez; metin→sayı dönüşümü lib/chart içindedir.
 */
export function CumulativeProfitChart({
  deals,
  title,
  empty,
}: {
  deals: readonly BotDeal[];
  title: string;
  empty: string;
}) {
  const points = useMemo(
    () =>
      textCurveToSamples(
        deals.filter((deal) => deal.closed_at_us !== null),
        (deal) => deal.closed_at_us as number,
        (deal) => deal.cumulative_profit,
      ),
    [deals],
  );
  if (points.length === 0) {
    return <ChartCard title={title} state="empty" empty={<span>{empty}</span>} />;
  }
  return (
    <ChartCard title={title}>
      <TimeAreaChart points={points} line="profit" label={title} testId="cumulative-chart" />
    </ChartCard>
  );
}
