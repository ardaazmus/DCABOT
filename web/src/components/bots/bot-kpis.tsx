"use client";

import { useTranslations } from "next-intl";

import { Pnl } from "@/components/pnl";
import { StatCard } from "@/components/stat-card";
import type { BotStats } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";

import { DurationText } from "./duration-text";

/** Genel sekmesi KPI şeridi: 7 kart, tek tek. */
export function BotKpis({ stats }: { stats: BotStats }) {
  const t = useTranslations("bots");
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatCard
        label={t("kpiTotalProfit")}
        value={
          <Pnl
            value={isDecimalString(stats.total_profit) ? stats.total_profit : undefined}
            variant="usdt"
            suffix="USDT"
          />
        }
      />
      <StatCard
        label={t("kpiRoi")}
        value={
          <Pnl
            value={isDecimalString(stats.roi_percent) ? stats.roi_percent : undefined}
            variant="percent"
          />
        }
      />
      <StatCard
        label={t("kpiWinRate")}
        value={
          <Pnl
            value={isDecimalString(stats.win_rate_percent) ? stats.win_rate_percent : undefined}
            variant="percent"
          />
        }
      />
      <StatCard label={t("kpiDeals")} value={<span>{stats.deals_completed}</span>} />
      <StatCard
        label={t("kpiAvgProfit")}
        value={
          <Pnl
            value={
              isDecimalString(stats.average_deal_profit)
                ? stats.average_deal_profit
                : undefined
            }
            variant="usdt"
            suffix="USDT"
          />
        }
      />
      <StatCard
        label={t("kpiAvgDuration")}
        value={<DurationText timeUs={stats.average_deal_duration_us} />}
      />
      <StatCard label={t("kpiStopLoss")} value={<span>{stats.stop_loss_deals}</span>} />
    </div>
  );
}
