"use client";

import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { BotTypeSelector, GridWizard, type WizardBotType } from "@/components/bots/grid-wizard";
import { PresetPicker } from "@/components/bots/preset-picker";
import { PreviewPanel } from "@/components/bots/preview-panel";
import { StrategyFields } from "@/components/bots/strategy-fields";
import { SymbolPicker } from "@/components/bots/symbol-picker";
import { WizardField } from "@/components/bots/wizard-field";
import { Card, CardContent } from "@/components/ui/card";
import { ApiHttpError } from "@/lib/api/client";
import { parseBacktestPrefill, wizardFormToSearchParams } from "@/lib/backtest";
import {
  useBotCreate,
  useBotPreview,
  useSymbolRules,
  type BotPreviewBody,
} from "@/lib/api/queries";
import {
  PRESETS,
  detectPreset,
  formToStrategy,
  isDecimalText,
  problemFieldTarget,
  type PresetId,
  type WizardForm,
} from "@/lib/bots";

const PREVIEW_DEBOUNCE_MS = 400;

// 422 eşlemesindeki alan anahtarı → odakta kaydırılacak test kimliği.
// Radyo gruplarında grubun ilk seçeneği hedeflenir.
const FIELD_TESTIDS: Record<string, string> = {
  symbol: "wizard-symbol",
  extraSymbols: "wizard-extra-symbols",
  direction: "wizard-direction-long",
  market: "wizard-market-spot",
  leverage: "wizard-leverage",
  cooldown: "wizard-cooldown",
  minPrice: "wizard-min-price",
  maxPrice: "wizard-max-price",
  baseOrder: "wizard-base-order",
  maxActiveDeals: "wizard-max-active-deals",
  safetyOrder: "wizard-safety-order",
  maxSafetyOrders: "wizard-max-safety-orders",
  maxActiveSafetyOrders: "wizard-max-active-safety-orders",
  priceDeviation: "wizard-price-deviation",
  volumeScale: "wizard-volume-scale",
  stepScale: "wizard-safety-step-scale",
  takeProfit: "wizard-take-profit",
  comboTakeProfit: "wizard-combo-take-profit",
  trailingTakeProfit: "wizard-trailing-take-profit",
  stopLoss: "wizard-stop-loss",
  budget: "wizard-budget",
  name: "wizard-name",
};

function fieldTestId(key: string): string {
  return FIELD_TESTIDS[key] ?? "wizard-summary";
}

function focusTestId(testId: string) {
  window.setTimeout(() => {
    const el = document.querySelector(`[data-testid="${testId}"]`);
    if (el instanceof HTMLElement) {
      el.scrollIntoView({ block: "center" });
      el.focus({ preventScroll: true });
    }
  }, 0);
}

