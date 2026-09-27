"use client";

import { useLocale } from "next-intl";

import {
  formatDecimal,
  parseDecimal,
  signOf,
  type DecimalString,
} from "@/lib/decimal";
import { cn } from "@/lib/utils";

function displayLocale(locale: string): "tr" | "en" {
  return locale === "en" ? "en" : "tr";
}

/** İşaretsiz büyüklük metni; eksi işareti metinden soyulur (hesap yok). */
function magnitude(value: DecimalString, locale: "tr" | "en"): string {
  const unsigned: DecimalString = value.startsWith("-")
    ? parseDecimal(value.slice(1))
    : value;
  return formatDecimal(unsigned, {
    locale,
    maxFractionDigits: 2,
  });
}

export function Pnl({
  value,
  variant = "usdt",
  suffix,
  className,
  title,
}: {
  value: DecimalString | null | undefined;
  variant?: "usdt" | "percent";
  /** USDT varyantında tutar son eki ("USDT" gibi). */
  suffix?: string;
  className?: string;
  /** Kısaltılmış gösterimde tam değer ipucu. */
  title?: string;
}) {
  const locale = displayLocale(useLocale());
  if (value === null || value === undefined) {
    return <span className={cn("font-mono", className)}>—</span>;
  }
  const sign = signOf(parseDecimal(value));
  const color =
    sign > 0 ? "text-profit" : sign < 0 ? "text-loss" : "text-muted-foreground";
  const mark = sign > 0 ? "+" : sign < 0 ? "-" : "";
  const magnitudeText = magnitude(parseDecimal(value), locale);
  const text =
    variant === "percent"
      ? `${mark}%${magnitudeText}`
      : `${mark}${magnitudeText}${suffix === undefined ? "" : ` ${suffix}`}`;
  return (
    <span className={cn("font-mono", color, className)} title={title}>
      {text}
    </span>
  );
}
