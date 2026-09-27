"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiHttpError } from "@/lib/api/client";
import { useBotCopy } from "@/lib/api/queries";

/**
 * Botu kopyalama düğmesi: kurulumu taze STOPPED bir bot olarak
 * çoğaltır ve kopyanın detayına gider. Kopyada runtime/deal yoktur.
 */
export function BotCopyButton({ botId, disabled }: { botId: string; disabled?: boolean }) {
  const t = useTranslations("bots");
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const copy = useBotCopy();

  function run() {
    setError(null);
    copy.mutate(
      { botId },
      {
        onSuccess: (envelope) => router.push(`/bots/${envelope.data.bot_id}`),
        onError: (mutationError) => {
          if (mutationError instanceof ApiHttpError && mutationError.problem !== undefined) {
            setError(mutationError.problem.detail ?? "");
          } else {
            setError(mutationError instanceof Error ? mutationError.message : "");
          }
        },
      },
    );
  }

  return (
    <span className="inline-flex flex-col items-end gap-1">
      <button
        type="button"
        disabled={disabled === true || copy.isPending}
        onClick={run}
        data-testid="bot-copy"
        title={t("copyHint")}
        className="rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50"
      >
        {copy.isPending ? t("copyingAction") : t("copyAction")}
      </button>
      {error === null ? null : (
        <span role="alert" className="max-w-64 text-right text-xs text-loss">
          {error}
        </span>
      )}
    </span>
  );
}
