"use client";

import { useTranslations } from "next-intl";

import { NeutralPercent, Price, Qty } from "@/components/money";
import type { DealPlan } from "@/lib/api/schemas";
import { isDecimalString, type DecimalString } from "@/lib/decimal";

function toDecimal(text: string): DecimalString | undefined {
  return isDecimalString(text) ? text : undefined;
}

/**
 * Önizleme emir tablosu: base + SO1..n; her değer backend metnidir.
 * Fiyatlar tick, miktarlar qty_step basamağıyla kısaltılır; tam metin
 * ipucundadır. Sapma kâr/zarar değildir: nötr, işaretsiz gösterilir.
 */
export function OrderTable({
  plan,
  priceDecimals = 2,
  qtyDecimals = 8,
}: {
  plan: DealPlan;
  priceDecimals?: number;
  qtyDecimals?: number;
}) {
  const t = useTranslations("wizard");
  const rows = [
    {
      level: t("baseRow"),
      price: plan.base_order.price,
      qty: plan.base_order.qty,
      amount: plan.base_order.amount,
      deviation: null as string | null,
    },
    ...plan.safety_orders.map((order) => ({
      level: `SO${order.index}`,
      price: order.price,
      qty: order.qty,
      amount: order.amount,
      deviation: order.deviation_percent,
    })),
  ];
  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50 text-left">
            <th scope="col" className="px-3 py-2 font-medium text-muted-foreground">
              {t("colLevel")}
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium text-muted-foreground">
              {t("colPrice")}
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium text-muted-foreground">
              {t("colQty")}
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium text-muted-foreground">
              {t("colAmount")}
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium text-muted-foreground">
              {t("colDeviation")}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.level} className="border-b border-border last:border-0">
              <td className="px-3 py-2 font-mono">{row.level}</td>
              <td className="px-3 py-2 text-right">
                <Price
                  value={toDecimal(row.price)}
                  options={{ maxFractionDigits: priceDecimals }}
                  title={row.price}
                />
              </td>
              <td className="px-3 py-2 text-right">
                <Qty
                  value={toDecimal(row.qty)}
                  options={{ maxFractionDigits: qtyDecimals }}
                  title={row.qty}
                />
              </td>
              <td className="px-3 py-2 text-right">
                <Price
                  value={toDecimal(row.amount)}
                  options={{ maxFractionDigits: 2 }}
                  title={row.amount}
                />
              </td>
              <td className="px-3 py-2 text-right">
                {row.deviation === null ? (
                  <span className="font-mono text-muted-foreground">—</span>
                ) : (
                  <NeutralPercent value={toDecimal(row.deviation)} title={row.deviation} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
