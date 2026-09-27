"use client";

import { useTranslations } from "next-intl";

/**
 * Durum rozeti yanı ipucu: duraklatma açıklaması + status_reason metni.
 * RUNNER_ERROR ham gösterilir; ikisi de yoksa hiçbir şey çizilmez.
 */
export function BotStatusHint({
  status,
  reason,
}: {
  status: string;
  reason: string | null;
}) {
  const t = useTranslations("bots");
  const reasonText =
    reason === "KILL_SWITCH_ACTIVE" || reason === "KILL_SWITCH_ON"
      ? t("reasonKillSwitch")
      : reason === "WAITING_MARKET_DATA"
        ? t("reasonMarketData")
        : reason;
  if (reasonText === null && status !== "PAUSED") return null;
  return (
    <div className="flex flex-col gap-0.5 text-xs text-muted-foreground">
      {status === "PAUSED" ? <span>{t("pausedHint")}</span> : null}
      {reasonText === null ? null : <span>{reasonText}</span>}
    </div>
  );
}
