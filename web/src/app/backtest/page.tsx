"use client";

import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useRef, useState } from "react";

import { BacktestResults } from "@/components/backtest/backtest-results";
import { PresetPicker } from "@/components/bots/preset-picker";
import { StrategyFields } from "@/components/bots/strategy-fields";
import { SymbolPicker } from "@/components/bots/symbol-picker";
import { WizardField } from "@/components/bots/wizard-field";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiHttpError } from "@/lib/api/client";
import { useBacktestRun, useSymbolRules } from "@/lib/api/queries";
import {
  BACKTEST_INTERVALS,
  MAX_BACKTEST_BARS,
  QUICK_RANGES,
  backtestFieldTarget,
  defaultBacktestRange,
  estimateBarCount,
  parseBacktestPrefill,
  quickRangeStart,
  wizardFormToSearchParams,
  type BacktestInterval,
} from "@/lib/backtest";
import {
  PRESETS,
  detectPreset,
  formToStrategy,
  isDecimalText,
  type PresetId,
  type WizardForm,
} from "@/lib/bots";
import { cn } from "@/lib/utils";

function initialForm(prefill: ReturnType<typeof parseBacktestPrefill>): WizardForm {
  const preset = PRESETS.balanced;
  return {
    symbol: prefill.symbol ?? "",
    extraSymbols: prefill.extraSymbols ?? "",
    direction: prefill.direction ?? "LONG",
    market: prefill.market ?? "SPOT",
    leverage: prefill.leverage ?? "",
    cooldown: prefill.cooldown ?? "",
    minPrice: prefill.minPrice ?? "",
    maxPrice: prefill.maxPrice ?? "",
    baseOrder: prefill.baseOrder ?? preset.baseOrder,
    safetyOrder: prefill.safetyOrder ?? preset.safetyOrder,
    maxSafetyOrders: prefill.maxSafetyOrders ?? preset.maxSafetyOrders,
    maxActiveSafetyOrders: prefill.maxActiveSafetyOrders ?? preset.maxActiveSafetyOrders,
    maxActiveDeals: prefill.maxActiveDeals ?? "",
    priceDeviation: prefill.priceDeviation ?? preset.priceDeviation,
    volumeScale: prefill.volumeScale ?? preset.volumeScale,
    stepScale: prefill.stepScale ?? preset.stepScale,
    takeProfit: prefill.takeProfit ?? preset.takeProfit,
    comboTakeProfit: prefill.comboTakeProfit ?? "",
    trailingEnabled: prefill.trailingEnabled ?? false,
    trailingTakeProfit: prefill.trailingTakeProfit ?? preset.trailingTakeProfit,
    stopLossEnabled: prefill.stopLossEnabled ?? false,
    stopLoss: prefill.stopLoss ?? preset.stopLoss,
    budget: prefill.budget ?? "",
    name: prefill.name ?? "",
  };
}

type FieldErrors = Partial<Record<string, string>>;

