"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiHttpError } from "@/lib/api/client";
import { useBotReplay } from "@/lib/api/queries";

function isoDaysAgo(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

type FieldErrors = Partial<Record<"start" | "end" | "general", string>>;

/**
 * Geçmiş çalıştırma formu: taze STOPPED botu seçili aralıkta yerelde
 * çalıştırır. Başarıda form sonuç paneline dönüşür (kanıt kaybolmaz);
 * sayfa yenilenirse çalışmış botta backend 409 ile dürüstçe reddeder.
 */
export function ReplayForm({ botId }: { botId: string }) {
  const t = useTranslations("bots");
  const [start, setStart] = useState(() => isoDaysAgo(3));
  const [end, setEnd] = useState(() => isoDaysAgo(1));
  const [errors, setErrors] = useState<FieldErrors>({});
  const replay = useBotReplay(botId);

  function run() {
    setErrors({});
    replay.mutate(
      { start_date: start, end_date: end },
      {
        onError: (error) => {
          if (error instanceof ApiHttpError && error.problem !== undefined) {
            const mapped: FieldErrors = {};
            for (const item of error.problem.errors ?? []) {
              if (item.field === "start_date") mapped.start = error.problem.detail;
              else if (item.field === "end_date") mapped.end = error.problem.detail;
              else mapped.general = error.problem.detail;
            }
            if (Object.keys(mapped).length === 0) mapped.general = error.problem.detail;
            setErrors(mapped);
          } else {
            setErrors({ general: error instanceof Error ? error.message : "" });
          }
        },
      },
    );
  }

  const data = replay.data?.data ?? null;
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{t("replayTitle")}</h2>
        </CardTitle>
      </CardHeader>
      {data === null ? (
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">{t("replayHint")}</p>
          <div className="grid grid-cols-1 gap-4 min-[420px]:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="font-medium">{t("replayStart")}</span>
              <input
                type="date"
                value={start}
                max={end}
                onChange={(event) => {
                  setStart(event.target.value);
                  setErrors((prev) => {
                    if (prev.start === undefined) return prev;
                    const next = { ...prev };
                    delete next.start;
                    return next;
                  });
                }}
                data-testid="replay-start"
                className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              {errors.start === undefined ? null : (
                <span role="alert" className="text-xs text-loss">
                  {errors.start}
                </span>
              )}
            </label>
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="font-medium">{t("replayEnd")}</span>
              <input
                type="date"
                value={end}
                min={start}
                onChange={(event) => {
                  setEnd(event.target.value);
                  setErrors((prev) => {
                    if (prev.end === undefined) return prev;
                    const next = { ...prev };
                    delete next.end;
                    return next;
                  });
                }}
                data-testid="replay-end"
                className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              {errors.end === undefined ? null : (
                <span role="alert" className="text-xs text-loss">
                  {errors.end}
                </span>
              )}
            </label>
          </div>
          {errors.general === undefined ? null : (
            <p role="alert" data-testid="replay-error" className="text-sm text-loss">
              {errors.general}
            </p>
          )}
          <div>
            <button
              type="button"
              disabled={replay.isPending || start === "" || end === ""}
              onClick={run}
              data-testid="replay-run"
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
            >
              {replay.isPending ? t("replayRunning") : t("replayRun")}
            </button>
          </div>
        </CardContent>
      ) : (
        <CardContent className="flex flex-col gap-2">
          <p role="status" data-testid="replay-result" className="text-sm">
            {t("replayDone", {
              bars: data.bars,
              opened: data.deals_opened,
              closed: data.deals_closed,
              fills: data.fills,
            })}
          </p>
          {data.stopped === null ? null : (
            <p className="text-sm text-muted-foreground">
              {t("replayStopped", { reason: data.stopped })}
            </p>
          )}
        </CardContent>
      )}
    </Card>
  );
}
