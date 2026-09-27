"use client";

import { useLocale, useTranslations } from "next-intl";
import { use, useMemo, type ReactNode } from "react";

import { ActiveDealCard } from "@/components/bots/active-deal-card";
import { BotActions } from "@/components/bots/bot-actions";
import { BotCopyButton } from "@/components/bots/bot-copy-button";
import { BotDealsTable } from "@/components/bots/bot-deals-table";
import { BotKpis } from "@/components/bots/bot-kpis";
import { BotStatusHint } from "@/components/bots/bot-status-hint";
import { BotTabs } from "@/components/bots/bot-tabs";
import { CumulativeProfitChart } from "@/components/bots/cumulative-profit-chart";
import { EventsTimeline } from "@/components/bots/events-timeline";
import { PreviewPanel } from "@/components/bots/preview-panel";
import { ReplayForm } from "@/components/bots/replay-form";
import { SoHistogram } from "@/components/bots/so-histogram";
import { WinLossRing } from "@/components/bots/win-loss-ring";
import { EmptyState } from "@/components/empty-state";
import { EnumValue } from "@/components/enum-value";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge, type StatusBadgeVariant } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiHttpError } from "@/lib/api/client";
import { useBot, useBotDeals, useBotPreview, useBotStats, type BotPreviewBody } from "@/lib/api/queries";
import { isGridStrategy, type DcaStrategy } from "@/lib/api/schemas";
import { GridBotDetail } from "@/components/bots/grid-bot-detail";
import { formatDecimal, isDecimalString } from "@/lib/decimal";

const STATUS_VARIANT: Record<string, StatusBadgeVariant> = {
  RUNNING: "running",
  PAUSED: "paused",
  STOPPED: "stopped",
  ERROR: "error",
};

const MODE_VARIANT: Record<string, StatusBadgeVariant> = {
  PAPER: "paper",
  TESTNET: "testnet",
};

/** Kayıtlı yüzde metni; Pnl ile aynı `%değer` geleneği, yerele göre biçimli. */
function Pct({ value, locale }: { value: string; locale: "tr" | "en" }) {
  const text = isDecimalString(value)
    ? formatDecimal(value, { locale })
    : value;
  return <span className="font-mono">%{text}</span>;
}

/** Kayıtlı çarpan metni, yerele göre biçimli ("1,5"). */
function Num({ value, locale }: { value: string; locale: "tr" | "en" }) {
  const text = isDecimalString(value) ? formatDecimal(value, { locale }) : value;
  return <span className="font-mono">{text}</span>;
}

