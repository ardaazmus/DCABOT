import type { HistogramData, LineData, Time } from "lightweight-charts";

export type IndexedPoint = { index: number };

/**
 * İndikatör noktalarını çizgi parçalarına çevirir. `null` / eksik / sonlu
 * olmayan nokta 0 uydurulmaz — parça orada bölünür ve grafik boşluk
 * bırakır. Nokta `index`'i kapanış listesindeki konumdur; `times`
 * dizisi aynı sıradaki mum zamanlarını verir.
 */
export function pointsToSegments<TPoint extends IndexedPoint>(
  points: readonly TPoint[],
  pick: (point: TPoint) => string | null | undefined,
  times: readonly Time[],
): LineData<Time>[][] {
  const segments: LineData<Time>[][] = [];
  let current: LineData<Time>[] = [];
  for (const point of points) {
    const text = pick(point);
    const time = times[point.index];
    const value = text === null || text === undefined ? NaN : Number(text);
    if (time === undefined || !Number.isFinite(value)) {
      if (current.length > 0) {
        segments.push(current);
        current = [];
      }
      continue;
    }
    current.push({ time, value });
  }
  if (current.length > 0) segments.push(current);
  return segments;
}

/**
 * Yatay seviye çizgisi (bot planı: giriş, SO, ortalama, TP, SL).
 * Değer backend metnidir; sonlu sayıya dönüşmezse çizgi çizilmez.
 */
export function levelToSegments(
  valueText: string | null | undefined,
  times: readonly Time[],
): LineData<Time>[][] {
  if (valueText === null || valueText === undefined) return [];
  const value = Number(valueText);
  if (!Number.isFinite(value) || times.length === 0) return [];
  return [times.map((time) => ({ time, value }))];
}

const ZERO_PATTERN = /^-?0*(\.0*)?$/;

function signColor(
  text: string,
  colors: { up: string; down: string; neutral: string },
): string {
  if (ZERO_PATTERN.test(text)) return colors.neutral;
  return text.startsWith("-") ? colors.down : colors.up;
}

/**
 * MACD histogram çubukları. Renk metnin işaretinden okunur (hesap yok);
 * `null` noktalar atlanır.
 */
export function pointsToHistogram<TPoint extends IndexedPoint>(
  points: readonly TPoint[],
  pick: (point: TPoint) => string | null | undefined,
  times: readonly Time[],
  colors: { up: string; down: string; neutral: string },
): HistogramData<Time>[] {
  const bars: HistogramData<Time>[] = [];
  for (const point of points) {
    const text = pick(point);
    const time = times[point.index];
    const value = text === null || text === undefined ? NaN : Number(text);
    if (time === undefined || !Number.isFinite(value) || text === null || text === undefined) {
      continue;
    }
    bars.push({ time, value, color: signColor(text, colors) });
  }
  return bars;
}
