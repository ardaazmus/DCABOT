import type { Time } from "lightweight-charts";

import { microsToTimestamp } from "./klines";

export type SamplePoint = { time: Time; value: number };

/**
 * Backend ondalık metnini çizim sayısına çevirir. Sonlu değilse
 * `null` (çizgi çizilmez). Yalnız piksel içindir.
 */
export function textToNumber(text: string | null | undefined): number | null {
  if (text === null || text === undefined) return null;
  const value = Number(text);
  return Number.isFinite(value) ? value : null;
}

/**
 * Backend eğri noktalarını grafik örneklerine çevirir. Sonlu sayıya
 * dönüşmeyen nokta atlanır (uydurma yok). `negate` yalnız gösterim
 * yönünü çevirir (drawdown sualtı çizilir).
 */
export function textCurveToSamples<T>(
  points: readonly T[],
  timeUs: (point: T) => number,
  valueText: (point: T) => string | null | undefined,
  options?: { negate?: boolean },
): SamplePoint[] {
  const samples: SamplePoint[] = [];
  for (const point of points) {
    const text = valueText(point);
    const value = text === null || text === undefined ? NaN : Number(text);
    if (!Number.isFinite(value)) continue;
    samples.push({
      time: microsToTimestamp(timeUs(point)),
      value: options?.negate === true ? -value : value,
    });
  }
  return samples;
}

/**
 * Uzun seriler için min/maks koruyan seyreltme (yalnız görüntü).
 * İlk ve son nokta her zaman korunur; her kovanın en küçük ve en
 * büyük değeri alınır, böylece tepeler ve dipler kaybolmaz.
 * Kartlar ve tablolar bu çıktıdan beslenmez.
 */
export function downsampleMinMax(
  points: readonly SamplePoint[],
  maxPoints: number,
): SamplePoint[] {
  if (points.length <= maxPoints || maxPoints < 3) return [...points];
  const first = points[0];
  const last = points[points.length - 1];
  if (first === undefined || last === undefined) return [];
  const buckets = Math.max(1, Math.ceil((maxPoints - 2) / 2));
  const inner = points.slice(1, -1);
  const kept: SamplePoint[] = [first];
  for (let bucket = 0; bucket < buckets; bucket++) {
    const start = Math.floor((bucket * inner.length) / buckets);
    const end = Math.floor(((bucket + 1) * inner.length) / buckets);
    const slice = inner.slice(start, end);
    if (slice.length === 0) continue;
    let minIdx = 0;
    let maxIdx = 0;
    for (let i = 1; i < slice.length; i++) {
      if ((slice[i]?.value ?? 0) < (slice[minIdx]?.value ?? 0)) minIdx = i;
      if ((slice[i]?.value ?? 0) > (slice[maxIdx]?.value ?? 0)) maxIdx = i;
    }
    // Grafik zaman-sıralı ister; değer sırası değil zaman sırası yazılır.
    const pair =
      minIdx <= maxIdx
        ? [slice[minIdx], slice[maxIdx]]
        : [slice[maxIdx], slice[minIdx]];
    for (const point of pair) {
      if (point !== undefined) kept.push(point);
    }
  }
  kept.push(last);
  const seen = new Set<SamplePoint>();
  return kept.filter((point) => {
    if (seen.has(point)) return false;
    seen.add(point);
    return true;
  });
}
