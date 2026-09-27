import { isDecimalString } from "./decimal";

/**
 * Borsa adım metninden (`tick`, `qty_step`) ondalık basamak sayısı.
 * Yalnız gösterim içindir: fiyatlar tick, miktarlar qty_step basamağıyla
 * kısaltılır. Geçersiz metin 0 verir (güvenli tarafta kalır).
 */
export function decimalsFromStep(step: string): number {
  if (!isDecimalString(step)) return 0;
  const dot = step.indexOf(".");
  if (dot === -1) return 0;
  let fraction = step.slice(dot + 1);
  if (!/^[0-9]+$/.test(fraction)) return 0;
  fraction = fraction.replace(/0+$/, "");
  return fraction.length;
}
