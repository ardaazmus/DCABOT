"use client";

import { Popover } from "@base-ui/react/popover";
import { Bell } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";

import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/skeleton";
import { useEvents, useMarkNotificationsRead, useNotificationState } from "@/lib/api/queries";
import type { Landmark } from "@/lib/api/schemas";
import { formatEventTime } from "@/lib/format-time";

export function maxSeqOf(items: readonly Landmark[]): number {
  return items.reduce((max, event) => Math.max(max, event.seq), 0);
}

/** Bildirim satırları: açılır liste ve merkez sayfası paylaşır. */
export function NotificationList({ items }: { items: readonly Landmark[] }) {
  const locale = useLocale();
  return (
    <ol className="flex flex-col">
      {items.map((event) => (
        <li
          key={event.seq}
          className="flex flex-col gap-0.5 rounded-lg px-2 py-1.5 hover:bg-muted"
        >
          <span className="text-sm">{event.summary}</span>
          <span className="font-mono text-xs text-muted-foreground">
            {event.kind} · {formatEventTime(event.time_us, locale)}
          </span>
        </li>
      ))}
    </ol>
  );
}

/** Bildirimler: rozetli çıngırak + son olaylar + tümünü okundu işaretle. */
export function Notifications() {
  const t = useTranslations("topbar");
  const [open, setOpen] = useState(false);
  const events = useEvents(20);
  const state = useNotificationState();
  const markRead = useMarkNotificationsRead();
  const items = events.data?.data.events ?? [];
  const unread = state.data?.data.unread_count ?? 0;

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger
        data-testid="notifications-bell"
        aria-label={unread > 0 ? t("notificationsUnread", { count: unread }) : t("notifications")}
        className="relative flex size-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"
      >
        <Bell className="size-4" aria-hidden="true" />
        {unread > 0 ? (
          <span
            aria-hidden="true"
            className="absolute top-0.5 right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[10px] font-semibold text-accent-foreground"
          >
            {unread > 99 ? "99+" : unread}
          </span>
        ) : null}
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Positioner sideOffset={8} align="end" className="z-50">
          <Popover.Popup className="max-h-96 w-80 overflow-y-auto rounded-xl border border-border bg-card p-2 text-card-foreground">
          <div className="flex items-center justify-between px-2 pt-1 pb-2">
            <p className="text-sm font-semibold">{t("notifications")}</p>
            <button
              type="button"
              disabled={unread === 0 || markRead.isPending}
              onClick={() => markRead.mutate({ upto_seq: maxSeqOf(items) })}
              className="text-xs font-medium text-muted-foreground hover:text-foreground disabled:opacity-40"
            >
              {t("markAllRead")}
            </button>
          </div>
          {events.isPending ? (
            <div className="flex flex-col gap-2 p-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : events.isError ? (
            <p role="alert" className="p-2 text-sm text-muted-foreground">
              {t("notificationsError")}
            </p>
          ) : items.length === 0 ? (
            <div className="px-2">
              <EmptyState
                title={t("notificationsEmpty")}
                description={t("notificationsEmptyHint")}
              />
            </div>
          ) : (
            <NotificationList items={items} />
          )}
          <div className="border-t border-border px-2 pt-2 pb-1">
            <Link
              href="/notifications"
              onClick={() => setOpen(false)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              {t("viewAll")}
            </Link>
          </div>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  );
}
