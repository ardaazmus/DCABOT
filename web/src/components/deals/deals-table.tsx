"use client";

import { useQueries } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { DurationText } from "@/components/bots/duration-text";
import { CLOSE_REASON_KEY } from "@/components/bots/event-text";
import { DataTable, type TableColumn } from "@/components/data-table";
import { Price } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { StatusBadge } from "@/components/status-badge";
import { apiGet } from "@/lib/api/client";
import {
  botEnvelopeSchema,
  dealDetailEnvelopeSchema,
  isGridStrategy,
  type Bot,
  type DealDetail,
  type DealV2,
} from "@/lib/api/schemas";

/** Deal'ler yalnız DCA botlardan gelir; grid gövdesinde SO alanı yoktur. */
function dcaStrategyOf(bot: Bot | undefined) {
  const strategy = bot?.strategy;
  return strategy !== undefined && !isGridStrategy(strategy) ? strategy : undefined;
}
import { isDecimalString } from "@/lib/decimal";
import { formatEventTime } from "@/lib/format-time";

export function dealId(botId: string, seq: number): string {
  return `${botId}:${seq}`;
}

function CloseReasonBadge({ reason }: { reason: string | null }) {
  const t = useTranslations("bots");
  if (reason === null) {
    return <StatusBadge variant="paper">{t("openBadge")}</StatusBadge>;
  }
  const variant =
    reason === "TAKE_PROFIT"
      ? "running"
      : reason === "STOP_LOSS"
        ? "error"
        : reason === "MANUAL_CLOSE"
          ? "warn"
          : "stopped";
  const key = CLOSE_REASON_KEY[reason];
  return <StatusBadge variant={variant}>{key === undefined ? reason : t(key)}</StatusBadge>;
}

function SoCell({ filled, manual, max }: { filled: number; manual: number; max: number | null }) {
  const t = useTranslations("deals");
  if (max === null) return <span className="font-mono">—</span>;
  return (
    <span className="font-mono">
      {t("soProgress", { filled, max })}
      {manual > 0 ? ` ${t("manualSuffix", { count: manual })}` : ""}
    </span>
  );
}

/**
 * Birleşik deal tablosu. Aktif satırlar canlı detay çeker
 * (bot sorgularıyla aynı anahtarlar: önbellek paylaşılır);
 * geçmiş satırlar liste alanlarıyla yetinir.
 */
