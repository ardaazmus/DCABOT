"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { DataTable, type TableColumn } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { FavoriteStar } from "@/components/market/favorite-star";
import { Price } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { VolumeCompact } from "@/components/volume-compact";
import { useExchangeSymbols, useTickers24h } from "@/lib/api/queries";
import { compareDecimal, isDecimalString, type DecimalString } from "@/lib/decimal";
import { useFavorites } from "@/lib/favorites";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 25;

type Tab = "USDT" | "USDC" | "BTC" | "FAV";

type MarketRow = {
  symbol: string;
  quote: string;
  /** Bilinen durumda işlem dışı (BREAK vb.): veri istenmez, rozet takılır. */
  halted: boolean;
  lastPrice: DecimalString | undefined;
  change: DecimalString | undefined;
  volume: DecimalString | undefined;
};

function isHalted(status: string): boolean {
  return status !== "" && status !== "TRADING";
}

function toDecimal(text: string | undefined): DecimalString | undefined {
  return text !== undefined && isDecimalString(text) ? text : undefined;
}

/** Sayısal sütun karşılaştırması (sözlük sırası değil). */
function decimalSort(
  rowA: { getValue: (columnId: string) => unknown },
  rowB: { getValue: (columnId: string) => unknown },
  columnId: string,
): number {
  const x = rowA.getValue(columnId);
  const y = rowB.getValue(columnId);
  const dx = isDecimalString(x) ? x : undefined;
  const dy = isDecimalString(y) ? y : undefined;
  if (dx === undefined && dy === undefined) return 0;
  if (dx === undefined) return 1;
  if (dy === undefined) return -1;
  return compareDecimal(dx, dy);
}

