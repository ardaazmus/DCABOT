"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BotActions } from "@/components/bots/bot-actions";
import { DataTable, type TableColumn } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { EnumValue } from "@/components/enum-value";
import { BotRowActiveDeal, BotRowProfit } from "@/components/bots/bot-row-stats";
import { BotStatusHint } from "@/components/bots/bot-status-hint";
import { Money } from "@/components/money";
import { StatusBadge, type StatusBadgeVariant } from "@/components/status-badge";
import { useBots } from "@/lib/api/queries";
import type { Bot } from "@/lib/api/schemas";
import { BOT_STATUSES } from "@/lib/bots";
import { isDecimalString } from "@/lib/decimal";
import { enumLabel } from "@/lib/enum-labels";
import { formatEventTime } from "@/lib/format-time";

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

export default function BotsPage() {
  const t = useTranslations("bots");
  const locale = useLocale();
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [showArchived, setShowArchived] = useState(false);
  const bots = useBots(showArchived);

  const rows = useMemo(() => {
    const all = bots.data?.data ?? [];
    return statusFilter === "ALL" ? all : all.filter((bot) => bot.status === statusFilter);
  }, [bots.data, statusFilter]);

  const columns: TableColumn<Bot>[] = useMemo(
    () => [
      {
        id: "name",
        header: t("colName"),
        accessorFn: (bot) => bot.name,
        cell: ({ row }) => (
          <Link
            href={`/bots/${row.original.bot_id}`}
            className="font-medium text-accent hover:underline"
          >
            {row.original.name}
          </Link>
        ),
      },
      {
        id: "symbol",
        header: t("colSymbol"),
        accessorFn: (bot) => bot.symbol,
        cell: ({ row }) => <span className="font-mono">{row.original.symbol}</span>,
      },
      {
        id: "type",
        header: t("colType"),
        accessorFn: (bot) => bot.type,
        cell: ({ row }) => (
          <StatusBadge variant={row.original.type === "DCA" ? "paper" : "testnet"}>
            {row.original.type === "FUTURES_GRID" ? "FUTURES GRID" : row.original.type}
          </StatusBadge>
        ),
      },
      {
        id: "status",
        header: t("colStatus"),
        accessorFn: (bot) => bot.status,
        cell: ({ row }) => (
          <span className="flex flex-col items-start gap-0.5">
            <span className="flex items-center gap-1">
              <StatusBadge variant={STATUS_VARIANT[row.original.status] ?? "stopped"}>
                <EnumValue code={row.original.status} />
              </StatusBadge>
              {row.original.archived ? (
                <StatusBadge variant="stopped">{t("archivedBadge")}</StatusBadge>
              ) : null}
            </span>
            <BotStatusHint status={row.original.status} reason={row.original.status_reason} />
          </span>
        ),
      },
      {
        id: "mode",
        header: t("colMode"),
        accessorFn: (bot) => bot.mode,
        cell: ({ row }) => (
          <StatusBadge variant={MODE_VARIANT[row.original.mode] ?? "paper"}>
            <EnumValue code={row.original.mode} />
          </StatusBadge>
        ),
      },
      {
        id: "budget",
        header: t("colBudget"),
        accessorFn: (bot) => bot.budget,
        cell: ({ row }) => (
          <Money
            value={isDecimalString(row.original.budget) ? row.original.budget : undefined}
            suffix="USDT"
          />
        ),
      },
      {
        id: "totalProfit",
        header: t("colTotalProfit"),
        enableSorting: false,
        cell: ({ row }) => <BotRowProfit botId={row.original.bot_id} />,
      },
      {
        id: "activeDeal",
        header: t("colActiveDeal"),
        enableSorting: false,
        cell: ({ row }) => <BotRowActiveDeal botId={row.original.bot_id} />,
      },
      {
        id: "created",
        header: t("colCreated"),
        accessorFn: (bot) => bot.created_at_us,
        cell: ({ row }) => (
          <span className="font-mono text-xs">
            {formatEventTime(row.original.created_at_us, locale)}
          </span>
        ),
      },
      {
        id: "actions",
        header: "",
        enableSorting: false,
        cell: ({ row }) => <BotActions bot={row.original} compact />,
      },
    ],
    [t, locale],
  );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <Link
          href="/bots/new"
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90"
        >
          {t("newBot")}
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-sm">
        <label htmlFor="bot-status-filter" className="font-medium">
          {t("colStatus")}:
        </label>
        <select
          id="bot-status-filter"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="rounded-md border border-input bg-background px-2 py-1.5"
        >
          <option value="ALL">{t("filterAll")}</option>
          {BOT_STATUSES.map((status) => (
            <option key={status} value={status}>
              {enumLabel(status, locale === "en" ? "en" : "tr")}
            </option>
          ))}
        </select>
        <label className="ml-2 flex items-center gap-2">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(event) => setShowArchived(event.target.checked)}
            className="size-4 accent-[var(--accent)]"
          />
          {t("showArchived")}
        </label>
      </div>

      {bots.isPending ? (
        <p role="status" className="text-sm text-muted-foreground">
          …
        </p>
      ) : bots.isError || bots.data === undefined ? (
        <p role="alert" className="text-sm text-loss">
          {t("loadError")}
        </p>
      ) : rows.length === 0 ? (
        <EmptyState
          title={t("firstBot")}
          description={t("firstBotHint")}
          actionLabel={t("firstBot")}
          actionHref="/bots/new"
        />
      ) : (
        <DataTable columns={columns} data={rows} emptyTitle={t("firstBot")} />
      )}
    </div>
  );
}
