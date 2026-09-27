"use client";

import { Dialog } from "@base-ui/react/dialog";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { ApiHttpError } from "@/lib/api/client";
import { useBotAction, type BotAction } from "@/lib/api/queries";
import type { Bot } from "@/lib/api/schemas";
import { allowedActions } from "@/lib/bots";
import { cn } from "@/lib/utils";

const ACTION_LABEL: Record<BotAction, "actionStart" | "actionPause" | "actionResume" | "actionStop" | "actionArchive"> = {
  start: "actionStart",
  pause: "actionPause",
  resume: "actionResume",
  stop: "actionStop",
  archive: "actionArchive",
};

/**
 * Durum makinesine göre yalnız geçerli eylemler. Başlatın 409'u
 * (`BOT_RUNNER_UNAVAILABLE`) hata değil bilgi diyaloğudur; revizyon
 * çakışmasında liste yenilenir ve kısa not gösterilir.
 */
export function BotActions({ bot, compact = false }: { bot: Bot; compact?: boolean }) {
  const t = useTranslations("bots");
  const mutation = useBotAction();
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [runnerOpen, setRunnerOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  function run(action: BotAction) {
    setNotice(null);
    mutation.mutate(
      { botId: bot.bot_id, action, revision: bot.revision },
      {
        onError: (error) => {
          if (error instanceof ApiHttpError) {
            if (error.problem?.code === "BOT_RUNNER_UNAVAILABLE") {
              setRunnerOpen(true);
              return;
            }
            if (error.problem?.code === "BOT_REVISION_CONFLICT") {
              setNotice(t("revisionConflict"));
              return;
            }
          }
          setNotice(error instanceof Error ? error.message : "");
        },
      },
    );
  }

  const actions = bot.archived ? [] : allowedActions(bot.status);
  if (actions.length === 0 && notice === null) return null;

  return (
    <div className="flex flex-col gap-1">
      <div className={cn("flex gap-1", compact ? "flex-row" : "flex-wrap")}>
        {actions.map((action) => (
          <button
            key={action}
            type="button"
            disabled={mutation.isPending || (action === "start" && bot.mode === "TESTNET")}
            title={
              action === "start" && bot.mode === "TESTNET" ? t("testnetStartDisabled") : undefined
            }
            onClick={() => {
              if (action === "archive") setArchiveOpen(true);
              else run(action);
            }}
            className={cn(
              "rounded-md border border-input bg-background font-medium hover:bg-muted",
              "disabled:cursor-wait disabled:opacity-60",
              compact ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm",
            )}
          >
            {t(ACTION_LABEL[action])}
          </button>
        ))}
      </div>
      {notice === null ? null : (
        <p role={notice === t("revisionConflict") ? "status" : "alert"} className="text-xs text-muted-foreground">
          {notice}
        </p>
      )}
      <ConfirmDialog
        open={archiveOpen}
        onOpenChange={setArchiveOpen}
        title={t("archiveTitle")}
        description={t("archiveDesc")}
        confirmLabel={t("confirm")}
        cancelLabel={t("cancel")}
        onConfirm={() => {
          setArchiveOpen(false);
          run("archive");
        }}
      />
      <Dialog.Root open={runnerOpen} onOpenChange={setRunnerOpen}>
        <Dialog.Portal>
          <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/60" />
          <Dialog.Popup
            aria-label={t("runnerTitle")}
            className="fixed top-1/2 left-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-6 text-card-foreground"
          >
            <Dialog.Title className="text-base font-semibold">
              {t("runnerTitle")}
            </Dialog.Title>
            <Dialog.Description className="mt-2 text-sm text-muted-foreground">
              {t("runnerInfo")}
            </Dialog.Description>
            <div className="mt-6 flex justify-end">
              <Dialog.Close className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90">
                {t("close")}
              </Dialog.Close>
            </div>
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
