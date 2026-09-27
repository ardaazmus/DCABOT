"use client";

import { useMemo, useState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { DataTable, type TableColumn } from "@/components/data-table";
import { Pnl } from "@/components/pnl";
import { StatusBadge } from "@/components/status-badge";
import type { BotDeal } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";
import { formatEventTime } from "@/lib/format-time";

import { DurationText } from "./duration-text";
import { CLOSE_REASON_KEY } from "./event-text";

/**
 * Deal tablosu: en yeni üstte, sayfalı. Süre kapanmışta kapanışa,
 * açıkta şu ana kadardır; kapanış nedeni rozetlidir.
 */
export function BotDealsTable({
  deals,
  maxSo,
  testId,
}: {
  deals: readonly BotDeal[];
  maxSo: number;
  testId: string;
}) {
  const t = useTranslations("bots");
  const locale = useLocale();
  const rows = useMemo(() => [...deals].reverse(), [deals]);
  const [nowUs] = useState(() => Date.now() * 1000);
  const showSymbol = new Set(rows.map((deal) => deal.symbol)).size > 1;
  const columns: TableColumn<BotDeal>[] = [
    { id: "deal", header: t("colDeal"), accessorFn: (deal) => deal.deal },
    ...(showSymbol
      ? [
          {
            id: "symbol",
            header: t("colSymbol"),
            accessorFn: (deal: BotDeal) => deal.symbol ?? "—",
          } satisfies TableColumn<BotDeal>,
        ]
      : []),
    {
      id: "started",
      header: t("colStart"),
      accessorFn: (deal) => formatEventTime(deal.started_at_us, locale),
    },
    {
      id: "closed",
      header: t("colEnd"),
      accessorFn: (deal) =>
        deal.closed_at_us === null ? t("openBadge") : formatEventTime(deal.closed_at_us, locale),
    },
    {
      id: "duration",
      header: t("colDuration"),
      cell: ({ row }) => (
        <DurationText
          timeUs={(row.original.closed_at_us ?? nowUs) - row.original.started_at_us}
        />
      ),
    },
    {
      id: "so",
      header: t("colSo"),
      accessorFn: (deal) =>
        t("soProgress", { filled: deal.safety_orders_filled, max: maxSo }),
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
      id: "closeReason",
      header: t("colCloseReason"),
      cell: ({ row }) => {
        const reason = row.original.close_reason;
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
        const key = CLOSE_REASON_KEY[reason] ?? "eventUnknown";
        return <StatusBadge variant={variant}>{key === "eventUnknown" ? reason : t(key)}</StatusBadge>;
      },
    },
  ];
  return (
    <div data-testid={testId}>
      <DataTable columns={columns} data={rows} emptyTitle={t("firstDealHint")} />
    </div>
  );
}
