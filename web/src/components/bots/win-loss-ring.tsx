"use client";

import { useTranslations } from "next-intl";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { winLossSlices } from "@/lib/chart/ring";

/**
 * Kazanma/kaybetme halkası (SVG, pathLength=100; bileşen aritmetik
 * yapmaz, dilimler lib/chart'tan gelir).
 */
export function WinLossRing({
  winningDeals,
  dealsCompleted,
  testId,
}: {
  winningDeals: number;
  dealsCompleted: number;
  testId: string;
}) {
  const t = useTranslations("bots");
  const { win, losses } = winLossSlices(winningDeals, dealsCompleted);
  return (
    <Card data-testid={testId}>
      <CardHeader>
        <CardTitle>{t("winLossTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex items-center gap-4">
        <svg width="96" height="96" viewBox="0 0 96 96" role="img" aria-label={t("winLossTitle")}>
          <circle cx="48" cy="48" r="40" fill="none" strokeWidth="12" className="stroke-loss/25" />
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            strokeWidth="12"
            pathLength={100}
            strokeDasharray={`${win} 100`}
            strokeLinecap="round"
            className="stroke-profit"
            transform="rotate(-90 48 48)"
          />
        </svg>
        <div className="flex flex-col gap-1 text-sm">
          <span>
            <span className="text-profit">●</span> {t("winLabel")}: {winningDeals}
          </span>
          <span>
            <span className="text-loss">●</span> {t("lossLabel")}: {losses}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
