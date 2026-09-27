"use client";

import { useTranslations } from "next-intl";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BotDeal } from "@/lib/api/schemas";
import { barHeights, countBySo } from "@/lib/chart/histogram";

/**
 * SO kullanım dağılımı: kapanan deal'lerin dolum sayısına göre
 * 0..max çubukları (sıfır kovalı). Sayım ve yükseklik lib/chart'tadır.
 */
export function SoHistogram({
  deals,
  maxSo,
  testId,
}: {
  deals: readonly BotDeal[];
  maxSo: number;
  testId: string;
}) {
  const t = useTranslations("bots");
  const counts = countBySo(deals, maxSo);
  const heights = barHeights(counts);
  return (
    <Card data-testid={testId}>
      <CardHeader>
        <CardTitle>{t("soHistTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-32 items-end gap-2" role="img" aria-label={t("soHistTitle")}>
          {counts.map((count, bucket) => (
            <div key={bucket} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
              <span className="font-mono text-xs text-muted-foreground">{count}</span>
              <div
                className="w-full rounded-t bg-accent"
                style={{ height: `${heights[bucket] ?? 0}%` }}
              />
              <span className="font-mono text-xs text-muted-foreground">{bucket}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
