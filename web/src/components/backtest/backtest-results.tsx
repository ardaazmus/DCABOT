"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo } from "react";

import { AssumptionsNote } from "@/components/backtest/assumptions-note";
import { BacktestPriceChart } from "@/components/backtest/backtest-price-chart";
import { DealTable } from "@/components/backtest/deal-table";
import { KpiGrid } from "@/components/backtest/kpi-grid";
import { MonthlyBars } from "@/components/backtest/monthly-bars";
import { OpenDealCard } from "@/components/backtest/open-deal-card";
import { SoUsageBars } from "@/components/backtest/so-usage-bars";
import { StatusBand } from "@/components/backtest/status-band";
import { TimeAreaChart } from "@/components/backtest/time-area-chart";
import { ChartCard } from "@/components/chart-card";
import { EmptyState } from "@/components/empty-state";
import type { BacktestResult } from "@/lib/api/schemas";
import { backtestDealMarkers } from "@/lib/chart/deal-markers";
import { textCurveToSamples } from "@/lib/chart/downsample";
import { readPalette } from "@/lib/chart/theme";

/**
 * Backtest sonucu: bant, KPI, grafikler, tablolar, varsayımlar.
 * Bileşen salt gösterir; köprü URL parametresiyle kurulur.
 */
export function BacktestResults({
  result,
  setupHref,
}: {
  result: BacktestResult;
  setupHref: string;
}) {
  const t = useTranslations("backtest");
  const equity = useMemo(
    () => textCurveToSamples(result.equity_curve, (p) => p.time_us, (p) => p.equity),
    [result],
  );
  const drawdown = useMemo(
    () =>
      textCurveToSamples(result.drawdown_curve, (p) => p.time_us, (p) => p.drawdown_percent, {
        negate: true,
      }),
    [result],
  );
  const price = useMemo(
    () => textCurveToSamples(result.price_curve, (p) => p.time_us, (p) => p.close),
    [result],
  );
  const tradeMarkers = useMemo(() => {
    const palette = readPalette();
    const candleTimes = new Set(price.map((point) => point.time));
    return backtestDealMarkers(result.deals, candleTimes, {
      profit: palette.profit,
      loss: palette.loss,
    });
  }, [result, price]);
  return (
    <div className="flex flex-col gap-4" data-testid="backtest-results">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <StatusBand result={result} />
        <Link
          href={setupHref}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90"
        >
          {t("setupBot")}
        </Link>
      </div>
      <KpiGrid result={result} />
      <ChartCard title={t("equityTitle")} state={equity.length === 0 ? "empty" : "ready"}>
        <TimeAreaChart
          points={equity}
          baselineText={result.budget}
          line="accent"
          label={t("equityTitle")}
          testId="equity-chart"
        />
      </ChartCard>
      <ChartCard title={t("tradesTitle")} state={price.length === 0 ? "empty" : "ready"}>
        <BacktestPriceChart
          points={price}
          markers={tradeMarkers}
          label={t("tradesTitle")}
          testId="trades-chart"
        />
      </ChartCard>
      <ChartCard title={t("drawdownTitle")} state={drawdown.length === 0 ? "empty" : "ready"}>
        <TimeAreaChart
          points={drawdown}
          line="loss"
          label={t("drawdownTitle")}
          testId="drawdown-chart"
        />
      </ChartCard>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <MonthlyBars rows={result.monthly_returns} />
        <SoUsageBars rows={result.safety_order_usage} />
      </div>
      <div className="flex flex-col gap-2">
        <h2 className="text-base font-semibold">{t("dealsTitle")}</h2>
        {result.deals.length === 0 ? (
          <EmptyState title={t("waitingResults")} />
        ) : (
          <DealTable deals={result.deals} />
        )}
      </div>
      <OpenDealCard openDeal={result.open_deal} />
      <AssumptionsNote assumptions={result.assumptions} />
    </div>
  );
}
