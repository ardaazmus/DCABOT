import type { CandlestickData, Time, UTCTimestamp } from "lightweight-charts";

import type { KlineBar } from "@/lib/api/schemas";

export type Candle = CandlestickData<Time>;

/**
 * Backend mumlarını grafik mumlarına çevirir. `Number()` bu dizinin
 * dışında yasaktır; metin → sayı dönüşümü yalnız burada ve yalnız
 * piksel hesabı içindir. Sonlu sayıya dönüşmeyen mum çizilmez
 * (uydurma nokta yok).
 */
export function barsToCandles(bars: readonly KlineBar[]): Candle[] {
  const candles: Candle[] = [];
  for (const bar of bars) {
    const open = Number(bar.open);
    const high = Number(bar.high);
    const low = Number(bar.low);
    const close = Number(bar.close);
    if (
      !Number.isFinite(open) ||
      !Number.isFinite(high) ||
      !Number.isFinite(low) ||
      !Number.isFinite(close)
    ) {
      continue;
    }
    candles.push({
      time: microsToTimestamp(bar.open_time_us),
      open,
      high,
      low,
      close,
    });
  }
  return candles;
}

/** `open_time_us` → grafik saniyesi (UTC). */
export function microsToTimestamp(openTimeUs: number): UTCTimestamp {
  return Math.floor(openTimeUs / 1_000_000) as UTCTimestamp;
}
