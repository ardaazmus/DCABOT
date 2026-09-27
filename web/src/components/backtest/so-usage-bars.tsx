"use client";

import { useTranslations } from "next-intl";
import { useMemo } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BacktestResult } from "@/lib/api/schemas";
import { countBars } from "@/lib/chart/bars";
import { paletteSnapshot } from "@/lib/chart/theme";

type UsageRow = BacktestResult["safety_order_usage"][number];

/**
 * SO kullanım dağılımı: x = dolan SO sayısı, y = deal sayısı.
 * Yükseklikler yalnız pikseldir; sayı etiketi ham yanıttır.
 */
export function SoUsageBars({ rows }: { rows: readonly UsageRow[] }) {
  const t = useTranslations("backtest");
  const palette = useMemo(() => paletteSnapshot(), []);
  const heights = useMemo(() => countBars(rows.map((row) => row.deals)), [rows]);
  if (rows.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("soUsageTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="flex h-40 items-stretch gap-2" aria-label={t("soUsageTitle")}>
          {rows.map((row, index) => (
            <li key={row.safety_orders_filled} className="flex min-w-0 flex-1 flex-col items-center justify-end gap-1">
              <span className="font-mono text-xs">{row.deals}</span>
              <div
                className="w-full max-w-12 rounded-t"
                aria-hidden="true"
                style={{
                  backgroundColor: palette.accent,
                  height: `${(heights[index] ?? 0).toFixed(1)}%`,
                  minHeight: row.deals > 0 ? 4 : 0,
                }}
              />
              <span className="font-mono text-[10px] text-muted-foreground">
                SO{row.safety_orders_filled}
              </span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
