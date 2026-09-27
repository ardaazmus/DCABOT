"use client";

import { useTranslations } from "next-intl";
import { useMemo } from "react";

import { ChartCard } from "@/components/chart-card";
import { PriceChart, type ChartOverlay } from "@/components/market/price-chart";
import { useKlines } from "@/lib/api/queries";
import type { DealPlan } from "@/lib/api/schemas";
import { levelToSegments } from "@/lib/chart/indicators";
import { barsToCandles, microsToTimestamp } from "@/lib/chart/klines";

const PLAN_KLINES_LIMIT = 150;

/**
 * Canlı mum grafiği üzerindeki plan seviyeleri. Çizgi değerleri yalnız
 * önizleme yanıtından gelir; istemci seviye hesaplamaz.
 */
export function PlanChart({
  symbol,
  plan,
  testId = "plan-chart",
}: {
  symbol: string;
  plan: DealPlan | null;
  testId?: string;
}) {
  const t = useTranslations("wizard");
  const klines = useKlines(symbol, "1h", PLAN_KLINES_LIMIT);

  const bars = useMemo(() => klines.data?.data.bars ?? [], [klines.data]);
  const candles = useMemo(() => barsToCandles(bars), [bars]);
  const times = useMemo(
    () => bars.map((bar) => microsToTimestamp(bar.open_time_us)),
    [bars],
  );

  const overlays: ChartOverlay[] = useMemo(() => {
    if (plan === null) return [];
    const list: ChartOverlay[] = [
      {
        id: "base",
        color: "entry",
        segments: levelToSegments(plan.base_order.price, times),
      },
      ...plan.safety_orders.map((order) => ({
        id: `so-${order.index}`,
        color: "safety" as const,
        dashed: true,
        segments: levelToSegments(order.price, times),
      })),
      {
        id: "average",
        color: "entry",
        dotted: true,
        segments: levelToSegments(plan.average_price_all_filled, times),
      },
    ];
    if (plan.take_profit_price !== null) {
      list.push({
        id: "tp",
        color: "profit",
        segments: levelToSegments(plan.take_profit_price, times),
      });
    }
    if (plan.stop_loss_price_initial !== null) {
      list.push({
        id: "sl",
        color: "loss",
        segments: levelToSegments(plan.stop_loss_price_initial, times),
      });
    }
    return list.filter((overlay) => overlay.segments.length > 0);
  }, [plan, times]);

  return (
    <ChartCard
      title={t("chartTitle")}
      state={klines.isPending ? "loading" : klines.isError ? "error" : "ready"}
    >
      <PriceChart candles={candles} overlays={overlays} height={280} label={t("chartTitle")} testId={testId} />
    </ChartCard>
  );
}
