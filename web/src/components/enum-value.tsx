"use client";

import { useLocale } from "next-intl";

import { enumLabel, hasEnumLabel } from "@/lib/enum-labels";

/**
 * Teknik kodun düz dil karşılığı; sözlükte varsa ham kod ipucunda durur,
 * yoksa ham kodun kendisi gösterilir.
 */
export function EnumValue({ code, className }: { code: string; className?: string }) {
  const locale = useLocale() === "en" ? "en" : "tr";
  const mapped = hasEnumLabel(code);
  return (
    <span className={className} title={mapped ? code : undefined}>
      {enumLabel(code, locale)}
    </span>
  );
}
