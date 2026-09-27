"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { ConnectionCard } from "@/components/connection-card";
import { DataTable, type TableColumn } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { EnumValue } from "@/components/enum-value";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBackupTake, useBackupVerify, useBackups, useEvents } from "@/lib/api/queries";
import type { Backups, Events } from "@/lib/api/schemas";
import { formatEventTime } from "@/lib/format-time";
import { cn } from "@/lib/utils";

const STORES = ["historical_runs", "two_leg_journal"] as const;
const EVENTS_PER_PAGE = 20;

type BackupRow = Backups["data"]["backups"][number];
type EventRow = Events["data"]["events"][number];

function verdictVariant(verdict: string): "live" | "error" | "warn" | "stopped" {
  if (verdict === "VERIFIED") return "live";
  if (verdict === "FAILED" || verdict === "CORRUPT") return "error";
  return "stopped";
}

export default function SystemPage() {
  const ts = useTranslations("settings");
  const locale = useLocale();
  const backups = useBackups();
  const take = useBackupTake();
  const verify = useBackupVerify();
  const events = useEvents(200);
  const [store, setStore] = useState<string>(STORES[0]);
  const [verdicts, setVerdicts] = useState<Record<string, string>>({});
  const [eventPage, setEventPage] = useState(0);

  const backupColumns: TableColumn<BackupRow>[] = [
    {
      accessorKey: "backup_file",
      header: ts("fileName"),
      cell: ({ row }) => (
        <span className="font-mono text-xs break-all">{row.original.backup_file}</span>
      ),
    },
    { accessorKey: "store", header: ts("store") },
    {
      accessorKey: "bytes",
      header: ts("bytes"),
      cell: ({ row }) => (
        <span className="font-mono">{row.original.bytes.toLocaleString(locale)}</span>
      ),
      enableSorting: false,
    },
    {
      accessorKey: "created_us",
      header: ts("created"),
      cell: ({ row }) => (
        <span className="font-mono text-xs">
          {formatEventTime(row.original.created_us, locale)}
        </span>
      ),
    },
    {
      id: "verify",
      header: "",
      cell: ({ row }) => {
        const verdict = verdicts[row.original.backup_file];
        return (
          <span className="inline-flex items-center gap-2">
            {verdict === undefined ? null : (
              <StatusBadge variant={verdictVariant(verdict)}>
                <EnumValue code={verdict} />
              </StatusBadge>
            )}
            <button
              type="button"
              disabled={verify.isPending}
              onClick={() =>
                verify.mutate(
                  { backup_file: row.original.backup_file },
                  {
                    onSuccess: (data) =>
                      setVerdicts((prev) => ({
                        ...prev,
                        [row.original.backup_file]: data.data.verdict,
                      })),
                  },
                )
              }
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              {verify.isPending ? ts("verifying") : ts("verify")}
            </button>
          </span>
        );
      },
      enableSorting: false,
    },
  ];

  const eventColumns: TableColumn<EventRow>[] = [
    {
      accessorKey: "summary",
      header: ts("eventSummary"),
      cell: ({ row }) => <span title={row.original.ref}>{row.original.summary}</span>,
    },
    {
      accessorKey: "kind",
      header: ts("eventKind"),
      cell: ({ row }) => <span className="font-mono text-xs">{row.original.kind}</span>,
    },
    {
      accessorKey: "time_us",
      header: ts("eventTime"),
      cell: ({ row }) => (
        <span className="font-mono text-xs">
          {formatEventTime(row.original.time_us, locale)}
        </span>
      ),
    },
  ];

  const allEvents = events.data?.data.events ?? [];
  const eventPageCount = Math.max(1, Math.ceil(allEvents.length / EVENTS_PER_PAGE));
  const safeEventPage = Math.min(eventPage, eventPageCount - 1);
  const pageEvents = allEvents.slice(
    safeEventPage * EVENTS_PER_PAGE,
    safeEventPage * EVENTS_PER_PAGE + EVENTS_PER_PAGE,
  );

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <ConnectionCard />
      </section>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle>
            <h2>{ts("backupsTitle")}</h2>
          </CardTitle>
          <span className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground" htmlFor="backup-store">
              {ts("store")}
            </label>
            <select
              id="backup-store"
              value={store}
              onChange={(event) => setStore(event.target.value)}
              className="h-9 rounded-md border border-input bg-background px-2 font-mono text-sm"
            >
              {STORES.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={take.isPending}
              onClick={() => take.mutate({ store })}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
            >
              {ts("takeBackup")}
            </button>
          </span>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {backups.isPending ? (
            <Skeleton className="h-32 w-full" />
          ) : backups.isError || backups.data === undefined ? (
            <p role="alert" className="text-sm text-loss">
              {backups.error instanceof Error ? backups.error.message : ""}
            </p>
          ) : backups.data.data.backups.length === 0 ? (
            <EmptyState title={ts("noBackups")} description={ts("noBackupsHint")} />
          ) : (
            <DataTable
              columns={backupColumns}
              data={[...backups.data.data.backups].reverse()}
              emptyTitle={ts("noBackups")}
              pageSize={25}
            />
          )}
          {take.isError ? (
            <p role="alert" className="text-sm text-loss">
              {take.error.message}
            </p>
          ) : null}
          {verify.isError ? (
            <p role="alert" className="text-sm text-loss">
              {verify.error.message}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{ts("eventsTitle")}</h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-xs text-muted-foreground">{ts("eventsNote")}</p>
          {events.isPending ? (
            <Skeleton className="h-32 w-full" />
          ) : events.isError ? (
            <p role="alert" className="text-sm text-loss">
              {events.error.message}
            </p>
          ) : (
            <>
              <DataTable
                columns={eventColumns}
                data={pageEvents}
                emptyTitle={ts("eventsTitle")}
                pageSize={EVENTS_PER_PAGE}
              />
              {eventPageCount <= 1 ? null : (
                <nav aria-label={ts("eventsTitle")} className="flex items-center justify-end gap-2 text-sm">
                  <button
                    type="button"
                    onClick={() => setEventPage(Math.max(0, safeEventPage - 1))}
                    disabled={safeEventPage === 0}
                    className={cn(
                      "rounded-md border border-input px-3 py-1.5",
                      safeEventPage === 0 ? "opacity-50" : "hover:bg-muted",
                    )}
                  >
                    {ts("previous")}
                  </button>
                  <span className="font-mono text-muted-foreground">
                    {safeEventPage + 1} {ts("of")} {eventPageCount}
                  </span>
                  <button
                    type="button"
                    onClick={() => setEventPage(Math.min(eventPageCount - 1, safeEventPage + 1))}
                    disabled={safeEventPage >= eventPageCount - 1}
                    className={cn(
                      "rounded-md border border-input px-3 py-1.5",
                      safeEventPage >= eventPageCount - 1 ? "opacity-50" : "hover:bg-muted",
                    )}
                  >
                    {ts("next")}
                  </button>
                </nav>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
