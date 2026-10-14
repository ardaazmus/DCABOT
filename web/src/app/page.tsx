"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";

import { BotCorrelation } from "@/components/dashboard/correlation-matrix";
import { DailyBars } from "@/components/dashboard/daily-bars";
import { EquityChart } from "@/components/dashboard/equity-chart";
import { EventsFeed } from "@/components/dashboard/events-feed";
import { KpiGrid } from "@/components/dashboard/kpi-grid";
import { ProfitSplits } from "@/components/dashboard/profit-splits";
import { DealsTable } from "@/components/deals/deals-table";
import { Skeleton } from "@/components/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useBots,
  useDailyProfit,
  useDeals,
  useEvents,
  usePortfolioEquity,
  usePortfolioSummary,
  useProfitByBot,
  useProfitByPair,
  type EquityRange,
} from "@/lib/api/queries";

export default function Home() {
  const t = useTranslations("dashboard");
  const nav = useTranslations("nav");
  const bots = useBots();
  const summary = usePortfolioSummary();
  const [range, setRange] = useState<EquityRange>("30d");
  const equity = usePortfolioEquity(range);
  const daily = useDailyProfit(30);
  const byBot = useProfitByBot();
  const byPair = useProfitByPair();
  const deals = useDeals("active");
  const events = useEvents(10);

  if (bots.isPending) {
    return (
      <div className="flex flex-col gap-4" role="status" aria-label={t("loading")}>
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (bots.isError) {
    return (
      <p role="alert" className="text-sm text-loss">
        {t("loadError")}
      </p>
    );
  }
  if (bots.data.data.length === 0) {
    return (
      <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">{nav("dashboard")}</h1>
      <Card data-testid="dashboard-empty">
        <CardHeader>
          <CardTitle>{t("emptyTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-start gap-3">
          <p className="text-sm text-muted-foreground">{t("emptyHint")}</p>
          <div className="flex gap-2">
            <Link
              href="/bots/new"
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90"
            >
              {t("createBot")}
            </Link>
            <Link
              href="/backtest"
              className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              {t("backtestFirst")}
            </Link>
          </div>
        </CardContent>
      </Card>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">{nav("dashboard")}</h1>
      {summary.isPending ? (
        <Skeleton className="h-28 w-full" data-testid="dashboard-kpis-loading" />
      ) : summary.isError ? (
        <p role="alert" className="text-sm text-loss">
          {t("loadError")}
        </p>
      ) : (
        <KpiGrid summary={summary.data.data} />
      )}
      <div className="grid gap-4 xl:grid-cols-2">
        {equity.isPending ? (
          <Skeleton className="h-64 w-full" />
        ) : equity.isError ? (
          <p role="alert" className="text-sm text-loss">
            {t("loadError")}
          </p>
        ) : (
          <EquityChart
            points={equity.data.data}
            range={range}
            onRange={setRange}
            baseline={summary.data?.data.deployed_capital ?? null}
          />
        )}
        {daily.isPending ? (
          <Skeleton className="h-64 w-full" />
        ) : daily.isError ? null : (
          <DailyBars rows={daily.data.data} />
        )}
      </div>
      {byBot.isPending || byPair.isPending ? (
        <Skeleton className="h-48 w-full" />
      ) : byBot.isError || byPair.isError ? null : (
        <ProfitSplits byBot={byBot.data.data} byPair={byPair.data.data} />
      )}
      <BotCorrelation />
      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{t("activeDealsTitle")}</h2>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {deals.isPending ? (
            <Skeleton className="h-32 w-full" />
          ) : deals.isError ? null : (
            <DealsTable rows={deals.data.data} mode="active" testId="dashboard-deals" />
          )}
        </CardContent>
      </Card>
      {events.isPending || events.isError ? null : <EventsFeed events={events.data.data.events} />}
    </div>
  );
}
