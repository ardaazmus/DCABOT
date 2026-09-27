"use client";

import type { Time } from "lightweight-charts";
import { useTranslations } from "next-intl";
import { useMemo } from "react";

import { ChartCard } from "@/components/chart-card";
import { PriceChart, type ChartOverlay } from "@/components/market/price-chart";
import { useKlines } from "@/lib/api/queries";
import type { DealDetail } from "@/lib/api/schemas";
import { dealMarkers } from "@/lib/chart/deal-markers";
import { levelToSegments } from "@/lib/chart/indicators";
import { barsToCandles, microsToTimestamp } from "@/lib/chart/klines";
import { readPalette } from "@/lib/chart/theme";

const DEAL_KLINES_LIMIT = 150;
const DEAL_INTERVAL_US = 15 * 60 * 1_000_000;

/**
 * Deal grafiği: 15 dakikalık mumlar, ortalama/TP/sonraki-SO
 * seviyeleri ve dolum işaretleri. Çizgi değerleri yalnız detay
 * yanıtından gelir; istemci seviye hesaplamaz.
 */
export function DealChart({
  deal,
  testId = "deal-chart",
}: {
  deal: DealDetail;
  testId?: string;
}) {
  const t = useTranslations("deals");
  const klines = useKlines(deal.symbol, "15m", DEAL_KLINES_LIMIT);

  const bars = useMemo(() => klines.data?.data.bars ?? [], [klines.data]);
  const candles = useMemo(() => barsToCandles(bars), [bars]);
  const times = useMemo(
    () => bars.map((bar) => microsToTimestamp(bar.open_time_us)),
    [bars],
  );

  const overlays: ChartOverlay[] = useMemo(() => {
    const list: ChartOverlay[] = [
      {
        id: "average",
        color: "entry",
        dotted: true,
        segments: levelToSegments(deal.average_price, times),
      },
      {
        id: "tp",
        color: "profit",
        segments: levelToSegments(deal.take_profit_price, times),
      },
      {
        id: "next-so",
        color: "safety",
        dashed: true,
        segments: levelToSegments(deal.next_safety_order_price, times),
      },
    ];
    return list.filter((overlay) => overlay.segments.length > 0);
  }, [deal.average_price, deal.take_profit_price, deal.next_safety_order_price, times]);

  const markers = useMemo(() => {
    const palette = readPalette();
    const candleTimes = new Set<Time>(times);
    return dealMarkers(deal.events, DEAL_INTERVAL_US, candleTimes, {
      profit: palette.profit,
      loss: palette.loss,
    });
  }, [deal.events, times]);

  return (
    <ChartCard
      title={t("chartTitle")}
      state={klines.isPending ? "loading" : klines.isError ? "error" : "ready"}
    >
      <PriceChart
        candles={candles}
        overlays={overlays}
        markers={markers}
        height={280}
        label={t("chartTitle")}
        testId={testId}
      />
    </ChartCard>
  );
}
