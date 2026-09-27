"use client";

import { AlertDialog } from "@base-ui/react/alert-dialog";
import { useState } from "react";

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel,
  onConfirm,
  reasonLabel,
  reasonPlaceholder,
  reasonRequired = false,
}: {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel: string;
  /** Gerekçe alanıyla birlikte çağrılır (alan yoksa `undefined`). */
  onConfirm: (reason: string | undefined) => void;
  /** Verilirse isteğe bağlı gerekçe alanı açılır. */
  reasonLabel?: string;
  reasonPlaceholder?: string;
  /** Doğruysa gerekçe boşken onay düğmesi devre dışı kalır. */
  reasonRequired?: boolean;
}) {
  const [reason, setReason] = useState("");
  const reasonOk = !reasonRequired || reason.trim() !== "";
  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Backdrop className="fixed inset-0 z-50 bg-black/60" />
        <AlertDialog.Popup className="fixed top-1/2 left-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-6 text-card-foreground">
          <AlertDialog.Title className="text-base font-semibold">
            {title}
          </AlertDialog.Title>
          <AlertDialog.Description className="mt-2 text-sm text-muted-foreground">
            {description}
          </AlertDialog.Description>
          {reasonLabel === undefined ? null : (
            <label className="mt-4 flex flex-col gap-1.5 text-sm">
              <span className="font-medium">{reasonLabel}</span>
              <input
                type="text"
                value={reason}
                required={reasonRequired}
                aria-required={reasonRequired || undefined}
                onChange={(event) => setReason(event.target.value)}
                placeholder={reasonPlaceholder}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          )}
          <div className="mt-6 flex justify-end gap-2">
            <AlertDialog.Close className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted">
              {cancelLabel}
            </AlertDialog.Close>
            <button
              type="button"
              disabled={!reasonOk}
              onClick={() => {
                onConfirm(reasonLabel === undefined ? undefined : reason.trim());
                setReason("");
              }}
              className="rounded-md bg-loss px-4 py-2 text-sm font-medium text-white hover:bg-loss/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {confirmLabel}
            </button>
          </div>
        </AlertDialog.Popup>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
