/**
 * Olay zaman damgası (mikrosaniye, tamsayı) → kısa yerel tarih-saat metni.
 * Para değil, takvim hesabıdır; finans disiplininin dışındadır.
 */
export function formatEventTime(timeUs: number, locale: string): string {
  const date = new Date(Math.floor(timeUs / 1000));
  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/** Milisaniye damga (testnet saatleri) → aynı kısa metin. */
/**
 * Gün başı (µs) → "12 Eyl" / "Sep 12". Takvim etiketidir; saat yoktur.
 */
export function formatDayLabel(dayStartUs: number, locale: string): string {
  return new Intl.DateTimeFormat(locale, { day: "numeric", month: "short" }).format(
    new Date(Math.floor(dayStartUs / 1000)),
  );
}

export function formatMsTime(timeMs: number, locale: string): string {
  return new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(timeMs));
}

/**
 * Mikrosaniye süre → saat/dakika/saniye parçaları (takvim hesabı).
 * Metin birimi bileşende i18n ile eklenir ("3 sa 12 dk" / "3h 12m").
 */
export function durationParts(timeUs: number): { hours: number; minutes: number; seconds: number } {
  const totalSeconds = Math.max(0, Math.floor(timeUs / 1_000_000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  return { hours, minutes, seconds: totalSeconds % 60 };
}

const MONTH_PATTERN = /^(\d{4})-(\d{2})$/;

/**
 * "2026-08" → "Ağu 2026". Takvim hesabıdır. Biçim dışı metin
 * aynen döner (uydurma etiket yok).
 */
export function formatMonthLabel(month: string, locale: string): string {
  const match = MONTH_PATTERN.exec(month);
  if (match === null) return month;
  // `Number()` çizim dizini dışında yasak; basamak birikimi (takvim).
  const digits = (text: string): number => {
    let value = 0;
    for (const char of text) value = value * 10 + (char.charCodeAt(0) - 48);
    return value;
  };
  const year = digits(match[1] ?? "");
  const monthIndex = digits(match[2] ?? "") - 1;
  if (monthIndex < 0 || monthIndex > 11) return month;
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, monthIndex, 1)));
}