function useDebounced<T>(value: T, delayMs: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setSettled(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return settled;
}

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

function WizardInner() {
  const t = useTranslations("wizard");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState<WizardForm>(() =>
    initialForm(parseBacktestPrefill(searchParams)),
  );
  const [botType, setBotType] = useState<WizardBotType>("DCA");
  const [submitErrors, setSubmitErrors] = useState<FieldErrors>({});

  const create = useBotCreate();
  const rules = useSymbolRules(form.symbol);
  const supported = rules.data?.data.bot_supported === true;

  function set<K extends keyof WizardForm>(key: K, value: WizardForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSubmitErrors((prev) => {
      if (!(key in prev)) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function applyPreset(id: Exclude<PresetId, "custom">) {
    const preset = PRESETS[id];
    setForm((prev) => ({ ...prev, ...preset }));
    setSubmitErrors({});
  }

  const preset = detectPreset(form);
  const debounced = useDebounced(form, PREVIEW_DEBOUNCE_MS);
  const previewBody: BotPreviewBody | null = useMemo(() => {
    const strategy = formToStrategy(debounced);
    if (strategy === null || !isDecimalText(debounced.budget)) return null;
    return { budget: debounced.budget, strategy };
  }, [debounced]);
  const preview = useBotPreview(previewBody);

  // Önizleme 422'leri alanların altında gösterilir (metin backend'indir).
  // Türetilmiş değerdir; başarılı yanıtta kendiliğinden temizlenir.
  const previewErrors: FieldErrors = useMemo(() => {
    const error = preview.error;
    if (!(error instanceof ApiHttpError) || error.status !== 422) return {};
    const mapped: FieldErrors = {};
    for (const item of error.problem?.errors ?? []) {
      const target = problemFieldTarget(item.field);
      if (target.key !== null) mapped[target.key] = error.problem?.detail ?? "";
    }
    if (error.problem?.errors?.some((item) => problemFieldTarget(item.field).key === null)) {
      mapped.general = error.problem?.detail ?? "";
    }
    return mapped;
  }, [preview.error]);

  const errors: FieldErrors = useMemo(
    () => ({ ...previewErrors, ...submitErrors }),
    [previewErrors, submitErrors],
  );

  const plan = preview.data?.data ?? null;
  const previewState =
    previewBody === null
      ? "waiting"
      : preview.isPending
        ? "loading"
        : preview.isError
          ? "error"
          : "ready";
  const previewErrorText =
    preview.error instanceof Error ? preview.error.message : undefined;

  const defaultName = form.symbol === "" ? "" : `${form.symbol} DCA`;

  function submit() {
    const strategy = formToStrategy(form);
    const nextErrors: FieldErrors = {};
    if (form.symbol === "" || !supported) nextErrors.symbol = t("symbolUnsupported");
    if (strategy === null) nextErrors.general = t("badFormat");
    if (!isDecimalText(form.budget)) nextErrors.budget = t("badFormat");
    if (Object.keys(nextErrors).length > 0) {
      setSubmitErrors((prev) => ({ ...prev, ...nextErrors }));
      if (nextErrors.symbol !== undefined) focusTestId(fieldTestId("symbol"));
      else if (nextErrors.budget !== undefined) focusTestId(fieldTestId("budget"));
      else focusTestId("wizard-summary");
      return;
    }
    if (strategy === null || !isDecimalText(form.budget)) return;
    create.mutate(
      {
        name: form.name.trim() === "" ? defaultName : form.name.trim(),
        mode: "PAPER",
        budget: form.budget,
        strategy,
      },
      {
        onSuccess: (envelope) => router.push(`/bots/${envelope.data.bot_id}`),
        onError: (error) => {
          if (error instanceof ApiHttpError && error.status === 422) {
            const mapped: FieldErrors = {};
            let first = { order: 8, testId: "wizard-summary" };
            for (const item of error.problem?.errors ?? []) {
              const target = problemFieldTarget(item.field);
              if (target.key !== null) {
                mapped[target.key] = error.problem?.detail ?? "";
                const testId = FIELD_TESTIDS[target.key];
                if (testId !== undefined && target.step < first.order) {
                  first = { order: target.step, testId };
                }
              } else {
                mapped.general = error.problem?.detail ?? "";
              }
            }
            setSubmitErrors(mapped);
            focusTestId(first.testId);
          } else {
            setSubmitErrors({ general: error instanceof Error ? error.message : "" });
          }
        },
      },
    );
  }

  const minNotional = rules.data?.data.min_notional;

  if (botType === "GRID" || botType === "FUTURES_GRID") {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
        <GridWizard
          onTypeChange={setBotType}
          initialSymbol={form.symbol}
          market={botType === "FUTURES_GRID" ? "FUTURES" : "SPOT"}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
      <BotTypeSelector value={botType} onChange={setBotType} />
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1fr)_400px]">
        {/* 3Commas tarzı tek-sayfa form: bölümler üst üste, adım gezgini yok. */}
        <Card>
          <CardContent className="flex flex-col gap-6 pt-4">
            <section aria-labelledby="wizard-section-1" className="flex flex-col gap-4">
              <h2 id="wizard-section-1" className="text-sm font-semibold">
                {t("step1")}
              </h2>
              <SymbolPicker
                value={form.symbol}
                onChange={(symbol) => set("symbol", symbol)}
                error={errors.symbol}
              />
              <WizardField
                label={t("extraSymbols")}
                value={form.extraSymbols}
                onChange={(value) => set("extraSymbols", value)}
                hint={t("extraSymbolsHint")}
                error={errors.extraSymbols}
                placeholder="ETHUSDT, SOLUSDT"
                testId="wizard-extra-symbols"
              />
              <fieldset>
                <legend className="text-sm font-medium">{t("modeLabel")}</legend>
                <div className="mt-2 flex gap-4 text-sm">
                  <label className="flex items-center gap-2">
                    <input type="radio" name="wizard-mode" checked readOnly />
                    {t("paperMode")}
                  </label>
                  <label
                    className="flex items-center gap-2 text-muted-foreground"
                    title={t("testnetHint")}
                  >
                    <input type="radio" name="wizard-mode" disabled />
                    {t("testnetMode")}
                  </label>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{t("testnetHint")}</p>
              </fieldset>
            </section>

            {/* Hazır ayar başlığı seçicinin kendisindedir; çift başlık çıkmasın. */}
            <section className="flex flex-col gap-4 border-t border-border pt-4">
              <PresetPicker preset={preset} onPreset={applyPreset} />
            </section>

            <section
              aria-labelledby="wizard-section-3"
              className="flex flex-col gap-4 border-t border-border pt-4"
            >
              <h2 id="wizard-section-3" className="text-sm font-semibold">
                {t("step3")}
              </h2>
              <StrategyFields
                form={form}
                errors={errors}
                minNotional={minNotional}
                onChange={set}
                include={["entry"]}
                testIdPrefix="wizard"
              />
            </section>

            <section
              aria-labelledby="wizard-section-4"
              className="flex flex-col gap-4 border-t border-border pt-4"
            >
              <h2 id="wizard-section-4" className="text-sm font-semibold">
                {t("step4")}
              </h2>
              <StrategyFields
                form={form}
                errors={errors}
                minNotional={minNotional}
                onChange={set}
                include={["safety"]}
                testIdPrefix="wizard"
              />
            </section>

            <section
              aria-labelledby="wizard-section-5"
              className="flex flex-col gap-4 border-t border-border pt-4"
            >
              <h2 id="wizard-section-5" className="text-sm font-semibold">
                {t("step5")}
              </h2>
              <StrategyFields
                form={form}
                errors={errors}
                minNotional={minNotional}
                onChange={set}
                include={["exit"]}
                testIdPrefix="wizard"
              />
            </section>

            <section
              aria-labelledby="wizard-section-6"
              className="flex flex-col gap-4 border-t border-border pt-4"
            >
              <h2 id="wizard-section-6" className="text-sm font-semibold">
                {t("step6")}
              </h2>
              <WizardField
                decimal
                label={t("budget")}
                value={form.budget}
                onChange={(value) => set("budget", value)}
                hint={t("budgetHint")}
                error={errors.budget}
                testId="wizard-budget"
              />
              {plan === null ? null : (
                <button
                  type="button"
                  onClick={() => set("budget", plan.required_funds)}
                  className="w-fit rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted"
                >
                  {t("useRequired")}
                </button>
              )}
              <WizardField
                label={t("name")}
                value={form.name}
                onChange={(value) => set("name", value)}
                placeholder={defaultName}
                inputMode="text"
                testId="wizard-name"
              />
            </section>

            <section
              aria-labelledby="wizard-section-7"
              className="flex flex-col gap-4 border-t border-border pt-4"
            >
              <h2 id="wizard-section-7" className="text-sm font-semibold">
                {t("step7")}
              </h2>
              <dl data-testid="wizard-summary" className="flex flex-col gap-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("symbolLabel")}</dt>
                  <dd className="font-mono">{form.symbol}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("directionLabel")}</dt>
                  <dd>{form.direction === "LONG" ? t("directionLong") : t("directionShort")}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("summaryMode")}</dt>
                  <dd>{t("paperMode")}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">{t("presetLabel")}</dt>
                  <dd>
                    {preset === "custom"
                      ? t("presetCustom")
                      : preset === "conservative"
                        ? t("presetConservative")
                        : preset === "balanced"
                          ? t("presetBalanced")
                          : t("presetAggressive")}
                  </dd>
                </div>
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
            </section>

            <div className="flex flex-wrap justify-end gap-2 border-t border-border pt-4">
              <button
                type="button"
                onClick={() =>
                  router.push(`/backtest?${wizardFormToSearchParams(form).toString()}`)
                }
                className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
              >
                {t("backtestFirst")}
              </button>
              <button
                type="button"
                disabled={create.isPending}
                onClick={submit}
                data-testid="wizard-create"
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:opacity-50"
              >
                {create.isPending ? t("creating") : t("create")}
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Yapışkan önizleme; mobilde formun altına iner. */}
        <div className="lg:sticky lg:top-4">
          <PreviewPanel
            symbol={form.symbol}
            plan={plan}
            budget={form.budget}
            state={previewState}
            errorText={previewErrorText}
            comboTakeProfit={isDecimalText(form.comboTakeProfit) ? form.comboTakeProfit : null}
          />
        </div>
      </div>
    </div>
  );
}

export default function BotsNewPage() {
  return (
    <Suspense>
      <WizardInner />
    </Suspense>
  );
}
