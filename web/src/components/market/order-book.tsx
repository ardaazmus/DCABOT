"use client";

import { useTranslations } from "next-intl";

import { Money, Price } from "@/components/money";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Depth } from "@/lib/api/schemas";
import { isDecimalString, type DecimalString } from "@/lib/decimal";

function toDecimal(text: string): DecimalString | undefined {
  return isDecimalString(text) ? text : undefined;
}

function Side({
  title,
  rows,
  priceClass,
  testId,
}: {
  title: string;
  rows: readonly (readonly [string, string])[];
  priceClass: string;
  testId: string;
}) {
  const t = useTranslations("symbol");
  return (
    <div className="flex min-w-0 flex-1 flex-col gap-1">
      <h3 className="text-sm font-semibold">{title}</h3>
      <table className="w-full text-sm" data-testid={testId}>
        <thead>
          <tr className="text-muted-foreground">
            <th scope="col" className="py-1 pr-2 text-left font-medium">
              {t("depthPrice")}
            </th>
            <th scope="col" className="py-1 text-right font-medium">
              {t("depthQty")}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([price, qty]) => (
            <tr key={`${price}-${qty}`} className="border-t border-border/50">
              <td className={`py-1 pr-2 ${priceClass}`}>
                <Price value={toDecimal(price)} />
              </td>
              <td className="py-1 text-right">
                <Money value={toDecimal(qty)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function OrderBook({
  depth,
  paused,
  onTogglePause,
}: {
  depth: Depth;
  paused: boolean;
  onTogglePause: () => void;
}) {
  const t = useTranslations("symbol");
  // Satışlar yüksekten düşüğe; en iyi satış spread'e en yakın satırdadır.
  const asks = [...depth.data.asks].reverse();
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle>{t("depth")}</CardTitle>
        <button
          type="button"
          aria-pressed={paused}
          onClick={onTogglePause}
          className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted"
        >
          {paused ? t("resume") : t("pause")}
        </button>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {paused ? (
          <p className="text-sm text-muted-foreground">{t("pausedNote")}</p>
        ) : null}
        <div className="flex flex-col gap-4 sm:flex-row">
          <Side title={t("asks")} rows={asks} priceClass="text-loss" testId="depth-asks" />
          <Side title={t("bids")} rows={depth.data.bids} priceClass="text-profit" testId="depth-bids" />
        </div>
      </CardContent>
    </Card>
  );
}
