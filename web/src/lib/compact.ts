import {
  formatDecimal,
  isDecimalString,
  parseDecimal,
  type DecimalString,
} from "@/lib/decimal";

export type CompactLocale = "tr" | "en";

const SUFFIXES: Record<CompactLocale, { million: string; billion: string; trillion: string }> = {
  tr: { million: "Mn", billion: "Mr", trillion: "Tr" },
  en: { million: "M", billion: "B", trillion: "T" },
};

/** Basamak dizisini bir artırır (görüntü yuvarlaması, elde ile). */
function incrementDigits(digits: string): string {
  const chars = digits.split("");
  let carry = true;
  for (let i = chars.length - 1; i >= 0 && carry; i--) {
    const char = chars[i] ?? "0";
    if (char === "9") {
      chars[i] = "0";
    } else {
      chars[i] = String.fromCharCode(char.charCodeAt(0) + 1);
      carry = false;
    }
  }
  if (carry) chars.unshift("1");
  return chars.join("");
}

function groupWhole(whole: string, locale: CompactLocale): string {
  return formatDecimal(parseDecimal(whole === "" ? "0" : whole), {
    locale,
    maxFractionDigits: 0,
  });
}

/**
 * Hacim gibi büyük tutarların okunaklı kısa metni. Yalnız görüntü
 * katmanıdır: metin üzerinde basamak kaydırma + görüntü yuvarlaması
 * yapar, finansal hesap içermez, `decimal.ts`'ye dokunmaz.
 *
 * - 1 Mn altı: tam sayı, binlik gruplu.
 * - üstü: en çok 2 ondalık + Mn/Mr/Tr (sıfırlar atılır).
 */
export function formatCompactVolume(
  value: DecimalString | null | undefined,
  locale: CompactLocale,
): string {
  if (value === null || value === undefined || !isDecimalString(value)) return "—";
  const negative = value.startsWith("-");
  const integer = (negative ? value.slice(1) : value).split(".")[0] ?? "0";
  const digits = integer.replace(/^0+(?=\d)/, "");
  if (digits.length <= 6) {
    const full = formatDecimal(parseDecimal(value), { locale, maxFractionDigits: 0 });
    return full;
  }
  const suffixes = SUFFIXES[locale];
  const scale = digits.length <= 9 ? 6 : digits.length <= 12 ? 9 : 12;
  const suffix = scale === 6 ? suffixes.million : scale === 9 ? suffixes.billion : suffixes.trillion;
  const whole = digits.slice(0, digits.length - scale);
  const rest = digits.slice(digits.length - scale);
  // İki ondalık, yarıya-yukarı görüntü yuvarlaması.
  const kept = (rest + "00").slice(0, 2);
  const next = rest.length > 2 ? (rest[2] ?? "0") : "0";
  let shown = whole + kept;
  if (next >= "5") shown = incrementDigits(shown);
  // Yuvarlama basamak taşırdıysa (999,995 Mn → 1000,00) yeniden böl.
  if (shown.length > whole.length + 2) {
    return formatCompactVolume(
      parseDecimal(`${negative ? "-" : ""}${shown.slice(0, -2) || "0"}${"0".repeat(scale)}`),
      locale,
    );
  }
  const frac = shown.slice(whole.length).replace(/0+$/, "");
  const sign = negative ? "-" : "";
  const decimalSeparator = locale === "tr" ? "," : ".";
  const groupedWhole = groupWhole(shown.slice(0, whole.length), locale);
  return frac === "" ? `${sign}${groupedWhole} ${suffix}` : `${sign}${groupedWhole}${decimalSeparator}${frac} ${suffix}`;
}
