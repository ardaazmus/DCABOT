"use client";

import { useTranslations } from "next-intl";

import { OrderTable } from "@/components/bots/order-table";
import { PlanChart } from "@/components/bots/plan-chart";
import { Money, NeutralPercent, Price } from "@/components/money";
import { Skeleton } from "@/components/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSymbolRules } from "@/lib/api/queries";
import type { DealPlan } from "@/lib/api/schemas";
import { isDecimalString, type DecimalString } from "@/lib/decimal";
import { decimalsFromStep } from "@/lib/precision";
import { cn } from "@/lib/utils";

function toDecimal(text: string | null | undefined): DecimalString | undefined {
  return text !== null && text !== undefined && isDecimalString(text) ? text : undefined;
}

/**
 * Canlı önizleme paneli: kartlar + emir tablosu + seviye grafiği.
 * Sihirbazda yapışkan panel, detayda "Güncel plan" kartı olarak kullanılır.
 */
export function PreviewPanel({
  symbol,
  plan,
  budget,
  state,
  errorText,
  showChart = true,
  title,
  note,
  comboTakeProfit,
}: {
  symbol: string;
  plan: DealPlan | null;
  budget: string;
  state: "waiting" | "loading" | "error" | "ready";
  errorText?: string;
  showChart?: boolean;
  /** Verilmezse sihirbaz başlığı kullanılır (detay kendi başlığını verir). */
  title?: string;
  note?: string;
  /** Birleşik TP hedefi (% metin); null = kapalı, deal TP geçerli. */
  comboTakeProfit?: string | null;
}) {
  const t = useTranslations("wizard");
  const rules = useSymbolRules(symbol);
  // Kurallar yokken (çevrimdışı) son çare 2/8 basamaktır.
  const priceDecimals = rules.data ? decimalsFromStep(rules.data.data.tick) : 2;
  const qtyDecimals = rules.data ? decimalsFromStep(rules.data.data.qty_step) : 8;
  return (
    <div className="flex flex-col gap-4" data-testid="preview-panel">
      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{title ?? t("previewTitle")}</h2>
          </CardTitle>
          {note === undefined ? null : (
            <p className="text-xs text-muted-foreground">{note}</p>
          )}
          {comboTakeProfit === null || comboTakeProfit === undefined ? null : (
            <p className="text-xs font-medium text-muted-foreground">{t("comboPreviewNote", { pct: comboTakeProfit })}</p>
          )}
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {state === "waiting" ? (
            <p className="text-sm text-muted-foreground">{t("previewWaiting")}</p>
          ) : state === "loading" ? (
            <div className="flex flex-col gap-2" role="status" aria-label={t("previewLoading")}>
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : state === "error" ? (
            <p role="alert" className="text-sm text-loss">
              {errorText ?? ""}
            </p>
          ) : plan === null ? null : (
            <>
              <dl className="grid grid-cols-1 gap-2 text-sm min-[420px]:grid-cols-2">
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">{t("ordersTotal")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Money
                      value={toDecimal(plan.orders_total)}
                      suffix="USDT"
                      options={{ maxFractionDigits: 2 }}
                      title={plan.orders_total}
                    />
                  </dd>
                </div>
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">{t("estimatedFees")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Money
                      value={toDecimal(plan.estimated_fees)}
                      suffix="USDT"
                      options={{ maxFractionDigits: 2 }}
                      title={plan.estimated_fees}
                    />
                  </dd>
                </div>
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">{t("requiredFunds")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Money
                      value={toDecimal(plan.required_funds)}
                      suffix="USDT"
                      options={{ maxFractionDigits: 2 }}
                      title={plan.required_funds}
                    />
                  </dd>
                  <dd className="font-mono text-xs text-muted-foreground">
                    <Money
                      value={toDecimal(budget)}
                      suffix="USDT"
                      options={{ maxFractionDigits: 2 }}
                      title={budget}
                    />
                  </dd>
                </div>
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">{t("coverage")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <NeutralPercent
                      value={toDecimal(plan.price_coverage_percent)}
                      title={plan.price_coverage_percent}
                    />
                  </dd>
                </div>
                <div className="rounded-lg bg-muted/50 px-3 py-2 min-[420px]:col-span-2">
                  <dt className="text-xs text-muted-foreground">{t("average")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Price
                      value={toDecimal(plan.average_price_all_filled)}
                      options={{ maxFractionDigits: priceDecimals }}
                      title={plan.average_price_all_filled}
                    />
                  </dd>
                </div>
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">{t("tpPrice")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Price
                      value={toDecimal(plan.take_profit_price)}
                      options={{ maxFractionDigits: priceDecimals }}
                      title={plan.take_profit_price ?? undefined}
                    />
                  </dd>
                </div>
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">{t("slPrice")}</dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Price
                      value={toDecimal(plan.stop_loss_price_initial)}
                      options={{ maxFractionDigits: priceDecimals }}
                      title={plan.stop_loss_price_initial ?? undefined}
                    />
                  </dd>
                </div>
              </dl>
              {plan.within_budget ? null : (
                <p
                  role="alert"
                  className={cn(
                    "rounded-md bg-safety/15 px-3 py-2 text-sm font-medium text-safety",
                  )}
                >
                  {t("budgetWarning")}
                </p>
              )}
              {plan.symbols === null || plan.total_required_funds === null ? null : (
                <div className="rounded-lg bg-muted/50 px-3 py-2">
                  <dt className="text-xs text-muted-foreground">
                    {t("totalRequiredFunds")} ({plan.symbols.join(", ")})
                  </dt>
                  <dd className="break-all font-mono text-sm font-semibold">
                    <Money
                      value={toDecimal(plan.total_required_funds)}
                      suffix="USDT"
                      options={{ maxFractionDigits: 2 }}
                      title={plan.total_required_funds}
                    />
                  </dd>
                </div>
              )}
              {plan.within_total_budget === false ? (
                <p
                  role="alert"
                  className={cn(
                    "rounded-md bg-safety/15 px-3 py-2 text-sm font-medium text-safety",
                  )}
                >
                  {t("totalBudgetWarning")}
                </p>
              ) : null}
              <div>
                <h3 className="mb-2 text-sm font-semibold">{t("ordersTitle")}</h3>
                <OrderTable plan={plan} priceDecimals={priceDecimals} qtyDecimals={qtyDecimals} />
              </div>
            </>
          )}
        </CardContent>
      </Card>
      {showChart && state === "ready" && plan !== null ? (
        <PlanChart symbol={symbol} plan={plan} />
      ) : null}
    </div>
  );
}
