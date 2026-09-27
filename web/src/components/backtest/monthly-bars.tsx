"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BacktestResult } from "@/lib/api/schemas";
import { divergingBars } from "@/lib/chart/bars";
import { paletteSnapshot, withAlpha } from "@/lib/chart/theme";
import { formatDecimal, isDecimalString } from "@/lib/decimal";
import { formatMonthLabel } from "@/lib/format-time";
import { cn } from "@/lib/utils";

type MonthlyRow = BacktestResult["monthly_returns"][number];

/**
 * Aylık getiri çubukları (ıraksak): artı yukarı yeşil, eksi aşağı
 * kırmızı. Kısmi aylar soluk + "kısmi" etiketi. Yükseklikler yalnız
 * piksel içindir (`lib/chart/bars`); değer etiketi ham metindir.
 */
export function MonthlyBars({ rows }: { rows: readonly MonthlyRow[] }) {
  const t = useTranslations("backtest");
  const locale = useLocale() === "en" ? "en" : "tr";
  const palette = useMemo(() => paletteSnapshot(), []);
  const layout = useMemo(
    () => divergingBars(rows.map((row) => row.return_percent)),
    [rows],
  );
  if (rows.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("monthlyTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="flex h-40 items-stretch gap-1" aria-label={t("monthlyTitle")}>
          {rows.map((row, index) => {
            const bar = layout[index];
            const color = bar?.positive === true ? palette.profit : palette.loss;
            return (
              <li key={row.month} className="flex min-w-0 flex-1 flex-col items-center gap-1">
                <div className="relative flex h-28 w-full items-center" aria-hidden="true">
                  <div className="absolute inset-x-0 top-1/2 h-px bg-border" />
                  {bar === null || bar === undefined ? null : (
                    <div
                      className={cn("absolute left-1/2 w-8 max-w-full -translate-x-1/2 rounded-sm")}
                      style={{
                        backgroundColor: row.complete ? color : withAlpha(color, 0.4),
                        height: `${(bar.heightPct / 2).toFixed(1)}%`,
                        ...(bar.positive ? { bottom: "50%" } : { top: "50%" }),
                      }}
                    />
                  )}
                </div>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {formatMonthLabel(row.month, locale)}
                </span>
                <span
                  className={cn(
                    "font-mono text-[10px]",
                    bar?.positive === true ? "text-profit" : "text-loss",
                  )}
                  title={row.return_percent}
                >
                  %
                  {isDecimalString(row.return_percent)
                    ? formatDecimal(row.return_percent, { locale, maxFractionDigits: 2 })
                    : row.return_percent}
                </span>
                {row.complete ? null : (
                  <span className="rounded bg-muted px-1 text-[10px] text-muted-foreground">
                    {t("partial")}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
