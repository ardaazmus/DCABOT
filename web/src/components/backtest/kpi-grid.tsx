"use client";

import { useLocale, useTranslations } from "next-intl";

import { Money, NeutralPercent } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BacktestResult } from "@/lib/api/schemas";
import { formatDecimal, isDecimalString, type DecimalString } from "@/lib/decimal";
import { formatDealDuration } from "@/lib/format-duration";

function toDecimal(text: string | null | undefined): DecimalString | undefined {
  return text !== null && text !== undefined && isDecimalString(text) ? text : undefined;
}

function Tile({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-muted/50 px-3 py-2">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="break-all font-mono text-sm font-semibold">{children}</dd>
    </div>
  );
}

/** KPI kartları; her metrik yanıttan gelir, hesaplama yok. */
export function KpiGrid({ result }: { result: BacktestResult }) {
  const t = useTranslations("backtest");
  const locale = useLocale() === "en" ? "en" : "tr";
  const summary = result.summary;
  const sharpe = toDecimal(summary.sharpe_ratio_annualized);
  const profitFactor = toDecimal(summary.profit_factor);
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>
            {result.symbol} · {result.interval}
          </h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-2 text-sm min-[420px]:grid-cols-3">
          <Tile label={t("netProfit")}>
            <Pnl
              value={toDecimal(summary.net_profit)}
              suffix="USDT"
              title={summary.net_profit}
            />
          </Tile>
          <Tile label={t("roi")}>
            <Pnl value={toDecimal(summary.roi_percent)} variant="percent" title={summary.roi_percent} />
          </Tile>
          <Tile label={t("annualRoi")}>
            <Pnl
              value={toDecimal(summary.annualized_roi_percent)}
              variant="percent"
              title={summary.annualized_roi_percent}
            />
          </Tile>
          <Tile label={t("dealsClosed")}>
            <span className="font-mono">{summary.deals_completed}</span>
          </Tile>
          <Tile label={t("winRate")}>
            <NeutralPercent value={toDecimal(summary.win_rate_percent)} title={summary.win_rate_percent ?? undefined} />
          </Tile>
          <Tile label={t("profitFactor")}>
            {profitFactor === undefined ? (
              <span className="font-mono">—</span>
            ) : (
              <span className="font-mono" title={summary.profit_factor ?? undefined}>
                {formatDecimal(profitFactor, { locale, maxFractionDigits: 2 })}
              </span>
            )}
          </Tile>
          <Tile label={t("maxDrawdown")}>
            <NeutralPercent
              value={toDecimal(summary.max_drawdown_percent)}
              title={summary.max_drawdown_percent}
            />
          </Tile>
          <Tile label={t("sharpe")}>
            {sharpe === undefined ? (
              <span className="font-mono">—</span>
            ) : (
              <span className="font-mono" title={summary.sharpe_ratio_annualized ?? undefined}>
                {formatDecimal(sharpe, { locale, maxFractionDigits: 2 })}
              </span>
            )}
          </Tile>
          <Tile label={t("avgDuration")}>
            <span className="font-mono">{formatDealDuration(summary.average_deal_duration_us, locale)}</span>
          </Tile>
          <Tile label={t("maxSoUsed")}>
            <span className="font-mono">{summary.max_safety_orders_used}</span>
          </Tile>
          <Tile label={t("totalFees")}>
            <Money
              value={toDecimal(summary.total_fees)}
              suffix="USDT"
              options={{ maxFractionDigits: 2 }}
              title={summary.total_fees}
            />
          </Tile>
        </dl>
      </CardContent>
    </Card>
  );
}
