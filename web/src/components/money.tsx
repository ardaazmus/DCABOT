"use client";

import { useLocale } from "next-intl";

import {
  formatDecimal,
  parseDecimal,
  type DecimalString,
  type FormatOptions,
} from "@/lib/decimal";
import { cn } from "@/lib/utils";

type Locale = "tr" | "en";

function displayLocale(locale: string): Locale {
  return locale === "en" ? "en" : "tr";
}

type AmountProps = {
  /** Tanımsız değer "—" gösterir. */
  value: DecimalString | null | undefined;
  options?: FormatOptions;
  suffix?: string;
  className?: string;
  /** Kısaltılmış gösterimde tam değer ipucu. */
  title?: string;
};

function Amount({ value, options, suffix, className, title }: AmountProps) {
  const locale = useLocale();
  if (value === null || value === undefined) {
    return <span className={cn("font-mono", className)}>—</span>;
  }
  const text = formatDecimal(parseDecimal(value), {
    ...options,
    locale: options?.locale ?? displayLocale(locale),
  });
  return (
    <span className={cn("font-mono", className)} title={title}>
      {suffix === undefined ? text : `${text} ${suffix}`}
    </span>
  );
}

/** Para tutarı (USDT gibi). */
export function Money(props: AmountProps) {
  return <Amount {...props} />;
}

/** Fiyat. */
export function Price(props: AmountProps) {
  return <Amount {...props} />;
}

/** Miktar. */
export function Qty(props: AmountProps) {
  return <Amount {...props} />;
}

/**
 * Nötr yüzde (sapma, fiyat kapsamı): kâr/zarar değildir, renk ve
 * işaret almaz. `%1,5` geleneği Pnl ile aynıdır.
 */
export function NeutralPercent({
  value,
  maxFractionDigits = 2,
  className,
  title,
}: {
  value: DecimalString | null | undefined;
  maxFractionDigits?: number;
  className?: string;
  title?: string;
}) {
  const locale = useLocale();
  if (value === null || value === undefined) {
    return <span className={cn("font-mono", className)}>—</span>;
  }
  const unsigned = value.startsWith("-") ? value.slice(1) : value;
  const text = formatDecimal(parseDecimal(unsigned), {
    maxFractionDigits,
    locale: displayLocale(locale),
  });
  return (
    <span className={cn("font-mono", className)} title={title}>
      %{text}
    </span>
  );
}
