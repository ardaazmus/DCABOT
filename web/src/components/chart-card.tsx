import type { ReactNode } from "react";

import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type ChartRange = { id: string; label: string };

export function ChartCard({
  title,
  ranges,
  activeRange,
  onRangeChange,
  state = "ready",
  error,
  onRetry,
  retryLabel = "Tekrar dene",
  empty,
  children,
  className,
}: {
  title: string;
  ranges?: readonly ChartRange[];
  activeRange?: string;
  onRangeChange?: (id: string) => void;
  state?: "ready" | "loading" | "error" | "empty";
  error?: string;
  onRetry?: () => void;
  retryLabel?: string;
  empty?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between gap-2">
        <CardTitle>{title}</CardTitle>
        {ranges === undefined || ranges.length === 0 ? null : (
          <div role="group" aria-label={title} className="flex gap-1">
            {ranges.map((range) => (
              <button
                key={range.id}
                type="button"
                aria-pressed={range.id === activeRange}
                onClick={() => onRangeChange?.(range.id)}
                className={cn(
                  "rounded-md px-2 py-1 text-xs font-medium",
                  range.id === activeRange
                    ? "bg-accent/12 text-accent"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {range.label}
              </button>
            ))}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {state === "loading" ? (
          <Skeleton className="h-48 w-full" />
        ) : state === "error" ? (
          <div className="flex h-48 flex-col items-center justify-center gap-3">
            <p role="alert" className="text-sm text-muted-foreground">
              {error ?? "Grafik yüklenemedi."}
            </p>
            {onRetry === undefined ? null : (
              <button
                type="button"
                onClick={onRetry}
                className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted"
              >
                {retryLabel}
              </button>
            )}
          </div>
        ) : state === "empty" ? (
          (empty ?? (
            <EmptyState
              title="Grafik için henüz veri yok"
              description="İlk veri geldiğinde grafik burada görünecek."
            />
          ))
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}
