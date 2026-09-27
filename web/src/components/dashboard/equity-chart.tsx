"use client";

import { useTranslations } from "next-intl";

import { TimeAreaChart } from "@/components/backtest/time-area-chart";
import { ChartCard } from "@/components/chart-card";
import type { EquityRange } from "@/lib/api/queries";
import type { EquityPoint } from "@/lib/api/schemas";
import { textCurveToSamples } from "@/lib/chart/downsample";

const RANGES: readonly EquityRange[] = ["7d", "30d", "all"];

/**
 * Portföy özsermaye alanı. Noktalar saatlik anlık görüntülerdir;
 * başvuru çizgisi bağlı sermayedir (neyle başlandığı).
 */
export function EquityChart({
  points,
  range,
  onRange,
  baseline,
}: {
  points: readonly EquityPoint[];
  range: EquityRange;
  onRange: (range: EquityRange) => void;
  baseline: string | null;
}) {
  const t = useTranslations("dashboard");
  return (
    <ChartCard
      title={t("equityTitle")}
      ranges={RANGES.map((id) => ({ id, label: t(`range${id}`) }))}
      activeRange={range}
      onRangeChange={(id) => onRange(id as EquityRange)}
      state={points.length === 0 ? "empty" : "ready"}
      empty={t("equityEmpty")}
    >
      <TimeAreaChart
        points={textCurveToSamples(points, (point) => point.time_us, (point) => point.equity)}
        baselineText={baseline}
        line="accent"
        label={t("equityTitle")}
        testId="dashboard-equity"
      />
    </ChartCard>
  );
}
