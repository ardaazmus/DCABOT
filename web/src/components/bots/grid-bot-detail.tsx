"use client";

import { useLocale, useTranslations } from "next-intl";

import { BotActions } from "@/components/bots/bot-actions";
import { EventsTimeline } from "@/components/bots/events-timeline";
import { BotCopyButton } from "@/components/bots/bot-copy-button";
import { BotStatusHint } from "@/components/bots/bot-status-hint";
import { ReplayForm } from "@/components/bots/replay-form";
import { EmptyState } from "@/components/empty-state";
import { EnumValue } from "@/components/enum-value";
import { Money, Price } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge, type StatusBadgeVariant } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useGridState } from "@/lib/api/queries";
import {
  isFuturesGridState,
  isFuturesGridStrategy,
  isGridStrategy,
  type Bot,
  type FuturesGridBotStrategy,
  type FuturesGridState,
  type GridBotStrategy,
  type GridState,
} from "@/lib/api/schemas";
import { decimalToNumber, gridLevelLayout } from "@/lib/chart/grid-levels";
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

function GridStrategyRows({ strategy }: { strategy: GridBotStrategy | FuturesGridBotStrategy }) {
  const t = useTranslations("grid");
  const rows: [string, string][] = [
    ...(isFuturesGridStrategy(strategy)
      ? [
          [t("direction"), strategy.direction] as [string, string],
          [t("leverage"), `${strategy.leverage}x`] as [string, string],
        ]
      : []),
    [t("mode"), strategy.mode],
    [t("lowerPrice"), `${strategy.lower_price} USDT`],
    [t("upperPrice"), `${strategy.upper_price} USDT`],
    [t("intervalCount"), String(strategy.interval_count)],
    [t("feeRate"), `%${strategy.fee_rate}`],
    [t("stopLossPrice"), strategy.stop_loss_price ?? "—"],
    [t("takeProfitPct"), strategy.take_profit_pct === null ? "—" : `%${strategy.take_profit_pct}`],
    [t("trailingUpPct"), strategy.trailing_up_pct === null ? "—" : `%${strategy.trailing_up_pct}`],
    [t("trailingDownPct"), strategy.trailing_down_pct === null ? "—" : `%${strategy.trailing_down_pct}`],
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

/**
 * Seviye merdiveni: her aralık bir satırdır; renk bekleyen yöndedir
 * (BUY=safety, SELL=entry). Güncel fiyat ve giriş çizgileri işaretlidir.
 * Yalnız görüntü; tüm değerler backend metnidir.
 */
export function GridLevelsChart({
  state,
  testId = "grid-levels",
}: {
  state: Pick<GridState, "levels" | "pending" | "last_price" | "entry_price">;
  testId?: string;
}) {
  const t = useTranslations("grid");
  const locale = useLocale() === "en" ? "en" : "tr";
  const { levels, pending, last_price } = state;
  const rowH = 22;
  const height = Math.max(60, levels.length * rowH + 8);
  const { rows, yFor } = gridLevelLayout(levels, height);
  const last = decimalToNumber(last_price);
  const entry = decimalToNumber(state.entry_price);
  return (
    <svg
      data-testid={testId}
      role="img"
      aria-label={t("levelsChart")}
      viewBox={`0 0 640 ${height}`}
      className="w-full"
    >
      {rows.map(({ level, index, y }) => {
        const below = pending[index - 1];
        const color =
          below === "BUY" ? "var(--color-safety)" : below === "SELL" ? "var(--color-entry)" : "var(--color-muted-foreground)";
        return (
          <g key={level}>
            <line x1={120} x2={640} y1={y} y2={y} stroke={color} strokeWidth={1} opacity={0.7} />
            <text x={112} y={y + 4} textAnchor="end" fontSize={11} className="fill-muted-foreground font-mono">
              {isDecimalString(level) ? formatDecimal(level, { locale }) : level}
            </text>
          </g>
        );
      })}
      {last !== null ? (
        <g>
          <line x1={120} x2={640} y1={yFor(last)} y2={yFor(last)} stroke="var(--color-profit)" strokeWidth={2} strokeDasharray="6 3" />
          <text x={112} y={yFor(last) + 4} textAnchor="end" fontSize={11} className="fill-profit font-mono">
            {isDecimalString(state.last_price) ? formatDecimal(state.last_price, { locale }) : ""}
          </text>
        </g>
      ) : null}
      {entry !== null ? (
        <circle cx={126} cy={yFor(entry)} r={4} className="fill-accent" aria-label={t("entryPrice")} />
      ) : null}
    </svg>
  );
}

function GridKpis({ state }: { state: GridState | FuturesGridState }) {
  const t = useTranslations("grid");
  const kpis: { label: string; node: React.ReactNode }[] = [
    { label: t("gridStatus"), node: <EnumValue code={state.grid_status} /> },
  ];
  if (isFuturesGridState(state)) {
    kpis.push(
      { label: t("direction"), node: <span className="font-mono">{`${state.direction} · ${state.leverage}x`}</span> },
      {
        label: t("equity"),
        node: <Money value={isDecimalString(state.equity_at_last) ? state.equity_at_last : undefined} suffix="USDT" />,
      },
      { label: t("cyclesClosed"), node: <span className="font-mono">{state.cycles_closed}</span> },
      {
        label: t("realized"),
        node: (
          <Pnl
            value={isDecimalString(state.realized_gross_pnl) ? state.realized_gross_pnl : undefined}
            variant="usdt"
            suffix="USDT"
          />
        ),
      },
      {
        label: t("feesPaid"),
        node: <Money value={isDecimalString(state.fees_paid_quote) ? state.fees_paid_quote : undefined} suffix="USDT" />,
      },
      {
        label: t("funding"),
        node: (
          <Pnl
            value={isDecimalString(state.funding_cashflow) ? state.funding_cashflow : undefined}
            variant="usdt"
            suffix="USDT"
          />
        ),
      },
      {
        label: t("walletFree"),
        node: <Money value={isDecimalString(state.wallet_free) ? state.wallet_free : undefined} suffix="USDT" />,
      },
      { label: t("openLots"), node: <span className="font-mono">{state.open_lots.length}</span> },
      {
        label: t("liqEstimate"),
        node: <span className="font-mono">{state.liq_estimate_price ?? "—"}</span>,
      },
    );
  } else {
    kpis.push(
      {
        label: t("equity"),
        node: <Money value={isDecimalString(state.equity_at_last) ? state.equity_at_last : undefined} suffix="USDT" />,
      },
      { label: t("cyclesClosed"), node: <span className="font-mono">{state.cycles_closed}</span> },
      {
        label: t("realized"),
        node: (
          <Pnl
            value={isDecimalString(state.realized_profit_quote) ? state.realized_profit_quote : undefined}
            variant="usdt"
            suffix="USDT"
          />
        ),
      },
      {
        label: t("feesPaid"),
        node: <Money value={isDecimalString(state.fees_paid_quote) ? state.fees_paid_quote : undefined} suffix="USDT" />,
      },
      {
        label: t("reserve"),
        node: <Money value={isDecimalString(state.quote_reserve) ? state.quote_reserve : undefined} suffix="USDT" />,
      },
    );
  }
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="flex flex-col gap-1 rounded-lg border border-border p-3">
          <span className="text-xs text-muted-foreground">{kpi.label}</span>
          <span className="text-sm font-medium">{kpi.node}</span>
        </div>
      ))}
    </div>
  );
}

