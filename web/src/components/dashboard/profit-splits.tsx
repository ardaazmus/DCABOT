"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo } from "react";
import type { ReactNode } from "react";

import { Pnl } from "@/components/pnl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BotProfitRow, PairProfitRow } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";
import { divergingBars } from "@/lib/chart/bars";
import { paletteSnapshot, withAlpha } from "@/lib/chart/theme";
import { cn } from "@/lib/utils";

/**
 * Bot/parite kâr listeleri. Halka negatif kârı dürüst gösteremez;
 * bunun yerine büyüklük çubuklu sıralı liste kullanılır (yeşil/kırmızı
 * yönü, çubuk büyüklüğü oranlar; değer etiketi ham metindir).
 */
export function ProfitSplits({
  byBot,
  byPair,
}: {
  byBot: readonly BotProfitRow[];
  byPair: readonly PairProfitRow[];
}) {
  const t = useTranslations("dashboard");
  const palette = useMemo(() => paletteSnapshot(), []);
  const botBars = useMemo(() => divergingBars(byBot.map((row) => row.profit)), [byBot]);
  const pairBars = useMemo(() => divergingBars(byPair.map((row) => row.profit)), [byPair]);
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{t("byBotTitle")}</h2>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="flex flex-col gap-3">
            {byBot.map((row, index) => (
              <SplitRow
                key={row.bot_id}
                name={
                  <Link
                    href={`/bots/${encodeURIComponent(row.bot_id)}`}
                    className="font-medium hover:underline"
                  >
                    {row.bot_name}
                  </Link>
                }
                meta={t("dealsCount", { count: row.deals_completed })}
                profit={row.profit}
                bar={botBars[index]}
                palette={palette}
              />
            ))}
          </ol>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{t("byPairTitle")}</h2>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="flex flex-col gap-3">
            {byPair.map((row, index) => (
              <SplitRow
                key={row.symbol}
                name={<span className="font-mono font-medium">{row.symbol}</span>}
                meta={t("dealsBotsCount", { deals: row.deals_completed, bots: row.bots })}
                profit={row.profit}
                bar={pairBars[index]}
                palette={palette}
              />
            ))}
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}

function SplitRow({
  name,
  meta,
  profit,
  bar,
  palette,
}: {
  name: ReactNode;
  meta: string;
  profit: string;
  bar: { heightPct: number; positive: boolean } | null | undefined;
  palette: { profit: string; loss: string };
}) {
  const color = bar?.positive === true ? palette.profit : palette.loss;
  return (
    <li className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-2">
        <span className="min-w-0 truncate text-sm">
          {name} <span className="text-xs text-muted-foreground">· {meta}</span>
        </span>
        <Pnl
          variant="usdt"
          value={isDecimalString(profit) ? profit : undefined}
          suffix="USDT"
        />
      </div>
      <div className="h-1 w-full rounded-full bg-muted" aria-hidden="true">
        {bar === null || bar === undefined || bar.heightPct === 0 ? null : (
          <div
            className={cn("h-1 rounded-full")}
            style={{ width: `${bar.heightPct.toFixed(1)}%`, backgroundColor: withAlpha(color, 0.85) }}
          />
        )}
      </div>
    </li>
  );
}
