"use client";

import { useLocale } from "next-intl";

import { formatCompactVolume } from "@/lib/compact";
import type { DecimalString } from "@/lib/decimal";
import { cn } from "@/lib/utils";

/** 24s hacim hücresi: kısaltılmış okunaklı metin + tam değer ipucu. */
export function VolumeCompact({
  value,
  suffix,
  className,
}: {
  value: DecimalString | null | undefined;
  suffix?: string;
  className?: string;
}) {
  const locale = useLocale() === "en" ? "en" : "tr";
  const text = formatCompactVolume(value, locale);
  return (
    <span
      className={cn("font-mono", className)}
      title={value ?? undefined}
    >
      {suffix === undefined || text === "—" ? text : `${text} ${suffix}`}
    </span>
  );
}
