/**
 * SO kullanım dağılımı: kapanan deal'lerin dolum sayısına göre sayımı
 * (0..max) ve çubuk yükseklikleri. Sayım para hesabı değildir; yüzde ve
 * yükseklik piksel hesabıdır, yalnız burada yapılır.
 */
export function countBySo(
  deals: readonly { closed_at_us: number | null; safety_orders_filled: number }[],
  maxSo: number,
): number[] {
  const counts = Array.from({ length: maxSo + 1 }, () => 0);
  for (const deal of deals) {
    if (deal.closed_at_us === null) continue;
    const bucket = Math.min(Math.max(0, deal.safety_orders_filled), maxSo);
    counts[bucket] = (counts[bucket] ?? 0) + 1;
  }
  return counts;
}

/** Sayımları en büyüğe göre 0..100 yüksekliklere çevirir (tepe 100). */
export function barHeights(counts: readonly number[]): number[] {
  const peak = Math.max(0, ...counts);
  if (peak === 0) return counts.map(() => 0);
  return counts.map((count) => Math.round((count / peak) * 1000) / 10);
}
