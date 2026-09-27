"use client";

import { useTranslations } from "next-intl";

import { Pnl } from "@/components/pnl";
import { useBotStats } from "@/lib/api/queries";
import { isDecimalString } from "@/lib/decimal";

/**
 * Liste satırı istatistikleri: toplam kâr + aktif deal SO x/y.
 * Tek çekimdir (liste anlığı); aynı anahtar TanStack'te tek istek olur.
 */
export function BotRowProfit({ botId }: { botId: string }) {
  const statsQuery = useBotStats(botId);
  const total = statsQuery.data?.data.total_profit;
  return (
    <Pnl
      value={total !== undefined && isDecimalString(total) ? total : undefined}
      variant="usdt"
      suffix="USDT"
    />
  );
}

export function BotRowActiveDeal({ botId }: { botId: string }) {
  const t = useTranslations("bots");
  const statsQuery = useBotStats(botId);
  const active = statsQuery.data?.data.active_deal;
  if (active === undefined || active === null) return <span>{t("noActiveShort")}</span>;
  return (
    <span className="font-mono">
      {t("soProgress", { filled: active.safety_orders_filled, max: active.max_safety_orders })}
    </span>
  );
}
