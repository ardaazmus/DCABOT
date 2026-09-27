"use client";

import { useLocale, useTranslations } from "next-intl";

import { StatusBadge } from "@/components/status-badge";
import type { BacktestResult } from "@/lib/api/schemas";
import { formatEventTime } from "@/lib/format-time";

/**
 * Durum bandı: INDETERMINATE amber uyarısı + veri kaynağı rozeti.
 * COMPLETED durumunda yalnız kaynak rozeti gösterilir.
 */
export function StatusBand({ result }: { result: BacktestResult }) {
  const t = useTranslations("backtest");
  const locale = useLocale();
  const indeterminate = result.status === "INDETERMINATE";
  return (
    <div className="flex flex-col gap-2" data-testid="backtest-status">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge variant={result.data_source === "CACHE" ? "paper" : "live"}>
          {t(result.data_source === "CACHE" ? "sourceCache" : "sourceVenue")}
        </StatusBadge>
        <span className="font-mono text-xs text-muted-foreground">
          {t("processedBars", {
            done: result.processed_bar_count,
            total: result.bar_count,
          })}
        </span>
      </div>
      {indeterminate && result.indeterminate_at_us !== null ? (
        <p role="alert" className="rounded-md bg-safety/15 px-3 py-2 text-sm font-medium text-safety">
          {t("indeterminate", {
            date: formatEventTime(result.indeterminate_at_us, locale),
          })}
        </p>
      ) : null}
    </div>
  );
}
