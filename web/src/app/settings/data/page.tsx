"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";

import { DataTable, type TableColumn } from "@/components/data-table";
import { EnumValue } from "@/components/enum-value";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useDatasets,
  useDownloadCancel,
  useDownloadJob,
  useDownloadStart,
} from "@/lib/api/queries";
import type { Datasets } from "@/lib/api/schemas";

type DatasetRow = Datasets["datasets"][number];

const TERMINAL = new Set(["SUCCEEDED", "FAILED", "CANCELLED"]);

function datasetStatusVariant(status: string): "live" | "error" | "warn" | "stopped" {
  if (status === "VERIFIED") return "live";
  if (status === "CORRUPT") return "error";
  if (status === "MISSING") return "warn";
  return "stopped";
}

function jobStatusVariant(status: string): "live" | "error" | "warn" | "stopped" | "paper" {
  if (status === "SUCCEEDED") return "live";
  if (status === "FAILED") return "error";
  if (status === "RUNNING" || status === "RETRYING") return "paper";
  if (status === "QUEUED") return "warn";
  return "stopped";
}

function DownloadJobCard({ jobId, datasetId }: { jobId: string; datasetId: string }) {
  const ts = useTranslations("settings");
  const locale = useLocale();
  const job = useDownloadJob(jobId);
  const cancel = useDownloadCancel();
  const active =
    job.data !== undefined && !TERMINAL.has(job.data.status);

  const progress =
    job.data === undefined
      ? null
      : job.data.total_bytes === null
        ? `${job.data.bytes_downloaded.toLocaleString(locale)} / ${ts("totalUnknown")}`
        : ts("progressBytes", {
            done: job.data.bytes_downloaded.toLocaleString(locale),
            total: job.data.total_bytes.toLocaleString(locale),
          });

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle className="font-mono text-sm font-medium">{datasetId}</CardTitle>
        {job.data === undefined ? null : (
          <StatusBadge variant={jobStatusVariant(job.data.status)}>
            <EnumValue code={job.data.status} />
          </StatusBadge>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {job.isPending ? (
          <Skeleton className="h-6 w-48" />
        ) : job.isError || job.data === undefined ? (
          <p role="alert" className="text-sm text-loss">
            {job.error instanceof Error ? job.error.message : ""}
          </p>
        ) : (
          <>
            <p className="font-mono text-sm">{progress}</p>
            {job.data.error_message === null ? null : (
              <p role="alert" className="text-sm text-loss">
                {job.data.error_message}
              </p>
            )}
            {active ? (
              <div>
                <button
                  type="button"
                  disabled={cancel.isPending}
                  onClick={() => cancel.mutate(jobId)}
                  className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50"
                >
                  {ts("cancelDownload")}
                </button>
              </div>
            ) : null}
            {cancel.isError ? (
              <p role="alert" className="text-sm text-loss">
                {cancel.error.message}
              </p>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function DataPage() {
  const ts = useTranslations("settings");
  const datasets = useDatasets();
  const starter = useDownloadStart();
  const [jobs, setJobs] = useState<Record<string, string>>({});

  const columns: TableColumn<DatasetRow>[] = [
    {
      accessorKey: "dataset_id",
      header: ts("datasetId"),
      cell: ({ row }) => (
        <span className="font-mono text-xs">{row.original.dataset_id}</span>
      ),
    },
    { accessorKey: "instrument", header: ts("instrument") },
    { accessorKey: "interval", header: ts("interval") },
    {
      id: "period",
      header: ts("period"),
      cell: ({ row }) => (
        <span className="font-mono text-xs">
          {row.original.period_start} → {row.original.period_end}
        </span>
      ),
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: ts("datasetStatus"),
      cell: ({ row }) => (
        <StatusBadge variant={datasetStatusVariant(row.original.status)}>
          <EnumValue code={row.original.status} />
        </StatusBadge>
      ),
    },
    {
      id: "sha",
      header: ts("sha"),
      cell: ({ row }) =>
        row.original.artifact === null ? (
          <span className="font-mono">—</span>
        ) : (
          <span className="font-mono text-xs break-all" title={row.original.artifact.sha256}>
            {row.original.artifact.sha256}
          </span>
        ),
      enableSorting: false,
    },
    {
      id: "action",
      header: "",
      cell: ({ row }) => {
        const active = jobs[row.original.dataset_id] !== undefined;
        return (
          <button
            type="button"
            disabled={active || starter.isPending}
            onClick={() =>
              starter.mutate(
                { dataset_id: row.original.dataset_id },
                {
                  onSuccess: (data) =>
                    setJobs((prev) => ({ ...prev, [row.original.dataset_id]: data.job.job_id })),
                },
              )
            }
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50"
          >
            {active ? ts("downloading") : ts("download")}
          </button>
        );
      },
      enableSorting: false,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">{ts("datasetsTitle")}</h2>
        {datasets.isPending ? (
          <Skeleton className="h-48 w-full" />
        ) : datasets.isError || datasets.data === undefined ? (
          <p role="alert" className="text-sm text-loss">
            {datasets.error instanceof Error ? datasets.error.message : ""}
          </p>
        ) : (
          <DataTable
            columns={columns}
            data={datasets.data.datasets}
            emptyTitle={ts("datasetsTitle")}
            pageSize={25}
          />
        )}
        {starter.isError ? (
          <p role="alert" className="text-sm text-loss">
            {starter.error.message}
          </p>
        ) : null}
      </section>

      {Object.entries(jobs).map(([datasetId, jobId]) => (
        <DownloadJobCard key={datasetId} jobId={jobId} datasetId={datasetId} />
      ))}
    </div>
  );
}
