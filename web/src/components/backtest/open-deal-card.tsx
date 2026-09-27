"use client";

import { useTranslations } from "next-intl";

import { Money, Qty } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BacktestResult } from "@/lib/api/schemas";
import { isDecimalString, type DecimalString } from "@/lib/decimal";

type OpenDeal = NonNullable<BacktestResult["open_deal"]>;

function toDecimal(text: string): DecimalString | undefined {
  return isDecimalString(text) ? text : undefined;
}

/** Açık deal kartı; deal yoksa gösterilmez. */
export function OpenDealCard({ openDeal }: { openDeal: OpenDeal | null }) {
  const t = useTranslations("backtest");
  if (openDeal === null) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("openDealTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-1 gap-2 text-sm min-[420px]:grid-cols-3">
          <div className="rounded-lg bg-muted/50 px-3 py-2">
            <dt className="text-xs text-muted-foreground">{t("unrealized")}</dt>
            <dd className="font-mono text-sm font-semibold">
              <Pnl value={toDecimal(openDeal.unrealized)} suffix="USDT" title={openDeal.unrealized} />
            </dd>
          </div>
          <div className="rounded-lg bg-muted/50 px-3 py-2">
            <dt className="text-xs text-muted-foreground">{t("cost")}</dt>
            <dd className="font-mono text-sm font-semibold">
              <Money
                value={toDecimal(openDeal.cost)}
                suffix="USDT"
                options={{ maxFractionDigits: 2 }}
                title={openDeal.cost}
              />
            </dd>
          </div>
          <div className="rounded-lg bg-muted/50 px-3 py-2">
            <dt className="text-xs text-muted-foreground">{t("qty")}</dt>
            <dd className="font-mono text-sm font-semibold">
              <Qty value={toDecimal(openDeal.qty)} title={openDeal.qty} />
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
