"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { use } from "react";

import { EventsTimeline } from "@/components/bots/events-timeline";
import { DealActions } from "@/components/deals/deal-actions";
import { DealChart } from "@/components/deals/deal-chart";
import { DealFillsTable } from "@/components/deals/deal-fills-table";
import { DealLevels } from "@/components/deals/deal-levels";
import { EmptyState } from "@/components/empty-state";
import { Pnl } from "@/components/pnl";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiHttpError } from "@/lib/api/client";
import { useBot, useDealDetail } from "@/lib/api/queries";
import { isGridStrategy } from "@/lib/api/schemas";
import { isDecimalString } from "@/lib/decimal";

/**
 * Deal kimliği `botId:sıra` biçimindedir; bot kimliklerinde iki
 * nokta geçmez, ayrım kesindir. Yönlendirici parametreyi kodlu
 * geçebilir (`%3A`), önce çözülür. Sıra basamak birikimiyle okunur
 * (`Number()` grafik dışı yasak).
 */
export function parseDealId(id: string): { botId: string; seq: number } | null {
  let raw = id;
  try {
    raw = decodeURIComponent(id);
  } catch {
    return null;
  }
  const cut = raw.lastIndexOf(":");
  if (cut <= 0) return null;
  const tail = raw.slice(cut + 1);
  if (!/^[1-9][0-9]{0,8}$/.test(tail)) return null;
  let seq = 0;
  for (const ch of tail) seq = seq * 10 + (ch.charCodeAt(0) - 48);
  return { botId: raw.slice(0, cut), seq };
}

export default function DealDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("deals");
  const tb = useTranslations("bots");
  const parsed = parseDealId(id);
  const detail = useDealDetail(parsed?.botId ?? "", parsed?.seq ?? 0, parsed !== null);
  const bot = useBot(parsed?.botId ?? "", parsed !== null);

  if (parsed === null) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t("notFound")}</h1>
        <EmptyState
          title={t("notFound")}
          actionLabel={t("backToDeals")}
          actionHref="/deals"
        />
      </div>
    );
  }

  if (detail.isPending || bot.isPending) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2" role="status">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const data = detail.data?.data;
  const botData = bot.data?.data;
  if (detail.isError || bot.isError || data === undefined || botData === undefined) {
    const notFound = detail.error instanceof ApiHttpError && detail.error.status === 404;
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t("notFound")}</h1>
        <EmptyState
          title={t("notFound")}
          description={notFound ? undefined : tb("loadError")}
          actionLabel={t("backToDeals")}
          actionHref="/deals"
        />
      </div>
    );
  }

  const open = data.closed_at_us === null;
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight">
              {t("detailTitle", { deal: data.deal })}
            </h1>
            <Link
              href={`/market/${data.symbol}`}
              className="font-mono text-lg text-muted-foreground underline-offset-4 hover:underline"
            >
              {data.symbol}
            </Link>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {open ? (
              <StatusBadge variant="paper">{tb("openBadge")}</StatusBadge>
            ) : (
              <Pnl
                value={isDecimalString(data.profit) ? data.profit : undefined}
                variant="usdt"
                suffix="USDT"
              />
            )}
            <Link
              href={`/bots/${encodeURIComponent(data.bot_id)}`}
              className="text-sm underline-offset-4 hover:underline"
            >
              {t("botLink")}: {data.bot_name}
            </Link>
          </div>
        </div>
        <DealActions
          botId={data.bot_id}
          seq={data.deal}
          revision={botData.revision}
          open={open}
          testId="deal-actions"
        />
      </div>

      <DealChart deal={data} />

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
        <DealLevels deal={data} />
        <Card>
          <CardHeader>
            <CardTitle>
              <h2>{t("eventsTitle")}</h2>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <EventsTimeline
              botId={data.bot_id}
              status={botData.status}
              maxSo={isGridStrategy(botData.strategy) ? 0 : botData.strategy.max_safety_orders}
              testId="deal-timeline"
              events={data.events}
            />
          </CardContent>
        </Card>
      </div>

      <DealFillsTable events={data.events} testId="deal-fills" />
    </div>
  );
}
