import { parseDecimal, type DecimalString } from "@/lib/decimal";

/**
 * Backend'in yüzde metnini (örn. "37.5") CSS çubuk genişliğine çevirir.
 * `Number()` bu dosyanın dışında yasak; yüzde metni yalnız burada ve
 * yalnız piksel hesabı için sayıya dönüşür. Aralık dışı değerler
 * kırpılır, bozuk metin %0 olur (bar boş, metin yine backend metnidir).
 */
export function percentToWidth(value: DecimalString): `${number}%` {
  let ratio = 0;
  try {
    ratio = Number(parseDecimal(value)) / 100;
  } catch {
    ratio = 0;
  }
  if (!Number.isFinite(ratio)) ratio = 0;
  const clamped = Math.min(1, Math.max(0, ratio));
  // Piksel hesabı: onda bir puandan ince ayrıntı anlamsız.
  return `${Math.round(clamped * 1000) / 10}%`;
}

/**
 * Sayaç oranı (dolan SO / azami SO gibi) → CSS çubuk genişliği.
 * Yüzde hesabı yalnız burada yapılır; sıfır bölme %0 olur.
 */
export function ratioToWidth(filled: number, max: number): `${number}%` {
  if (!Number.isFinite(filled) || !Number.isFinite(max) || max <= 0) return "0%";
  const clamped = Math.min(1, Math.max(0, filled / max));
  return `${Math.round(clamped * 1000) / 10}%`;
}
