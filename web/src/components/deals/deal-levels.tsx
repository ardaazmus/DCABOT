"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Money, Price, Qty } from "@/components/money";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DealDetail } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";

/** Seviye kartı: bütün değerler backend metnidir, hesap yok. */
export function DealLevels({ deal }: { deal: DealDetail }) {
  const t = useTranslations("deals");
  const money = (value: string | null, suffix: string) => (
    <Money value={isDecimalString(value) ? value : undefined} suffix={suffix} />
  );
  const rows: [string, ReactNode][] = [
    [t("averageRow"), <Price key="a" value={isDecimalString(deal.average_price) ? deal.average_price : undefined} suffix="USDT" />],
    [t("markRow"), <Price key="m" value={isDecimalString(deal.mark_price) ? deal.mark_price : undefined} suffix="USDT" />],
    [t("tpRow"), <Price key="t" value={isDecimalString(deal.take_profit_price) ? deal.take_profit_price : undefined} suffix="USDT" />],
    [t("nextSoRow"), <Price key="s" value={isDecimalString(deal.next_safety_order_price) ? deal.next_safety_order_price : undefined} suffix="USDT" />],
    [t("costRow"), <span key="c">{money(deal.cost, "USDT")}</span>],
    [t("qtyRow"), <Qty key="q" value={isDecimalString(deal.qty) ? deal.qty : undefined} />],
    [t("grossRow"), <span key="g">{money(deal.gross_profit, "USDT")}</span>],
    [t("feesRow"), <span key="f">{money(deal.fees, "USDT")}</span>],
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("levelsTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="flex flex-col gap-2 text-sm">
          {rows.map(([label, value]) => (
            <div key={label} className="flex justify-between gap-4">
              <dt className="text-muted-foreground">{label}</dt>
              <dd className="font-mono">{value}</dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
