"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";

import { looksLikeThousandsSeparator } from "@/lib/bots";
import { cn } from "@/lib/utils";

/**
 * Sihirbaz metin alanı: etiket + giriş + ipucu + alan hatası.
 * `decimal` alanlarda virgül noktaya çevrilir ("1,5" → "1.5");
 * binlik ayırıcı şüphesinde amber uyarı gösterilir.
 */
export function WizardField({
  label,
  value,
  onChange,
  hint,
  error,
  placeholder,
  inputMode = "decimal",
  decimal = false,
  testId,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
  error?: string;
  placeholder?: string;
  inputMode?: "decimal" | "numeric" | "text";
  decimal?: boolean;
  testId?: string;
}) {
  const t = useTranslations("wizard");
  const hintId = useId();
  const errorId = useId();
  const warningId = useId();
  const warning = decimal && error === undefined && looksLikeThousandsSeparator(value);
  const describedBy =
    error !== undefined ? errorId : warning ? warningId : hint !== undefined ? hintId : undefined;
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium">{label}</span>
      <input
        type="text"
        inputMode={inputMode}
        value={value}
        placeholder={placeholder}
        aria-invalid={error !== undefined || undefined}
        aria-describedby={describedBy}
        data-testid={testId}
        onChange={(event) => {
          const raw = event.target.value;
          onChange(decimal ? raw.replace(/,/g, ".") : raw);
        }}
        className={cn(
          "rounded-md border bg-background px-3 py-2 font-mono text-sm outline-none",
          "focus-visible:ring-2 focus-visible:ring-ring",
          error !== undefined ? "border-loss" : "border-input",
        )}
      />
      {hint !== undefined && error === undefined && !warning ? (
        <span id={hintId} className="text-xs text-muted-foreground">
          {hint}
        </span>
      ) : null}
      {warning ? (
        <span id={warningId} role="status" className="text-xs font-medium text-safety">
          {t("thousandsWarning")}
        </span>
      ) : null}
      {error !== undefined ? (
        <span id={errorId} role="alert" className="text-xs text-loss">
          {error}
        </span>
      ) : null}
    </label>
  );
}
