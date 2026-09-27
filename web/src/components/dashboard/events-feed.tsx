"use client";

import { useLocale, useTranslations } from "next-intl";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Events } from "@/lib/api/schemas";
import { formatEventTime } from "@/lib/format-time";

type FeedEvent = Events["data"]["events"][number];

/** Son sistem olayları. Olay yoksa bölüm gizlenir (boş liste yok). */
export function EventsFeed({ events }: { events: readonly FeedEvent[] }) {
  const t = useTranslations("dashboard");
  const locale = useLocale() === "en" ? "en" : "tr";
  if (events.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("eventsTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="flex flex-col gap-2">
          {events.map((event) => (
            <li key={event.seq} className="flex items-baseline gap-3 text-sm">
              <span className="shrink-0 font-mono text-xs text-muted-foreground">
                {formatEventTime(event.time_us, locale)}
              </span>
              <span className="min-w-0">{event.summary}</span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}
