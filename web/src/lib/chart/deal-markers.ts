import type { SeriesMarker, Time } from "lightweight-charts";

import type { BotEvent } from "@/lib/api/schemas";
import { isDecimalString, parseDecimal, signOf } from "@/lib/decimal";

import { microsToTimestamp } from "./klines";

export type MarkerPalette = { profit: string; loss: string };

/**
 * Dolum işaretleri: alışlar mum altı yeşil, satış mum üstü kırmızı.
 * İptal satışı çizilmez (satış olmadı). Olay zamanları grafik
 * aralığına yuvarlanır (yalnız görüntüleme); mum kümesinde karşılığı
 * olmayan işaret atılır — bilinmeyen zaman çizilmez.
 */
export function dealMarkers(
  events: readonly BotEvent[],
  intervalUs: number,
  candleTimes: ReadonlySet<Time>,
  palette: MarkerPalette,
): SeriesMarker<Time>[] {
  const markers: SeriesMarker<Time>[] = [];
  for (const event of events) {
    const bucket = Math.floor(event.time_us / intervalUs) * intervalUs;
    const time = microsToTimestamp(bucket);
    if (!candleTimes.has(time)) continue;
    if (
      event.kind === "DEAL_STARTED" ||
      event.kind === "SAFETY_ORDER_FILLED" ||
      event.kind === "MANUAL_ORDER_FILLED"
    ) {
      markers.push({ time, position: "belowBar", shape: "arrowUp", color: palette.profit });
    } else if (event.kind === "DEAL_CLOSED" && event.detail.reason !== "CANCELLED") {
      markers.push({ time, position: "aboveBar", shape: "arrowDown", color: palette.loss });
    }
  }
  return markers.sort((a, b) => (a.time as number) - (b.time as number));
}

export type BacktestDealMarkerInput = {
  readonly started_at_us: number | null;
  readonly closed_at_us: number | null;
  readonly profit: string | null;
};

/**
 * Backtest işlem işaretleri: giriş mum altı yeşil, çıkış mum üstü
 * (kârlıysa yeşil, değilse kırmızı). Zamanlar fiyat eğrisinin
 * kendi bar açılışlarıyla birebir eşleşir; eğride karşılığı
 * olmayan işaret atılır — bilinmeyen zaman çizilmez.
 */
export function backtestDealMarkers(
  deals: readonly BacktestDealMarkerInput[],
  candleTimes: ReadonlySet<Time>,
  palette: MarkerPalette,
): SeriesMarker<Time>[] {
  const markers: SeriesMarker<Time>[] = [];
  for (const deal of deals) {
    if (deal.started_at_us !== null) {
      const time = microsToTimestamp(deal.started_at_us);
      if (candleTimes.has(time)) {
        markers.push({ time, position: "belowBar", shape: "arrowUp", color: palette.profit });
      }
    }
    if (deal.closed_at_us !== null) {
      const time = microsToTimestamp(deal.closed_at_us);
      if (!candleTimes.has(time)) continue;
      const won =
        deal.profit !== null && isDecimalString(deal.profit) && signOf(parseDecimal(deal.profit)) > 0;
      markers.push({
        time,
        position: "aboveBar",
        shape: "arrowDown",
        color: won ? palette.profit : palette.loss,
      });
    }
  }
  return markers.sort((a, b) => (a.time as number) - (b.time as number));
}
