"use client";

import { Dialog } from "@base-ui/react/dialog";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { WizardField } from "@/components/bots/wizard-field";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { ApiHttpError } from "@/lib/api/client";
import { useDealAction, type DealAction } from "@/lib/api/queries";
import { isDecimalText } from "@/lib/bots";

/**
 * Açık deal eylemleri: fon ekle (tutar diyaloglu), piyasadan
 * kapat ve iptal (onaylı). Kapalı deal'de hiçbir şey çizilmez.
 * Revizyon çakışmasında kısa not gösterilir, liste yenilenir.
 */
export function DealActions({
  botId,
  seq,
  revision,
  open,
  testId,
}: {
  botId: string;
  seq: number;
  revision: number;
  open: boolean;
  testId: string;
}) {
  const t = useTranslations("deals");
  const tb = useTranslations("bots");
  const mutation = useDealAction();
  const [closeOpen, setCloseOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [fundsOpen, setFundsOpen] = useState(false);
  const [amount, setAmount] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  function run(action: DealAction, amountText?: string) {
    setNotice(null);
    mutation.mutate(
      { botId, seq, action, revision, amount: amountText },
      {
        onSuccess: () => {
          setCloseOpen(false);
          setCancelOpen(false);
          setFundsOpen(false);
          setAmount("");
        },
        onError: (error) => {
          if (error instanceof ApiHttpError && error.problem?.code === "BOT_REVISION_CONFLICT") {
            setNotice(tb("revisionConflict"));
            return;
          }
          setNotice(error instanceof Error ? error.message : "");
        },
      },
    );
  }

  if (!open && notice === null) return null;

  const amountOk = isDecimalText(amount) && amount !== "0";
  return (
    <div className="flex flex-col gap-1" data-testid={testId}>
      {open ? (
        <div className="flex flex-wrap gap-1">
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => setFundsOpen(true)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:cursor-wait disabled:opacity-60"
          >
            {t("addFunds")}
          </button>
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => setCloseOpen(true)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:cursor-wait disabled:opacity-60"
          >
            {t("closeAtMarket")}
          </button>
          <button
            type="button"
            disabled={mutation.isPending}
            onClick={() => setCancelOpen(true)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:cursor-wait disabled:opacity-60"
          >
            {t("cancelDeal")}
          </button>
        </div>
      ) : null}
      {notice === null ? null : (
        <p role="alert" className="text-xs text-muted-foreground">
          {notice}
        </p>
      )}
      <ConfirmDialog
        open={closeOpen}
        onOpenChange={setCloseOpen}
        title={t("closeTitle", { deal: seq })}
        description={t("closeHint")}
        confirmLabel={t("closeConfirm")}
        cancelLabel={t("dialogCancel")}
        onConfirm={() => run("close")}
      />
      <ConfirmDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        title={t("cancelTitle", { deal: seq })}
        description={t("cancelHint")}
        confirmLabel={t("cancelConfirm")}
        cancelLabel={t("dialogCancel")}
        onConfirm={() => run("cancel")}
      />
      <Dialog.Root open={fundsOpen} onOpenChange={setFundsOpen}>
        <Dialog.Portal>
          <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/60" />
          <Dialog.Popup
            aria-label={t("addFundsTitle", { deal: seq })}
            className="fixed top-1/2 left-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-6 text-card-foreground"
          >
            <Dialog.Title className="text-base font-semibold">
              {t("addFundsTitle", { deal: seq })}
            </Dialog.Title>
            <Dialog.Description className="mt-2 text-sm text-muted-foreground">
              {t("addFundsHint")}
            </Dialog.Description>
            <div className="mt-4">
              <WizardField
                label={t("addFundsLabel")}
                value={amount}
                onChange={setAmount}
                decimal
                testId="add-funds-amount"
              />
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Dialog.Close className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted">
                {t("dialogCancel")}
              </Dialog.Close>
              <button
                type="button"
                disabled={!amountOk || mutation.isPending}
                onClick={() => run("add-funds", amount)}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {t("addFundsConfirm")}
              </button>
            </div>
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
