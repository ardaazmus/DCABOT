"use client";

import { useTranslations } from "next-intl";

const ASSUMPTION_KEYS = [
  "CURRENT_VENUE_RULES",
  "CLOSED_BAR_FILLS",
  "FEES_FROM_PAPER_CONFIG",
  "FUNDING_NOT_MODELED",
] as const;

/** Varsayımlar dipnotu; bilinmeyen kod ham metinle gösterilir. */
export function AssumptionsNote({ assumptions }: { assumptions: readonly string[] }) {
  const t = useTranslations("backtest");
  if (assumptions.length === 0) return null;
  function label(code: string): string {
    switch (code) {
      case "CURRENT_VENUE_RULES":
        return t("assumptionCURRENT_VENUE_RULES");
      case "CLOSED_BAR_FILLS":
        return t("assumptionCLOSED_BAR_FILLS");
      case "FEES_FROM_PAPER_CONFIG":
        return t("assumptionFEES_FROM_PAPER_CONFIG");
      case "FUNDING_NOT_MODELED":
        return t("assumptionFUNDING_NOT_MODELED");
      default:
        return code;
    }
  }
  return (
    <div className="flex flex-col gap-1">
      <h2 className="text-sm font-semibold">{t("assumptionsTitle")}</h2>
      <ul className="flex flex-col gap-1 text-xs text-muted-foreground">
        {assumptions.map((code) => (
          <li key={code} title={ASSUMPTION_KEYS.includes(code as (typeof ASSUMPTION_KEYS)[number]) ? code : undefined}>
            {label(code)}
          </li>
        ))}
      </ul>
    </div>
  );
}