export function DealsTable({
  rows,
  mode,
  testId,
}: {
  rows: readonly DealV2[];
  mode: "active" | "history";
  testId: string;
}) {
  const t = useTranslations("deals");
  const router = useRouter();
  const locale = useLocale();
  const [nowUs] = useState(() => Date.now() * 1000);

  const details = useQueries({
    queries:
      mode === "active"
        ? rows.map((row) => ({
            queryKey: ["v2-deal", row.bot_id, row.deal],
            queryFn: () =>
              apiGet(
                `/api/v2/bots/${encodeURIComponent(row.bot_id)}/deals/${row.deal}`,
                dealDetailEnvelopeSchema,
              ),
            refetchInterval: 15_000,
          }))
        : [],
  });
  const botIds = useMemo(() => [...new Set(rows.map((row) => row.bot_id))], [rows]);
  const bots = useQueries({
    queries: botIds.map((botId) => ({
      queryKey: ["v2-bot", botId],
      queryFn: () => apiGet(`/api/v2/bots/${encodeURIComponent(botId)}`, botEnvelopeSchema),
    })),
  });
  const botById = useMemo(() => {
    const map = new Map<string, Bot>();
    for (const query of bots) {
      const bot = query.data?.data;
      if (bot !== undefined) map.set(bot.bot_id, bot);
    }
    return map;
  }, [bots]);
  const detailByDeal = useMemo(() => {
    const map = new Map<string, DealDetail>();
    if (mode !== "active") return map;
    rows.forEach((row, index) => {
      const detail = details[index]?.data?.data;
      if (detail !== undefined) map.set(dealId(row.bot_id, row.deal), detail);
    });
    return map;
  }, [details, mode, rows]);

  const money = (value: string | null) => (
    <Price value={isDecimalString(value) ? value : undefined} suffix="USDT" />
  );

  const columns: TableColumn<DealV2>[] = [
    {
      id: "pair",
      header: t("colPair"),
      cell: ({ row }) => (
        <Link
          href={`/market/${row.original.symbol}`}
          className="font-mono underline-offset-4 hover:underline"
        >
          {row.original.symbol}
        </Link>
      ),
    },
    {
      id: "bot",
      header: t("colBot"),
      cell: ({ row }) => (
        <Link
          href={`/bots/${encodeURIComponent(row.original.bot_id)}`}
          className="underline-offset-4 hover:underline"
        >
          {row.original.bot_name}
        </Link>
      ),
    },
    {
      id: "side",
      header: t("colSide"),
      cell: ({ row }) => (
        <StatusBadge variant="paper">
          {dcaStrategyOf(botById.get(row.original.bot_id))?.direction === "SHORT"
            ? t("shortBadge")
            : t("longBadge")}
        </StatusBadge>
      ),
    },
  ];
  if (mode === "active") {
    columns.push(
      {
        id: "avg",
        header: t("colAvg"),
        cell: ({ row }) => money(detailByDeal.get(dealId(row.original.bot_id, row.original.deal))?.average_price ?? null),
      },
      {
        id: "current",
        header: t("colCurrent"),
        cell: ({ row }) => money(detailByDeal.get(dealId(row.original.bot_id, row.original.deal))?.mark_price ?? null),
      },
      {
        id: "tp",
        header: t("colTp"),
        cell: ({ row }) => money(detailByDeal.get(dealId(row.original.bot_id, row.original.deal))?.take_profit_price ?? null),
      },
      {
        id: "upnl",
        header: t("colUpnl"),
        cell: ({ row }) => {
          const detail = detailByDeal.get(dealId(row.original.bot_id, row.original.deal));
          return (
            <span className="flex flex-col">
              <Pnl
                value={isDecimalString(detail?.unrealized_profit) ? detail?.unrealized_profit : undefined}
                variant="usdt"
                suffix="USDT"
              />
              <Pnl
                value={isDecimalString(detail?.unrealized_percent) ? detail?.unrealized_percent : undefined}
                variant="percent"
              />
            </span>
          );
        },
      },
      {
        id: "so",
        header: t("colSo"),
        cell: ({ row }) => (
          <SoCell
            filled={row.original.safety_orders_filled}
            manual={row.original.manual_orders_filled}
            max={dcaStrategyOf(botById.get(row.original.bot_id))?.max_safety_orders ?? null}
          />
        ),
      },
      {
        id: "duration",
        header: t("colDuration"),
        cell: ({ row }) => <DurationText timeUs={nowUs - row.original.started_at_us} />,
      },
    );
  } else {
    columns.push(
      {
        id: "started",
        header: t("colStart"),
        accessorFn: (deal) => formatEventTime(deal.started_at_us, locale),
      },
      {
        id: "closed",
        header: t("colEnd"),
        accessorFn: (deal) =>
          deal.closed_at_us === null ? "—" : formatEventTime(deal.closed_at_us, locale),
      },
      {
        id: "duration",
        header: t("colDuration"),
        cell: ({ row }) =>
          row.original.closed_at_us === null ? (
            <span className="font-mono">—</span>
          ) : (
            <DurationText timeUs={row.original.closed_at_us - row.original.started_at_us} />
          ),
      },
      {
        id: "so",
        header: t("colSo"),
        cell: ({ row }) => (
          <SoCell
            filled={row.original.safety_orders_filled}
            manual={row.original.manual_orders_filled}
            max={dcaStrategyOf(botById.get(row.original.bot_id))?.max_safety_orders ?? null}
          />
        ),
      },
      {
        id: "profit",
        header: t("colProfit"),
        cell: ({ row }) => (
          <Pnl
            value={isDecimalString(row.original.profit) ? row.original.profit : undefined}
            variant="usdt"
            suffix="USDT"
          />
        ),
      },
      {
        id: "reason",
        header: t("colReason"),
        cell: ({ row }) => <CloseReasonBadge reason={row.original.close_reason} />,
      },
    );
  }
  columns.push({
    id: "deal",
    header: `#`,
    cell: ({ row }) => (
      <Link
        href={`/deals/${encodeURIComponent(dealId(row.original.bot_id, row.original.deal))}`}
        className="font-mono underline-offset-4 hover:underline"
      >
        #{row.original.deal}
      </Link>
    ),
  });

  return (
    <div data-testid={testId}>
      <DataTable
        columns={columns}
        data={[...rows]}
        emptyTitle={mode === "active" ? t("emptyActiveTitle") : t("emptyHistoryTitle")}
        emptyDescription={mode === "active" ? t("emptyActiveHint") : t("emptyHistoryHint")}
        pageSize={25}
        onRowClick={(row) => router.push(`/deals/${encodeURIComponent(dealId(row.bot_id, row.deal))}`)}
      />
    </div>
  );
}
