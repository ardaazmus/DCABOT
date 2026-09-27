"use client";

import { useLocale, useTranslations } from "next-intl";

import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Regime } from "@/lib/api/schemas";
import { formatDecimal, isDecimalString } from "@/lib/decimal";
import { regimeLabel } from "@/lib/regime-label";

function plainNumber(text: string | null, locale: "tr" | "en"): string {
  if (text === null || !isDecimalString(text)) return "—";
  return formatDecimal(text, { locale, maxFractionDigits: 2 });
}

export function RegimeCard({ regime }: { regime: Regime }) {
  const t = useTranslations("symbol");
  const locale = useLocale() === "en" ? "en" : "tr";
  const label = regimeLabel(regime.data.state, regime.data.direction);
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("regime")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div>
          {label.key === null ? (
            <StatusBadge variant="warn">{label.raw}</StatusBadge>
          ) : (
            <span className="text-xl font-semibold">{t(label.key)}</span>
          )}
        </div>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted-foreground">{t("regimeAdx")}</dt>
          <dd className="font-mono">{plainNumber(regime.data.adx, locale)}</dd>
          <dt className="text-muted-foreground">{t("regimeConfidence")}</dt>
          <dd className="font-mono">{plainNumber(regime.data.confidence, locale)}</dd>
        </dl>
        <p className="text-xs text-muted-foreground">{t("regimeBarsNote")}</p>
        <p className="text-xs text-muted-foreground">{t("regimeNote")}</p>
      </CardContent>
    </Card>
  );
}
