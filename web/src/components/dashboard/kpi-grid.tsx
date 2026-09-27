"use client";

import { useTranslations } from "next-intl";

import { Money } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { StatCard } from "@/components/stat-card";
import type { PortfolioSummary } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";

export function KpiGrid({ summary }: { summary: PortfolioSummary }) {
  const t = useTranslations("dashboard");
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" data-testid="dashboard-kpis">
      <StatCard
        label={t("totalValue")}
        value={
          <Money
            value={isDecimalString(summary.total_value) ? summary.total_value : undefined}
            suffix="USDT"
          />
        }
      />
      <StatCard
        label={t("todayProfit")}
        value={
          <Pnl
            value={isDecimalString(summary.today_profit) ? summary.today_profit : undefined}
            variant="usdt"
            suffix="USDT"
          />
        }
      />
      <StatCard label={t("activeBots")} value={<span>{summary.active_bots}</span>} />
      <StatCard
        label={t("deployedCapital")}
        value={
          <Money
            value={isDecimalString(summary.deployed_capital) ? summary.deployed_capital : undefined}
            suffix="USDT"
          />
        }
      />
    </div>
  );
}
