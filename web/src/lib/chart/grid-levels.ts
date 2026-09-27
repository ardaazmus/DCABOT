import { isDecimalString } from "@/lib/decimal";

/**
 * Grid seviye merdiveni yerleşimi. Metin → sayı dönüşümü yalnız
 * burada ve yalnız piksel hesabı içindir; sonlu sayıya dönüşmeyen
 * değer çizilmez (uydurma nokta yok).
 */
export type GridLevelRow = {
  level: string;
  index: number;
  y: number;
};

export function gridLevelLayout(
  levels: readonly string[],
  height: number,
): { rows: GridLevelRow[]; yFor: (value: number) => number; top: number; bottom: number } {
  const prices = levels.map((level) => (isDecimalString(level) ? Number(level) : NaN));
  const finite = prices.filter((price) => Number.isFinite(price));
  const top = finite.length > 0 ? Math.max(...finite) : 1;
  const bottom = finite.length > 0 ? Math.min(...finite) : 0;
  const span = top - bottom === 0 ? 1 : top - bottom;
  const yFor = (value: number) => 4 + (1 - (value - bottom) / span) * (height - 8);
  const rows: GridLevelRow[] = [];
  levels.forEach((level, index) => {
    const price = prices[index];
    if (price === undefined || !Number.isFinite(price)) return;
    rows.push({ level, index, y: yFor(price) });
  });
  return { rows, yFor, top, bottom };
}

/** Sonlu ondalık metin → sayı; grafik dışı kullanım yasaktır. */
export function decimalToNumber(value: string | null): number | null {
  if (value === null || !isDecimalString(value)) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
