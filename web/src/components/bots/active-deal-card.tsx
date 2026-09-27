"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { Money } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ActiveDeal } from "@/lib/api/schemas";
import { ratioToWidth } from "@/lib/chart/percent";
import { isDecimalString } from "@/lib/decimal";
import { durationParts, formatEventTime } from "@/lib/format-time";

function money(value: string | null, suffix: string) {
  return (
    <Money value={isDecimalString(value) ? value : undefined} suffix={suffix} />
  );
}

/**
 * Aktif deal kartı: ort/mark/uPnL(TP/sonraki SO/SO x/y/süre.
 * Deal yoksa ilk-deal ipucu + son mum saati gösterilir.
 */
export function ActiveDealCard({
  deal,
  lastBarOpenUs,
}: {
  deal: ActiveDeal | null;
  lastBarOpenUs: number | null;
}) {
  const t = useTranslations("bots");
  const locale = useLocale();
  const [nowUs] = useState(() => Date.now() * 1000);
  if (deal === null) {
    return (
      <Card data-testid="active-deal">
        <CardHeader>
          <CardTitle>{t("activeDealTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-1 text-sm text-muted-foreground">
          <span>{t("noActiveDeal")}</span>
          <span>{t("firstDealHint")}</span>
          {lastBarOpenUs === null ? null : (
            <span>{t("lastBar", { time: formatEventTime(lastBarOpenUs, locale) })}</span>
          )}
        </CardContent>
      </Card>
    );
  }
  const elapsed = durationParts(nowUs - deal.started_at_us);
  return (
    <Card data-testid="active-deal">
      <CardHeader>
        <CardTitle>{t("activeDealTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm md:grid-cols-4">
          <div>
            <dt className="text-muted-foreground">{t("avgPrice")}</dt>
            <dd>{money(deal.average_price, "USDT")}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("markPrice")}</dt>
            <dd>{money(deal.mark_price, "USDT")}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("unrealized")}</dt>
            <dd>
              <Pnl
                value={isDecimalString(deal.unrealized_profit) ? deal.unrealized_profit : undefined}
                variant="usdt"
                suffix="USDT"
              />
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("tpPrice")}</dt>
            <dd>{money(deal.take_profit_price, "USDT")}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("nextSoPrice")}</dt>
            <dd>{money(deal.next_safety_order_price, "USDT")}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">
              {t("soProgress", { filled: deal.safety_orders_filled, max: deal.max_safety_orders })}
            </dt>
            <dd
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={deal.max_safety_orders}
              aria-valuenow={deal.safety_orders_filled}
              className="h-1.5 overflow-hidden rounded-full bg-muted"
            >
              <div
                className="h-full rounded-full bg-accent"
                style={{
                  width: ratioToWidth(deal.safety_orders_filled, deal.max_safety_orders),
                }}
              />
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("dealDuration")}</dt>
            <dd>
              {elapsed.hours > 0
                ? t("durationHm", { h: elapsed.hours, m: elapsed.minutes })
                : elapsed.minutes > 0
                  ? t("durationM", { m: elapsed.minutes })
                  : t("durationS", { s: elapsed.seconds })}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