function BacktestInner() {
  const t = useTranslations("backtest");
  const tw = useTranslations("wizard");
  const locale = useLocale();
  const searchParams = useSearchParams();
  const prefill = useMemo(() => parseBacktestPrefill(searchParams), [searchParams]);
  const [form, setForm] = useState<WizardForm>(() => initialForm(prefill));
  const [interval, setInterval] = useState<BacktestInterval>(prefill.interval ?? "1h");
  const [range, setRange] = useState(() => {
    const fallback = defaultBacktestRange();
    return {
      start: prefill.startDate ?? fallback.start,
      end: prefill.endDate ?? fallback.end,
    };
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const run = useBacktestRun();
  const abortRef = useRef<AbortController | null>(null);

  const rules = useSymbolRules(form.symbol);
  const supported = rules.data?.data.bot_supported === true;
  const preset = detectPreset(form);

  function set<K extends keyof WizardForm>(key: K, value: WizardForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      if (!(key in prev)) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function applyPreset(id: Exclude<PresetId, "custom">) {
    setForm((prev) => ({ ...prev, ...PRESETS[id] }));
    setErrors({});
  }

  const estimated = estimateBarCount(interval, range.start, range.end);
  const tooLarge = estimated !== null && estimated > MAX_BACKTEST_BARS;
  const canRun = supported && !tooLarge && estimated !== null;

  function submit() {
    const strategy = formToStrategy(form);
    const nextErrors: FieldErrors = {};
    if (form.symbol === "" || !supported) nextErrors.symbol = tw("symbolUnsupported");
    if (strategy === null) nextErrors.general = tw("badFormat");
    if (!isDecimalText(form.budget)) nextErrors.budget = tw("badFormat");
    if (estimated === null) nextErrors.startDate = tw("badFormat");
    if (Object.keys(nextErrors).length > 0) {
      setErrors((prev) => ({ ...prev, ...nextErrors }));
      return;
    }
    if (strategy === null || !isDecimalText(form.budget) || estimated === null) return;
    setErrors({});
    const controller = new AbortController();
    abortRef.current = controller;
    run.mutate(
      {
        body: {
          budget: form.budget,
          strategy,
          interval,
          start_date: range.start,
          end_date: range.end,
        },
        signal: controller.signal,
      },
      {
        onError: (error) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          if (error instanceof ApiHttpError && error.status === 422) {
            const mapped: FieldErrors = {};
            for (const item of error.problem?.errors ?? []) {
              const target = backtestFieldTarget(item.field);
              if (target === null) mapped.general = error.problem?.detail ?? "";
              else mapped[target] = error.problem?.detail ?? "";
            }
            setErrors(mapped);
          } else {
            setErrors({ general: error instanceof Error ? error.message : "" });
          }
        },
      },
    );
  }

  const setupHref = useMemo(() => {
    const params = wizardFormToSearchParams(form);
    return `/bots/new?${params.toString()}`;
  }, [form]);

  const numberFormat = useMemo(() => new Intl.NumberFormat(locale), [locale]);
  const result = run.data?.data ?? null;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[400px_minmax(0,1fr)]">
        {/* Form (sol) */}
        <Card>
          <CardHeader>
            <CardTitle>
              <h2>{t("formTitle")}</h2>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <SymbolPicker value={form.symbol} onChange={(symbol) => set("symbol", symbol)} error={errors.symbol} />
            <PresetPicker preset={preset} onPreset={applyPreset} />
            <StrategyFields
              form={form}
              errors={errors}
              minNotional={rules.data?.data.min_notional}
              onChange={set}
            />
            <WizardField
              decimal
              label={tw("budget")}
              value={form.budget}
              onChange={(value) => set("budget", value)}
              hint={tw("budgetHint")}
              error={errors.budget}
              testId="backtest-budget"
            />
            <fieldset>
              <legend className="text-sm font-medium">{t("intervalLabel")}</legend>
              <div className="mt-2 flex flex-wrap gap-1" role="radiogroup" aria-label={t("intervalLabel")}>
                {BACKTEST_INTERVALS.map((id) => (
                  <button
                    key={id}
                    type="button"
                    role="radio"
                    aria-checked={interval === id}
                    onClick={() => setInterval(id)}
                    className={cn(
                      "rounded-md px-3 py-1.5 font-mono text-sm font-medium",
                      interval === id
                        ? "bg-accent/12 text-accent"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {id}
                  </button>
                ))}
              </div>
              {errors.interval === undefined ? null : (
                <p role="alert" className="mt-1 text-xs text-loss">
                  {errors.interval}
                </p>
              )}
            </fieldset>
            <div className="grid grid-cols-1 gap-4 min-[420px]:grid-cols-2">
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="font-medium">{t("startLabel")}</span>
                <input
                  type="date"
                  value={range.start}
                  onChange={(event) => {
                    setRange((prev) => ({ ...prev, start: event.target.value }));
                    setErrors((prev) => {
                      if (prev.startDate === undefined) return prev;
                      const next = { ...prev };
                      delete next.startDate;
                      return next;
                    });
                  }}
                  data-testid="backtest-start"
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                {errors.startDate === undefined ? null : (
                  <span role="alert" className="text-xs text-loss">
                    {errors.startDate}
                  </span>
                )}
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="font-medium">{t("endLabel")}</span>
                <input
                  type="date"
                  value={range.end}
                  onChange={(event) => {
                    setRange((prev) => ({ ...prev, end: event.target.value }));
                    setErrors((prev) => {
                      if (prev.endDate === undefined) return prev;
                      const next = { ...prev };
                      delete next.endDate;
                      return next;
                    });
                  }}
                  data-testid="backtest-end"
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                {errors.endDate === undefined ? null : (
                  <span role="alert" className="text-xs text-loss">
                    {errors.endDate}
                  </span>
                )}
              </label>
            </div>
            <div className="flex flex-wrap gap-1" role="group" aria-label={t("startLabel")}>
              {QUICK_RANGES.map((chip) => (
                <button
                  key={chip.id}
                  type="button"
                  onClick={() => {
                    const start = quickRangeStart(range.end, chip.days);
                    if (start !== null) {
                      setRange((prev) => ({ ...prev, start }));
                      setErrors((prev) => {
                        if (prev.startDate === undefined) return prev;
                        const next = { ...prev };
                        delete next.startDate;
                        return next;
                      });
                    }
                  }}
                  className="rounded-md px-3 py-1.5 font-mono text-sm font-medium text-muted-foreground hover:bg-muted"
                >
                  {t(
                    chip.id === "30d"
                      ? "quick30d"
                      : chip.id === "90d"
                        ? "quick90d"
                        : chip.id === "180d"
                          ? "quick180d"
                          : "quick1y",
                  )}
                </button>
              ))}
            </div>
            {estimated === null ? null : (
              <p className="font-mono text-xs text-muted-foreground" data-testid="backtest-estimate">
                {t("estimatedBars", { n: numberFormat.format(estimated) })}
              </p>
            )}
            {errors.general === undefined ? null : (
              <p role="alert" className="text-sm text-loss">
                {errors.general}
              </p>
            )}
            {tooLarge ? (
              <p role="alert" className="rounded-md bg-safety/15 px-3 py-2 text-sm font-medium text-safety">
                {t("rangeWarning")}
              </p>
            ) : (
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={!canRun || run.isPending}
                  onClick={submit}
                  data-testid="backtest-run"
                  className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
                >
                  {t("run")}
                </button>
                {run.isPending ? (
                  <button
                    type="button"
                    onClick={() => abortRef.current?.abort()}
                    className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                  >
                    {t("cancel")}
                  </button>
                ) : null}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sonuç (sağ) */}
        <div className="flex min-w-0 flex-col gap-4" data-testid="backtest-results-pane">
          {run.isPending ? (
            <div className="flex flex-col gap-3" role="status" aria-label={t("running")}>
              <p className="text-sm text-muted-foreground">{t("running")}</p>
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-60 w-full" />
            </div>
          ) : result === null ? (
            <EmptyState title={t("waitingResults")} />
          ) : (
            <BacktestResults result={result} setupHref={setupHref} />
          )}
        </div>
      </div>
    </div>
  );
}

export default function BacktestPage() {
  return (
    <Suspense>
      <BacktestInner />
    </Suspense>
  );
}
