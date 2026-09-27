"use client";

import { useTranslations } from "next-intl";

import { EmptyState } from "@/components/empty-state";
import { NotificationList, maxSeqOf } from "@/components/shell/notifications";
import { TelegramSettingsCard } from "@/components/shell/telegram-settings";
import { Skeleton } from "@/components/skeleton";
import { useEvents, useMarkNotificationsRead, useNotificationState } from "@/lib/api/queries";

/** Bildirim merkezi: tam olay geçmişi + okundu durumu. */
export default function NotificationsPage() {
  const t = useTranslations("topbar");
  const title = useTranslations("notifications");
  const events = useEvents(200);
  const state = useNotificationState();
  const markRead = useMarkNotificationsRead();
  const items = events.data?.data.events ?? [];
  const unread = state.data?.data.unread_count ?? 0;

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-4 p-4 md:p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{title("title")}</h1>
        <button
          type="button"
          disabled={unread === 0 || markRead.isPending}
          onClick={() => markRead.mutate({ upto_seq: maxSeqOf(items) })}
          className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-40"
        >
          {t("markAllRead")}
        </button>
      </div>
      <TelegramSettingsCard />
      {events.isPending ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : events.isError ? (
        <p role="alert" className="text-sm text-muted-foreground">
          {t("notificationsError")}
        </p>
      ) : items.length === 0 ? (
        <EmptyState title={t("notificationsEmpty")} description={t("notificationsEmptyHint")} />
      ) : (
        <NotificationList items={items} />
      )}
    </main>
  );
}
