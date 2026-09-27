"use client";

import { useLocale, useTranslations } from "next-intl";
import { useMemo } from "react";

import { Pnl } from "@/components/pnl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DailyProfit } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";
import { divergingBars } from "@/lib/chart/bars";
import { paletteSnapshot, withAlpha } from "@/lib/chart/theme";
import { formatDayLabel } from "@/lib/format-time";
import { cn } from "@/lib/utils";

/**
 * Günlük gerçekleşmiş kâr çubukları (ıraksak): artı yukarı yeşil,
 * eksi aşağı kırmızı. Etiketler 30 çubukta okunurluk için seyreltilir
 * (her 5 günde bir + son gün); değer yalnız sıfır olmayanda yazılır,
 * ham metin her çubukta ipucundadır.
 */
export function DailyBars({ rows }: { rows: readonly DailyProfit[] }) {
  const t = useTranslations("dashboard");
  const locale = useLocale() === "en" ? "en" : "tr";
  const palette = useMemo(() => paletteSnapshot(), []);
  const layout = useMemo(() => divergingBars(rows.map((row) => row.profit)), [rows]);
  if (rows.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("dailyTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="flex h-44 items-stretch gap-1" aria-label={t("dailyTitle")}>
          {rows.map((row, index) => {
            const bar = layout[index];
            const color = bar?.positive === true ? palette.profit : palette.loss;
            const showLabel = index % 5 === 0 || index === rows.length - 1;
            return (
              <li
                key={row.day_start_us}
                className="flex min-w-0 flex-1 flex-col items-center gap-1"
                title={row.profit}
              >
                <div className="relative flex h-28 w-full items-center" aria-hidden="true">
                  <div className="absolute inset-x-0 top-1/2 h-px bg-border" />
                  {bar === null || bar === undefined ? null : (
                    <div
                      className={cn("absolute left-1/2 w-4 max-w-full -translate-x-1/2 rounded-sm")}
                      style={{
                        backgroundColor: withAlpha(color, 0.85),
                        height: `${(bar.heightPct / 2).toFixed(1)}%`,
                        ...(bar.positive ? { bottom: "50%" } : { top: "50%" }),
                      }}
                    />
                  )}
                </div>
                <span className="font-mono text-[10px] text-muted-foreground">
                  {showLabel ? formatDayLabel(row.day_start_us, locale) : " "}
                </span>
                <span className="font-mono text-[10px]">
                  {row.profit === "0" ? (
                    " "
                  ) : (
                    <Pnl
                      variant="usdt"
                      value={isDecimalString(row.profit) ? row.profit : undefined}
                    />
                  )}
                </span>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
