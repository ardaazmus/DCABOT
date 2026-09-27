"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { CheckCheck, Info, Layers, Play } from "lucide-react";

import { Skeleton } from "@/components/skeleton";
import { Button } from "@/components/ui/button";
import { useBotEvents } from "@/lib/api/queries";
import type { BotEvent } from "@/lib/api/schemas";
import { formatEventTime } from "@/lib/format-time";

import { CLOSE_REASON_KEY, describeBotEvent, detailChips, type EventTone } from "./event-text";

const TONE_ICON: Record<EventTone, typeof Info> = {
  open: Play,
  fill: Layers,
  close: CheckCheck,
  note: Info,
};

const PAGE = 50;
const MAX = 500;

/**
 * Olay kaydı: yeniden eskiye satırlar, ikon + TR/EN metin + detay
 * çipleri. Sayfa başı 50; "Daha fazla" limiti 50'şer artırır (≤500).
 * `events` verilirse hazır liste gösterilir (deal detayı), istek atılmaz.
 */
export function EventsTimeline({
  botId,
  status,
  maxSo,
  testId,
  events: provided,
}: {
  botId: string;
  status: string;
  maxSo: number;
  testId: string;
  events?: readonly BotEvent[];
}) {
  const t = useTranslations("bots");
  const locale = useLocale();
  const [limit, setLimit] = useState(PAGE);
  const eventsQuery = useBotEvents(botId, limit, status, provided === undefined);
  const events = provided ?? eventsQuery.data?.data ?? [];

  function textFor(kind: string, key: string, detail: Record<string, string | number | null>): string {
    const deal = detail.deal ?? "?";
    switch (key) {
      case "eventDealStarted":
      case "eventAmbiguous":
        return t(key, { deal });
      case "eventDealClosed": {
        const reasonKey = CLOSE_REASON_KEY[String(detail.reason ?? "")];
        const reason = reasonKey === undefined ? null : t(reasonKey);
        return reason === null ? t(key, { deal }) : `${t(key, { deal })} — ${reason}`;
      }
      case "eventSafetyFilled":
        return t(key, { filled: detail.index ?? "?", max: maxSo });
      case "eventManualFilled":
        return t(key, { index: detail.index ?? "?" });
      case "eventNote":
        return detail.text === undefined || detail.text === null ? t(key) : String(detail.text);
      default:
        return t("eventUnknown", { kind });
    }
  }

  return (
    <div data-testid={testId} className="flex flex-col gap-2">
      {provided === undefined && eventsQuery.isPending ? (
        <div className="flex flex-col gap-2" role="status">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : null}
      <ol className="flex flex-col gap-2">
        {events.map((event) => {
          const { key, tone } = describeBotEvent(event);
          const Icon = TONE_ICON[tone];
          return (
            <li key={`${event.time_us}-${event.kind}`} className="flex items-start gap-2 text-sm">
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
              <div className="flex flex-col gap-0.5">
                <span>{textFor(event.kind, key, event.detail)}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {formatEventTime(event.time_us, locale)}
                </span>
                <span className="flex flex-wrap gap-1">
                  {detailChips(event.detail).map((chip) => (
                    <span
                      key={chip.label}
                      className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-muted-foreground"
                    >
                      {chip.label}: {chip.value}
                    </span>
                  ))}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
      {provided === undefined && events.length >= limit && limit < MAX ? (
        <Button type="button" variant="outline" onClick={() => setLimit(limit + PAGE)}>
          {t("moreEvents")}
        </Button>
      ) : null}
    </div>
  );
}
