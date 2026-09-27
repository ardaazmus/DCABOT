"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

import { DataTable, type TableColumn } from "@/components/data-table";
import { Pnl } from "@/components/pnl";
import { StatusBadge } from "@/components/status-badge";
import type { BacktestResult } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";
import { formatEventTime } from "@/lib/format-time";

type DealRow = BacktestResult["deals"][number];

/** Deal tablosu; açık deal "açık" rozetiyle, kârı yoktur. */
export function DealTable({ deals }: { deals: readonly DealRow[] }) {
  const t = useTranslations("backtest");
  const locale = useLocale();
  const columns: TableColumn<DealRow>[] = useMemo(
    () => [
      {
        id: "deal",
        header: t("colNum"),
        accessorFn: (row) => row.deal,
        cell: ({ row }) => <span className="font-mono">{row.original.deal}</span>,
      },
      {
        id: "started",
        header: t("colStart"),
        accessorFn: (row) => row.started_at_us,
        cell: ({ row }) => (
          <span className="font-mono text-xs">
            {formatEventTime(row.original.started_at_us, locale)}
          </span>
        ),
      },
      {
        id: "closed",
        header: t("colEnd"),
        accessorFn: (row) => row.closed_at_us ?? 0,
        cell: ({ row }) =>
          row.original.closed_at_us === null ? (
            <StatusBadge variant="warn">{t("openBadge")}</StatusBadge>
          ) : (
            <span className="font-mono text-xs">
              {formatEventTime(row.original.closed_at_us, locale)}
            </span>
          ),
      },
      {
        id: "so",
        header: t("colSoFilled"),
        accessorFn: (row) => row.safety_orders_filled,
        cell: ({ row }) => <span className="font-mono">{row.original.safety_orders_filled}</span>,
      },
      {
        id: "profit",
        header: t("colProfit"),
        accessorFn: (row) => row.profit ?? "",
        cell: ({ row }) => (
          <Pnl
            value={
              row.original.profit !== null && isDecimalString(row.original.profit)
                ? row.original.profit
                : undefined
            }
            suffix="USDT"
            title={row.original.profit ?? undefined}
          />
        ),
      },
    ],
    [t, locale],
  );
  return (
    <DataTable
      columns={columns}
      data={[...deals]}
      emptyTitle={t("dealsTitle")}
      pageSize={10}
    />
  );
}
