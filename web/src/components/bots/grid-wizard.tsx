"use client";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { SymbolPicker } from "@/components/bots/symbol-picker";
import { WizardField } from "@/components/bots/wizard-field";
import { EnumValue } from "@/components/enum-value";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiHttpError } from "@/lib/api/client";
import {
  useFuturesGridBotCreate,
  useFuturesGridPreview,
  useGridBotCreate,
  useGridPreview,
  useSymbolRules,
  type FuturesGridPreviewBody,
  type GridPreviewBody,
} from "@/lib/api/queries";
import type { FuturesGridPreview, GridPreview } from "@/lib/api/schemas";
import {
  formToFuturesGridStrategy,
  formToGridStrategy,
  gridProblemFieldTarget,
  isDecimalText,
  type GridWizardForm,
} from "@/lib/bots";
import { cn } from "@/lib/utils";

export type WizardBotType = "DCA" | "GRID" | "FUTURES_GRID";

export function BotTypeSelector({
  value,
  onChange,
}: {
  value: WizardBotType;
  onChange: (value: WizardBotType) => void;
}) {
  const t = useTranslations("wizard");
  return (
    <fieldset data-testid="wizard-bot-type">
      <legend className="text-sm font-medium">{t("botTypeLabel")}</legend>
      <div className="mt-2 flex flex-wrap gap-2">
        {(["DCA", "GRID", "FUTURES_GRID"] as const).map((type) => (
          <button
            key={type}
            type="button"
            aria-pressed={value === type}
            onClick={() => onChange(type)}
            data-testid={`wizard-type-${type.toLowerCase()}`}
            className={cn(
              "rounded-lg border px-4 py-2 text-sm font-medium",
              value === type
                ? "border-accent bg-accent/12 text-accent"
                : "border-input text-muted-foreground hover:bg-muted",
            )}
          >
            {type === "DCA" ? t("botTypeDca") : type === "GRID" ? t("botTypeGrid") : t("botTypeFuturesGrid")}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

function useDebounced<T>(value: T, delayMs: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setSettled(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return settled;
}

function GridPreviewPanel({
  preview,
  state,
  errorText,
}: {
  preview: GridPreview | FuturesGridPreview | null;
  state: "waiting" | "loading" | "error" | "ready";
  errorText?: string;
}) {
  const t = useTranslations("wizard");
  const tg = useTranslations("grid");
  return (
    <Card data-testid="grid-preview-panel">
      <CardHeader>
        <CardTitle>
          <h2>{t("previewTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {state === "waiting" ? (
          <p className="text-sm text-muted-foreground">{t("previewWaiting")}</p>
        ) : state === "loading" ? (
          <p role="status" className="text-sm text-muted-foreground">
            …
          </p>
        ) : state === "error" ? (
          <p role="alert" className="text-sm text-loss">
            {errorText ?? t("previewError")}
          </p>
        ) : preview === null ? null : (
          <dl className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">{tg("entryPrice")}</dt>
              <dd className="font-mono">{preview.reference_price} USDT</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">{t("previewPosition")}</dt>
              <dd>
                <StatusBadge variant={preview.entry_position === "WITHIN" ? "running" : "warn"}>
                  <EnumValue code={preview.entry_position} />
                </StatusBadge>
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">{tg("intervalCount")}</dt>
              <dd className="font-mono">{preview.levels.length - 1}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">{t("previewPerGrid")}</dt>
              <dd className="font-mono">{preview.quote_per_grid} USDT</dd>
            </div>
            {"leverage" in preview ? (
              <>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{tg("direction")}</dt>
                  <dd className="font-mono">
                    {preview.direction} · {preview.leverage}x
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("previewNotional")}</dt>
                  <dd className="font-mono">{preview.notional_per_grid} USDT</dd>
                </div>
              </>
            ) : null}
            {preview.within_min_notional ? null : (
              <p role="alert" className="text-sm text-loss">
                {t("previewMinNotional")}
              </p>
            )}
          </dl>
        )}
      </CardContent>
    </Card>
  );
}

type FieldErrors = Partial<Record<string, string>>;

const GRID_STEPS = ["gridStep1", "gridStep2", "gridStep3"] as const;

function initialGridForm(prefillSymbol: string, market: "SPOT" | "FUTURES"): GridWizardForm {
  return {
    symbol: prefillSymbol,
    mode: "ARITHMETIC",
    lowerPrice: "",
    upperPrice: "",
    intervalCount: "10",
    budget: "",
    feeRate: market === "FUTURES" ? "0.0005" : "0.001",
    stopLossEnabled: false,
    stopLossPrice: "",
    takeProfitPct: "",
    trailingUpPct: "",
    trailingDownPct: "",
    name: "",
    direction: "LONG",
    leverage: market === "FUTURES" ? "5" : "1",
  };
}

export function GridWizard({
  onTypeChange,
  initialSymbol = "",
  market = "SPOT",
}: {
  onTypeChange: (value: WizardBotType) => void;
  initialSymbol?: string;
  market?: "SPOT" | "FUTURES";
}) {
  const t = useTranslations("wizard");
  const router = useRouter();
  const futures = market === "FUTURES";
  const [form, setForm] = useState<GridWizardForm>(() => initialGridForm(initialSymbol, market));
  const [step, setStep] = useState(1);
  const [submitErrors, setSubmitErrors] = useState<FieldErrors>({});

  const createSpot = useGridBotCreate();
  const createFutures = useFuturesGridBotCreate();
  const create = futures ? createFutures : createSpot;
  const rules = useSymbolRules(form.symbol);
  const supported = futures || rules.data?.data.bot_supported === true;

  function set<K extends keyof GridWizardForm>(key: K, value: GridWizardForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSubmitErrors((prev) => {
      if (!(key in prev)) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  const debounced = useDebounced(form, 400);
  const previewBody: GridPreviewBody | FuturesGridPreviewBody | null = useMemo(() => {
    const strategy = futures ? formToFuturesGridStrategy(debounced) : formToGridStrategy(debounced);
    if (strategy === null || !isDecimalText(debounced.budget)) return null;
    return { budget: debounced.budget, strategy };
  }, [debounced, futures]);
  const previewSpot = useGridPreview(futures ? null : (previewBody as GridPreviewBody | null));
  const previewFutures = useFuturesGridPreview(futures ? (previewBody as FuturesGridPreviewBody | null) : null);
  const preview = futures ? previewFutures : previewSpot;

  const previewErrors: FieldErrors = useMemo(() => {
    const error = preview.error;
    if (!(error instanceof ApiHttpError) || error.status !== 422) return {};
    const mapped: FieldErrors = {};
    for (const item of error.problem?.errors ?? []) {
      const target = gridProblemFieldTarget(item.field);
      if (target.key !== null) mapped[target.key] = error.problem?.detail ?? "";
    }
    if (error.problem?.errors?.some((item) => gridProblemFieldTarget(item.field).key === null)) {
      mapped.general = error.problem?.detail ?? "";
    }
    return mapped;
  }, [preview.error]);

  const errors: FieldErrors = useMemo(
    () => ({ ...previewErrors, ...submitErrors }),
    [previewErrors, submitErrors],
  );

  const defaultName =
    form.symbol === "" ? "" : `${form.symbol} ${futures ? t("botTypeFuturesGrid") : t("botTypeGrid")}`;

  function submit() {
    const strategy = futures ? formToFuturesGridStrategy(form) : formToGridStrategy(form);
    const nextErrors: FieldErrors = {};
    if (form.symbol === "" || !supported) nextErrors.symbol = t("symbolUnsupported");
    if (strategy === null) nextErrors.general = t("badFormat");
    if (!isDecimalText(form.budget)) nextErrors.budget = t("badFormat");
    if (Object.keys(nextErrors).length > 0) {
      setSubmitErrors((prev) => ({ ...prev, ...nextErrors }));
      if (nextErrors.symbol !== undefined) setStep(1);
      else setStep(2);
      return;
    }
    if (strategy === null || !isDecimalText(form.budget)) return;
    const payload = {
      name: form.name.trim() === "" ? defaultName : form.name.trim(),
      mode: "PAPER",
      budget: form.budget,
    };
    const handlers = {
      onSuccess: (envelope: { data: { bot_id: string } }) => router.push(`/bots/${envelope.data.bot_id}`),
      onError: (error: Error) => {
        if (error instanceof ApiHttpError && error.status === 422) {
          const mapped: FieldErrors = {};
          let firstStep = 3;
          for (const item of error.problem?.errors ?? []) {
            const target = gridProblemFieldTarget(item.field);
            if (target.key !== null) mapped[target.key] = error.problem?.detail ?? "";
            else mapped.general = error.problem?.detail ?? "";
            firstStep = Math.min(firstStep, target.step);
          }
          setSubmitErrors(mapped);
          setStep(firstStep);
        } else {
          setSubmitErrors({ general: error instanceof Error ? error.message : "" });
        }
      },
    };
    if (futures) {
      createFutures.mutate({ ...payload, strategy: strategy as FuturesGridPreviewBody["strategy"] }, handlers);
    } else {
      createSpot.mutate({ ...payload, strategy: strategy as GridPreviewBody["strategy"] }, handlers);
    }
  }

  const canNext = step !== 1 || supported;
  const plan = preview.data?.data ?? null;
  const previewState =
    previewBody === null ? "waiting" : preview.isPending ? "loading" : preview.isError ? "error" : "ready";

  return (
    <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1fr)_400px]">
      <div className="flex flex-col gap-4">
        <BotTypeSelector value={futures ? "FUTURES_GRID" : "GRID"} onChange={onTypeChange} />
        <ol aria-label={t("title")} className="flex gap-1 overflow-x-auto" data-testid="wizard-steps">
          {GRID_STEPS.map((key, index) => {
            const number = index + 1;
            const current = number === step;
            return (
              <li key={key} className="shrink-0">
                <button
                  type="button"
                  aria-current={current ? "step" : undefined}
                  onClick={() => setStep(number)}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium whitespace-nowrap",
                    current ? "bg-accent/12 text-accent" : "text-muted-foreground hover:bg-muted",
                  )}
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "flex size-5 items-center justify-center rounded-full font-mono text-xs",
                      current ? "bg-accent text-accent-foreground" : "bg-muted",
                    )}
                  >
                    {number}
                  </span>
                  {t(key)}
                </button>
              </li>
            );
          })}
        </ol>

        <Card data-testid={`wizard-step-${step}`}>
          <CardContent className="flex flex-col gap-4 pt-4">
            {step === 1 ? (
              <>
                <SymbolPicker value={form.symbol} onChange={(symbol) => set("symbol", symbol)} error={errors.symbol} />
                <fieldset>
                  <legend className="text-sm font-medium">{t("gridModeLabel")}</legend>
                  <div className="mt-2 flex gap-4 text-sm">
                    {(["ARITHMETIC", "GEOMETRIC"] as const).map((mode) => (
                      <label key={mode} className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="grid-mode"
                          checked={form.mode === mode}
                          onChange={() => set("mode", mode)}
                          data-testid={`grid-mode-${mode.toLowerCase()}`}
                        />
                        <EnumValue code={mode} />
                      </label>
                    ))}
                  </div>
                </fieldset>
                {futures ? (
                  <fieldset>
                    <legend className="text-sm font-medium">{t("directionLabel")}</legend>
                    <div className="mt-2 flex gap-4 text-sm">
                      {(["LONG", "SHORT"] as const).map((direction) => (
                        <label key={direction} className="flex items-center gap-2">
                          <input
                            type="radio"
                            name="grid-direction"
                            checked={form.direction === direction}
                            onChange={() => set("direction", direction)}
                            data-testid={`grid-direction-${direction.toLowerCase()}`}
                          />
                          {direction === "LONG" ? t("directionLong") : t("directionShort")}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                ) : null}
              </>
            ) : null}

            {step === 2 ? (
              <>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <WizardField decimal label={t("gridLower")} value={form.lowerPrice} onChange={(value) => set("lowerPrice", value)} error={errors.lowerPrice} testId="grid-lower" />
                  <WizardField decimal label={t("gridUpper")} value={form.upperPrice} onChange={(value) => set("upperPrice", value)} error={errors.lowerPrice} testId="grid-upper" />
                </div>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <WizardField label={t("gridCount")} value={form.intervalCount} onChange={(value) => set("intervalCount", value)} error={errors.intervalCount} inputMode="numeric" testId="grid-count" />
                  <WizardField decimal label={t("budget")} value={form.budget} onChange={(value) => set("budget", value)} hint={t("budgetHint")} error={errors.budget} testId="grid-budget" />
                </div>
                {futures ? (
                  <WizardField label={t("leverage")} value={form.leverage} onChange={(value) => set("leverage", value)} hint={t("leverageHint")} error={errors.leverage} inputMode="numeric" testId="grid-leverage" />
                ) : null}
                <WizardField decimal label={t("gridFee")} value={form.feeRate} onChange={(value) => set("feeRate", value)} error={errors.feeRate} testId="grid-fee" />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.stopLossEnabled}
                    onChange={(event) => set("stopLossEnabled", event.target.checked)}
                    data-testid="grid-sl-toggle"
                  />
                  {t("gridSlEnabled")}
                </label>
                {form.stopLossEnabled ? (
                  <WizardField decimal label={t("gridSlPrice")} value={form.stopLossPrice} onChange={(value) => set("stopLossPrice", value)} error={errors.stopLossPrice} testId="grid-sl" />
                ) : null}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <WizardField decimal label={t("gridTp")} value={form.takeProfitPct} onChange={(value) => set("takeProfitPct", value)} error={errors.takeProfitPct} testId="grid-tp" />
                  <WizardField decimal label={t("gridTrailUp")} value={form.trailingUpPct} onChange={(value) => set("trailingUpPct", value)} error={errors.trailingUpPct} testId="grid-trail-up" />
                  <WizardField decimal label={t("gridTrailDown")} value={form.trailingDownPct} onChange={(value) => set("trailingDownPct", value)} error={errors.trailingDownPct} testId="grid-trail-down" />
                </div>
                <WizardField label={t("name")} value={form.name} onChange={(value) => set("name", value)} placeholder={defaultName} inputMode="text" testId="grid-name" />
              </>
            ) : null}

            {step === 3 ? (
              <dl className="flex flex-col gap-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("symbolLabel")}</dt>
                  <dd className="font-mono">{form.symbol}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("gridModeLabel")}</dt>
                  <dd>
                    <EnumValue code={form.mode} />
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("gridRange")}</dt>
                  <dd className="font-mono">
                    {form.lowerPrice} – {form.upperPrice} ({form.intervalCount})
                  </dd>
                </div>
                {futures ? (
                  <>
                    <div className="flex justify-between gap-4">
                      <dt className="text-muted-foreground">{t("directionLabel")}</dt>
                      <dd>{form.direction === "LONG" ? t("directionLong") : t("directionShort")}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt className="text-muted-foreground">{t("leverage")}</dt>
                      <dd className="font-mono">{form.leverage}x</dd>
                    </div>
                  </>
                ) : null}
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("summaryBudget")}</dt>
                  <dd className="font-mono">{form.budget} USDT</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("summaryName")}</dt>
                  <dd>{form.name.trim() === "" ? defaultName : form.name.trim()}</dd>
                </div>
                {errors.general === undefined ? null : (
                  <p role="alert" className="text-sm text-loss">
                    {errors.general}
                  </p>
                )}
              </dl>
            ) : null}

            <div className="flex justify-between gap-2 border-t border-border pt-4">
              <button
                type="button"
                disabled={step === 1}
                onClick={() => setStep((value) => Math.max(1, value - 1))}
                className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
              >
                {t("back")}
              </button>
              {step < 3 ? (
                <button
                  type="button"
                  disabled={!canNext}
                  title={step === 1 && !canNext ? t("symbolUnsupported") : undefined}
                  onClick={() => setStep((value) => Math.min(3, value + 1))}
                  className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
                >
                  {t("next")}
                </button>
              ) : (
                <button
                  type="button"
                  disabled={create.isPending}
                  onClick={submit}
                  data-testid="wizard-create"
                  className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
                >
                  {create.isPending ? t("creating") : t("create")}
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="lg:sticky lg:top-4">
        <GridPreviewPanel
          preview={plan}
          state={previewState}
          errorText={preview.error instanceof Error ? preview.error.message : undefined}
        />
      </div>
    </div>
  );
}