export default function MarketPage() {
  const t = useTranslations("nav");
  const tm = useTranslations("market");
  const router = useRouter();
  const symbolsQuery = useExchangeSymbols(true);
  const favorites = useFavorites((state) => state.symbols);
  const [tab, setTab] = useState<Tab>("USDT");
  const [query, setQuery] = useState("");
  const [pageIndex, setPageIndex] = useState(0);

  const entries = useMemo(() => {
    const all = symbolsQuery.data?.symbols ?? [];
    const lookup = new Map(all.map((entry) => [entry.symbol, entry]));
    // Ana sekmeler yalnız TRADING: işlem görmeyen paritenin verisi
    // gelmiyor; üstelik tek bozuk sembol tüm toplu isteği 502'ye
    // düşürüyor. Favorilerde işlem-dışı satırlar rozetle durur.
    const base =
      tab === "FAV"
        ? favorites.map(
            (symbol) =>
              lookup.get(symbol) ?? {
                symbol,
                status: "",
                base_asset: "",
                quote_asset: "",
              },
          )
        : all.filter((entry) => entry.quote_asset === tab && entry.status === "TRADING");
    const needle = query.trim().toLocaleLowerCase("tr");
    const filtered =
      needle === ""
        ? base
        : base.filter((entry) => entry.symbol.toLocaleLowerCase("tr").includes(needle));
    return filtered;
  }, [symbolsQuery.data, favorites, tab, query]);

  const pageCount = Math.max(1, Math.ceil(entries.length / PAGE_SIZE));
  const safePage = Math.min(pageIndex, pageCount - 1);
  const pageEntries = entries.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);
  const pageSymbols = useMemo(
    () => pageEntries.filter((entry) => !isHalted(entry.status)).map((entry) => entry.symbol),
    [pageEntries],
  );
  const tickers = useTickers24h(pageSymbols, 15_000);

  const rows: MarketRow[] = useMemo(() => {
    const bySymbol = new Map(
      (tickers.data?.data ?? []).map((ticker) => [ticker.symbol, ticker]),
    );
    return pageEntries.map((entry) => {
      const ticker = bySymbol.get(entry.symbol);
      return {
        symbol: entry.symbol,
        quote: entry.quote_asset,
        halted: isHalted(entry.status),
        lastPrice: toDecimal(ticker?.last_price),
        change: toDecimal(ticker?.price_change_percent),
        volume: toDecimal(ticker?.quote_volume),
      };
    });
  }, [pageEntries, tickers.data]);

  const columns: TableColumn<MarketRow>[] = useMemo(
    () => [
      {
        accessorKey: "symbol",
        header: tm("pair"),
        cell: ({ row }) => (
          <span className="inline-flex items-center gap-2">
            <Link
              href={`/market/${row.original.symbol}`}
              onClick={(event) => event.stopPropagation()}
              className="font-mono font-medium text-accent hover:underline"
            >
              {row.original.symbol}
            </Link>
            {row.original.halted ? (
              <StatusBadge variant="stopped">{tm("notTrading")}</StatusBadge>
            ) : null}
          </span>
        ),
      },
      {
        accessorKey: "lastPrice",
        header: tm("price"),
        sortFn: decimalSort,
        sortUndefined: "last",
        cell: ({ row }) => <Price value={row.original.lastPrice} />,
      },
      {
        accessorKey: "change",
        header: tm("change"),
        sortFn: decimalSort,
        sortUndefined: "last",
        cell: ({ row }) => <Pnl value={row.original.change} variant="percent" />,
      },
      {
        accessorKey: "volume",
        header: tm("volume"),
        sortFn: decimalSort,
        sortUndefined: "last",
        cell: ({ row }) => (
          <VolumeCompact
            value={row.original.volume}
            suffix={row.original.quote || undefined}
          />
        ),
      },
      {
        id: "favorite",
        header: tm("favorite"),
        cell: ({ row }) => <FavoriteStar symbol={row.original.symbol} />,
        enableSorting: false,
      },
    ],
    [tm],
  );

  function selectTab(next: Tab) {
    setTab(next);
    setPageIndex(0);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "USDT", label: tm("tabUsdt") },
    { id: "USDC", label: tm("tabUsdc") },
    { id: "BTC", label: tm("tabBtc") },
    { id: "FAV", label: tm("tabFavorites") },
  ];

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("market")}</h1>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div role="group" aria-label={t("market")} className="flex gap-1">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={tab === item.id}
              onClick={() => selectTab(item.id)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium",
                tab === item.id
                  ? "bg-accent/12 text-accent"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
        <input
          type="search"
          aria-label={tm("search")}
          placeholder={tm("search")}
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPageIndex(0);
          }}
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring sm:w-64"
        />
      </div>

      {symbolsQuery.isPending ? (
        <div className="flex flex-col gap-2" role="status" aria-label={tm("search")}>
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : symbolsQuery.isError ? (
        <p role="alert" className="text-sm text-loss">
          {tm("loadError")}
        </p>
      ) : entries.length === 0 ? (
        tab === "FAV" && query.trim() === "" ? (
          <EmptyState title={tm("noFavorites")} description={tm("noFavoritesHint")} />
        ) : (
          <EmptyState title={tm("noResults")} description={tm("noResultsHint")} />
        )
      ) : (
        <>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{tm("pairsCount", { count: entries.length })}</span>
            <span>{tm("sortedNote")}</span>
          </div>
          {tickers.isPending && tickers.data === undefined ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-64 w-full" />
            </div>
          ) : tickers.isError ? (
            <p role="alert" className="text-sm text-loss">
              {tm("loadError")}
            </p>
          ) : (
            <DataTable
              columns={columns}
              data={rows}
              emptyTitle={tm("noResults")}
              emptyDescription={tm("noResultsHint")}
              pageSize={PAGE_SIZE}
              onRowClick={(row) => router.push(`/market/${row.symbol}`)}
            />
          )}
          {pageCount <= 1 ? null : (
            <nav aria-label={tm("pages")} className="flex items-center justify-end gap-2 text-sm">
              <button
                type="button"
                onClick={() => setPageIndex(Math.max(0, safePage - 1))}
                disabled={safePage === 0}
                className={cn(
                  "rounded-md border border-input px-3 py-1.5",
                  safePage === 0 ? "opacity-50" : "hover:bg-muted",
                )}
              >
                {tm("previous")}
              </button>
              <span className="font-mono text-muted-foreground">
                {safePage + 1} {tm("of")} {pageCount}
              </span>
              <button
                type="button"
                onClick={() => setPageIndex(Math.min(pageCount - 1, safePage + 1))}
                disabled={safePage >= pageCount - 1}
                className={cn(
                  "rounded-md border border-input px-3 py-1.5",
                  safePage >= pageCount - 1 ? "opacity-50" : "hover:bg-muted",
                )}
              >
                {tm("next")}
              </button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
