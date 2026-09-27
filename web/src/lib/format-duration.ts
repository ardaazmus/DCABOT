/**
 * Deal süresi (mikrosaniye, tamsayı) → "7s 56dk" gibi kısa metin.
 * Para değil, takvim hesabıdır; finans disiplininin dışındadır.
 * En büyük iki sıfır-dışı birim gösterilir.
 */
export function formatDealDuration(durationUs: number, locale: string): string {
  const units: { tr: string; en: string; micros: number }[] = [
    { tr: "g", en: "d", micros: 86_400_000_000 },
    { tr: "s", en: "h", micros: 3_600_000_000 },
    { tr: "dk", en: "m", micros: 60_000_000 },
    { tr: "sn", en: "s", micros: 1_000_000 },
  ];
  const totalSeconds = Math.max(0, Math.floor(durationUs / 1_000_000));
  let rest = totalSeconds;
  const parts: string[] = [];
  for (const unit of units) {
    const unitSeconds = unit.micros / 1_000_000;
    const count = Math.floor(rest / unitSeconds);
    rest -= count * unitSeconds;
    if (count > 0) parts.push(`${count}${locale === "en" ? unit.en : unit.tr}`);
    if (parts.length === 2) break;
  }
  if (parts.length === 0) return locale === "en" ? "0m" : "0dk";
  return parts.join(" ");
}
