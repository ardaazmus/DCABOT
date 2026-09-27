export type DivergingBar = { heightPct: number; positive: boolean } | null;

/**
 * Iraksak çubuk yerleşimi (aylık getiri): yükseklik en büyük
 * büyüklüğe oranlanır. `Number()` yalnız burada, yalnız piksel
 * içindir; kartlar ham metni gösterir.
 */
export function divergingBars(
  values: readonly (string | null | undefined)[],
  maxPct = 100,
): DivergingBar[] {
  const parsed = values.map((text) => {
    if (text === null || text === undefined) return null;
    const value = Number(text);
    return Number.isFinite(value) ? value : null;
  });
  const magnitudes = parsed.filter((value): value is number => value !== null).map(Math.abs);
  const peak = magnitudes.length === 0 ? 0 : Math.max(...magnitudes);
  return parsed.map((value) => {
    if (value === null || peak === 0) return null;
    return { heightPct: (Math.abs(value) / peak) * maxPct, positive: value >= 0 };
  });
}

/** Sayım çubukları (SO kullanımı): yükseklik en büyük sayıma oranlanır. */
export function countBars(counts: readonly number[], maxPct = 100): number[] {
  const peak = counts.length === 0 ? 0 : Math.max(...counts);
  if (peak <= 0) return counts.map(() => 0);
  return counts.map((count) => (count <= 0 ? 0 : (count / peak) * maxPct));
}