function StrategyRows({ strategy, locale }: { strategy: DcaStrategy; locale: "tr" | "en" }) {
  const t = useTranslations("wizard");
  const symbols = strategy.symbols !== null && strategy.symbols.length > 1 ? strategy.symbols : null;
  const rows: [string, ReactNode][] = [
    [
      symbols === null ? t("symbolLabel") : t("symbolsLabel"),
      <span key="s" className="font-mono">{symbols === null ? strategy.symbol : symbols.join(", ")}</span>,
    ],
    [t("directionLabel"), strategy.direction === "LONG" ? t("directionLong") : t("directionShort")],
    [t("marketLabel"), strategy.market_type === "FUTURES" ? t("marketFutures") : t("marketSpot")],
    [t("leverage"), strategy.leverage === null ? "—" : `${strategy.leverage}x`],
    [t("cooldown"), String(strategy.cooldown_seconds)],
    [t("minPrice"), strategy.min_price === null ? "—" : `${strategy.min_price} USDT`],
    [t("maxPrice"), strategy.max_price === null ? "—" : `${strategy.max_price} USDT`],
    [t("baseOrder"), `${strategy.base_order} USDT`],
    [t("safetyOrder"), `${strategy.safety_order} USDT`],
    [t("maxSafetyOrders"), String(strategy.max_safety_orders)],
    [
      t("maxActiveSafetyOrders"),
      strategy.max_active_safety_orders === null
        ? t("maxActivePlaceholder")
        : String(strategy.max_active_safety_orders),
    ],
    [
      t("maxActiveDeals"),
      strategy.max_active_deals === null
        ? t("maxActiveDealsPlaceholder")
        : String(strategy.max_active_deals),
    ],
    [t("priceDeviation"), <Pct key="d" value={strategy.price_deviation} locale={locale} />],
    [t("volumeScale"), <Num key="v" value={strategy.safety_order_volume_scale} locale={locale} />],
    [t("stepScale"), <Num key="s" value={strategy.safety_order_step_scale} locale={locale} />],
    [t("takeProfit"), <Pct key="p" value={strategy.take_profit} locale={locale} />],
    [
      t("comboTakeProfit"),
      strategy.combined_take_profit === null ? (
        "—"
      ) : (
        <Pct key="c" value={strategy.combined_take_profit} locale={locale} />
      ),
    ],
    [
      t("trailingTakeProfit"),
      strategy.trailing_take_profit === null ? (
        "—"
      ) : (
        <Pct key="t" value={strategy.trailing_take_profit} locale={locale} />
      ),
    ],
    [
      t("stopLoss"),
      strategy.stop_loss === null ? (
        "—"
      ) : (
        <Pct key="s" value={strategy.stop_loss} locale={locale} />
      ),
    ],
  ];
  return (
    <dl className="flex flex-col gap-2 text-sm">
      {rows.map(([label, value]) => (
        <div key={label} className="flex justify-between gap-4">
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="font-mono">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function BotDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("bots");
  const locale = useLocale() === "en" ? "en" : "tr";
  const bot = useBot(id);

  const previewBody: BotPreviewBody | null = useMemo(() => {
    const data = bot.data?.data;
    if (data === undefined || isGridStrategy(data.strategy)) return null;
    return { budget: data.budget, strategy: data.strategy };
  }, [bot.data]);
  const preview = useBotPreview(previewBody);
  const plan = preview.data?.data ?? null;
  const stats = useBotStats(id, bot.data?.data.status);
  const deals = useBotDeals(id, bot.data?.data.status);

  if (bot.isPending) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2">
        <p role="status" className="text-sm text-muted-foreground">
          …
        </p>
      </div>
    );
  }

  const data = bot.data?.data;
  if (bot.isError || data === undefined) {
    const notFound =
      bot.error instanceof ApiHttpError && bot.error.status === 404;
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t("notFound")}</h1>
        <EmptyState
          title={t("notFound")}
          description={notFound ? t("notFoundHint") : t("loadError")}
          actionLabel={t("backToBots")}
          actionHref="/bots"
        />
      </div>
    );
  }

  if (isGridStrategy(data.strategy)) {
    return <GridBotDetail bot={data} />;
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{data.name}</h1>
            <span className="font-mono text-lg text-muted-foreground">{data.symbol}</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge variant={STATUS_VARIANT[data.status] ?? "stopped"}>
              <EnumValue code={data.status} />
            </StatusBadge>
            <StatusBadge variant={MODE_VARIANT[data.mode] ?? "paper"}>
              <EnumValue code={data.mode} />
            </StatusBadge>
            {data.archived ? (
              <StatusBadge variant="stopped">{t("archivedBadge")}</StatusBadge>
            ) : null}
          </div>
          <BotStatusHint status={data.status} reason={data.status_reason} />
        </div>
        <div className="flex flex-wrap items-start gap-2">
          <BotCopyButton botId={id} disabled={data.archived} />
          <BotActions bot={data} />
        </div>
      </div>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>
              <h2>{t("strategyTitle")}</h2>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <StrategyRows strategy={data.strategy} locale={locale} />
          </CardContent>
        </Card>

        <PreviewPanel
          symbol={data.symbol}
          plan={plan}
          budget={data.budget}
          state={
            preview.isPending
              ? "loading"
              : preview.isError
                ? "error"
                : "ready"
          }
          errorText={preview.error instanceof Error ? preview.error.message : undefined}
          title={t("planTitle")}
          note={t("planNote")}
          comboTakeProfit={data.strategy.combined_take_profit}
        />
      </div>

      {stats.isPending || deals.isPending ? (
        <div className="flex flex-col gap-2" role="status">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : stats.isError || deals.isError || stats.data === undefined || deals.data === undefined ? (
        <p role="alert" className="text-sm text-loss">
          {t("loadError")}
        </p>
      ) : (
        <>
          {data.mode === "PAPER" && data.status === "STOPPED" && !data.archived ? (
            <ReplayForm botId={id} />
          ) : null}
          <BotTabs
            tabs={[
            {
              id: "overview",
              label: t("tabOverview"),
              panel: (
                <div className="flex flex-col gap-4">
                  <BotKpis stats={stats.data.data} />
                  <CumulativeProfitChart
                    deals={deals.data.data}
                    title={t("cumulativeTitle")}
                    empty={t("firstDealHint")}
                  />
                  <ActiveDealCard
                    deal={stats.data.data.active_deal}
                    lastBarOpenUs={stats.data.data.last_bar_open_us}
                  />
                </div>
              ),
            },
            {
              id: "deals",
              label: t("tabDeals"),
              panel: (
                <BotDealsTable
                  deals={deals.data.data}
                  maxSo={data.strategy.max_safety_orders}
                  testId="deals-table"
                />
              ),
            },
            {
              id: "stats",
              label: t("tabStats"),
              panel: (
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <SoHistogram
                    deals={deals.data.data}
                    maxSo={data.strategy.max_safety_orders}
                    testId="so-histogram"
                  />
                  <WinLossRing
                    winningDeals={stats.data.data.winning_deals}
                    dealsCompleted={stats.data.data.deals_completed}
                    testId="win-loss-ring"
                  />
                </div>
              ),
            },
            {
              id: "events",
              label: t("tabEvents"),
              panel: (
                <EventsTimeline
                  botId={id}
                  status={data.status}
                  maxSo={data.strategy.max_safety_orders}
                  testId="events-timeline"
                />
              ),
            },
            ]}
          />
        </>
      )}
    </div>
  );
}