function GridFillsTable({ state }: { state: GridState | FuturesGridState }) {
  const t = useTranslations("grid");
  const locale = useLocale() === "en" ? "en" : "tr";
  if (state.fills_recent.length === 0) {
    return <EmptyState title={t("noFills")} description={t("noFillsHint")} />;
  }
  return (
    <ol data-testid="grid-fills" className="flex flex-col gap-1 text-sm">
      {state.fills_recent.map((fill) => {
        const quantity = "quantity" in fill ? fill.quantity : fill.base_quantity;
        return (
          <li key={fill.fill_id} className="flex flex-wrap items-center gap-x-3 gap-y-0.5 rounded-lg px-2 py-1.5 hover:bg-muted">
            <StatusBadge variant={fill.side === "BUY" ? "warn" : "running"}>
              <EnumValue code={fill.side} />
            </StatusBadge>
            <Price value={isDecimalString(fill.price) ? fill.price : undefined} suffix="USDT" />
            <span className="font-mono text-muted-foreground">
              {isDecimalString(quantity) ? formatDecimal(quantity, { locale }) : quantity}
            </span>
            <span className="font-mono text-xs text-muted-foreground">{fill.fill_id}</span>
          </li>
        );
      })}
    </ol>
  );
}

export function GridBotDetail({ bot }: { bot: Bot }) {
  const t = useTranslations("bots");
  const tg = useTranslations("grid");
  const strategy = bot.strategy;
  const grid = useGridState(bot.bot_id, bot.status, isGridStrategy(strategy));
  if (!isGridStrategy(strategy)) return null;
  const state = grid.data?.data ?? null;
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">{bot.name}</h1>
            <span className="font-mono text-lg text-muted-foreground">{bot.symbol}</span>
            <StatusBadge variant="paper">
              {isFuturesGridStrategy(strategy) ? tg("futuresBadge") : tg("gridBadge")}
            </StatusBadge>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge variant={STATUS_VARIANT[bot.status] ?? "stopped"}>
              <EnumValue code={bot.status} />
            </StatusBadge>
            <StatusBadge variant={MODE_VARIANT[bot.mode] ?? "paper"}>
              <EnumValue code={bot.mode} />
            </StatusBadge>
            {bot.archived ? <StatusBadge variant="stopped">{t("archivedBadge")}</StatusBadge> : null}
          </div>
          <BotStatusHint status={bot.status} reason={bot.status_reason} />
        </div>
        <div className="flex flex-wrap items-start gap-2">
          <BotCopyButton botId={bot.bot_id} disabled={bot.archived} />
          <BotActions bot={bot} />
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
            <GridStrategyRows strategy={strategy} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>
              <h2>{tg("levelsTitle")}</h2>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {grid.isPending ? (
              <Skeleton className="h-64 w-full" />
            ) : grid.isError || state === null ? (
              <p role="alert" className="text-sm text-loss">
                {t("loadError")}
              </p>
            ) : (
              <GridLevelsChart state={state} />
            )}
          </CardContent>
        </Card>
      </div>

      {grid.isPending ? (
        <div className="flex flex-col gap-2" role="status">
          <Skeleton className="h-24 w-full" />
        </div>
      ) : grid.isError || state === null ? (
        <p role="alert" className="text-sm text-loss">
          {t("loadError")}
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          {bot.mode === "PAPER" && bot.status === "STOPPED" && !bot.archived ? (
            <ReplayForm botId={bot.bot_id} />
          ) : null}
          <GridKpis state={state} />
          <Card>
            <CardHeader>
              <CardTitle>
                <h2>{tg("fillsTitle")}</h2>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <GridFillsTable state={state} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>
                <h2>{t("tabEvents")}</h2>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EventsTimeline botId={bot.bot_id} status={bot.status} maxSo={0} testId="events-timeline" />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
