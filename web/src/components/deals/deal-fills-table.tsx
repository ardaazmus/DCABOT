"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

import { DataTable, type TableColumn } from "@/components/data-table";
import { Money, Price, Qty } from "@/components/money";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BotEvent } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";
import { formatEventTime } from "@/lib/format-time";

type FillRow = {
  key: string;
  time_us: number;
  side: "base" | "safety" | "manual" | "sell";
  index: number | null;
  price: string | null;
  qty: string | null;
  fee: string | null;
};

/** Olaylardan dolum satırları (eskiden yeniye). İptal satışı satır olmaz. */
export function fillsFromEvents(events: readonly BotEvent[]): FillRow[] {
  const rows: FillRow[] = [];
  for (const event of events) {
    const text = (value: string | number | null | undefined): string | null =>
      typeof value === "string" ? value : null;
    if (event.kind === "DEAL_STARTED") {
      rows.push({
        key: `base-${event.time_us}`,
        time_us: event.time_us,
        side: "base",
        index: null,
        price: text(event.detail.price),
        qty: text(event.detail.qty),
        fee: text(event.detail.fee),
      });
    } else if (event.kind === "SAFETY_ORDER_FILLED" || event.kind === "MANUAL_ORDER_FILLED") {
      const index = typeof event.detail.index === "number" ? event.detail.index : null;
      rows.push({
        key: `${event.kind}-${event.time_us}`,
        time_us: event.time_us,
        side: event.kind === "SAFETY_ORDER_FILLED" ? "safety" : "manual",
        index,
        price: text(event.detail.price),
        qty: text(event.detail.qty),
        fee: text(event.detail.fee),
      });
    } else if (event.kind === "DEAL_CLOSED" && event.detail.reason !== "CANCELLED") {
      rows.push({
        key: `sell-${event.time_us}`,
        time_us: event.time_us,
        side: "sell",
        index: null,
        price: text(event.detail.price),
        qty: text(event.detail.qty),
        fee: text(event.detail.fee),
      });
    }
  }
  return rows;
}

export function DealFillsTable({ events, testId }: { events: readonly BotEvent[]; testId: string }) {
  const t = useTranslations("deals");
  const locale = useLocale();
  const rows = useMemo(() => fillsFromEvents(events), [events]);
  const amount = (value: string | null, suffix: string) => (
    <Money value={isDecimalString(value) ? value : undefined} suffix={suffix} />
  );
  const columns: TableColumn<FillRow>[] = [
    {
      id: "side",
      header: t("colSide"),
      cell: ({ row }) => {
        const fill = row.original;
        if (fill.side === "base") return <StatusBadge variant="paper">{t("baseBadge")}</StatusBadge>;
        if (fill.side === "sell") return <StatusBadge variant="error">{t("sellBadge")}</StatusBadge>;
        if (fill.side === "safety")
          return <StatusBadge variant="warn">{t("safetyBadge", { index: fill.index ?? "?" })}</StatusBadge>;
        return <StatusBadge variant="testnet">{t("manualBadge", { index: fill.index ?? "?" })}</StatusBadge>;
      },
    },
    {
      id: "time",
      header: t("colTime"),
      accessorFn: (fill) => formatEventTime(fill.time_us, locale),
    },
    {
      id: "price",
      header: t("colPrice"),
      cell: ({ row }) => (
        <Price value={isDecimalString(row.original.price) ? row.original.price : undefined} suffix="USDT" />
      ),
    },
    {
      id: "qty",
      header: t("colQty"),
      cell: ({ row }) => (
        <Qty value={isDecimalString(row.original.qty) ? row.original.qty : undefined} />
      ),
    },
    {
      id: "fee",
      header: t("colFee"),
      cell: ({ row }) => <span>{amount(row.original.fee, "USDT")}</span>,
    },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("fillsTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div data-testid={testId}>
          <DataTable columns={columns} data={rows} emptyTitle={t("fillsTitle")} pageSize={25} />
        </div>
      </CardContent>
    </Card>
  );
}
