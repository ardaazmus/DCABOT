import { useState } from "react";

import type { BotRegisterPayload } from "./BotPanel";
import { CandleChart } from "./CandleChart";
import type { HistoricalChartBar } from "./datasetCatalog";
import { isTemplateDetail, isTemplateMetaList, type TemplateMeta } from "./TemplatePanel";
import {
  AdvancedDetails,
  BudgetSlider,
  CalculatedPreview,
  ConditionalField,
  FieldGroup,
  LabeledSlider,
  NumericParameter,
  QuickPercentChips,
  RiskCritical,
  SegmentedControl,
  StepperInput,
  TextParameter,
  ToggleSwitchRow,
} from "./forms";
import { useI18n } from "./i18n";
import { SIGNAL_WEBHOOK_PATH } from "./SignalPanel";

/**
 * Faz 12.2: birleşik "Bot Oluştur" akışı — eski 5 adım (Kimlik/Pariteler/
 * Listeler/Bütçe/Önizleme) ile "Bot stüdyosu" parametreleri tek sihirbazda:
 * Kimlik+Parite → Giriş → Çıkış → Bütçe → Önizleme+Backtest.
 * Giriş/Çıkış değerleri istemci-taraflı TASLAK'tır (localStorage, bot_id
 * anahtarlı); sunucu stratejisi değil. Kayıt yükü (BotRegisterPayload)
 * değişmedi; yetki backend'dedir.
 */

const IDENTIFIER = /^[A-Za-z0-9_.:-]{1,100}$/;
const SYMBOL = /^[A-Z0-9]{3,20}$/;
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;
const COUNT = /^(?:0|[1-9]\d*)$/;

export const STRATEGY_DRAFT_PREFIX = "dcabot-strategy-draft:";

export type StartCondition = "immediate" | "indicator" | "webhook";

export type IndicatorKind = "sma" | "ema";
export type CrossCondition = "up" | "down";

export type WizardDraft = {
  botId: string;
  name: string;
  pairs: string;
  blacklist: string;
  favorites: string;
  startCondition: StartCondition;
  indicatorKind: IndicatorKind;
  fastWindow: string;
  slowWindow: string;
  crossCondition: CrossCondition;
  baseQty: string;
  safetyQty: string;
  safetyCount: string;
  deviation: string;
  volumeMult: string;
  stepMult: string;
  takeProfit: string;
  stopLoss: string;
  trailingStop: string;
  budget: string;
};

const INITIAL_DRAFT: WizardDraft = {
  botId: "",
  name: "",
  pairs: "",
  blacklist: "",
  favorites: "",
  startCondition: "immediate",
  indicatorKind: "sma",
  fastWindow: "9",
  slowWindow: "21",
  crossCondition: "up",
  baseQty: "0.001",
  safetyQty: "0.002",
  safetyCount: "3",
  deviation: "0.02",
  volumeMult: "2",
  stepMult: "1.5",
  takeProfit: "0.01",
  stopLoss: "",
  trailingStop: "",
  budget: "",
};

/* Faz 15.2: exact metin durakları — slider/çip konumu bu listeden seçilir,
 * UI'da oran hesabı yapılmaz (eşleme tablosu disiplini). */
const MULTIPLIER_STOPS = ["1", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "2"];
const TAKE_PROFIT_CHIPS = [
  { chip: "0.5%", ratio: "0.005" },
  { chip: "1%", ratio: "0.01" },
  { chip: "2%", ratio: "0.02" },
  { chip: "5%", ratio: "0.05" },
  { chip: "10%", ratio: "0.1" },
];

const STEP_KEYS = [
  "wizard.identityPairs.label",
  "wizard.entry.label",
  "wizard.exit.label",
  "wizard.budget.label",
  "wizard.preview.label",
] as const;

function parseCsv(raw: string): string[] {
  return raw.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
}

/* Faz 15.3: şablon yükü (snake_case Config anahtarları) → taslak alanları.
 * Yalnız string değerler alınır (safety_count için tam-sayı da kabul);
 * bilinmeyen anahtarlar yoksayılır, sunucu doğrulaması değişmez. */
type WizardPresetField = "baseQty" | "safetyQty" | "safetyCount" | "deviation" | "volumeMult" | "stepMult" | "takeProfit";

const PRESET_FIELD_MAP: { key: string; draft: WizardPresetField }[] = [
  { key: "base_qty", draft: "baseQty" },
  { key: "safety_qty", draft: "safetyQty" },
  { key: "safety_count", draft: "safetyCount" },
  { key: "deviation", draft: "deviation" },
  { key: "volume_multiplier", draft: "volumeMult" },
  { key: "step_multiplier", draft: "stepMult" },
  { key: "take_profit", draft: "takeProfit" },
];

function PairListInput({ value, onChange }: { value: string; onChange: (csv: string) => void }) {
  const { t } = useI18n();
  const rows = value === "" ? [""] : value.split(",");
  const rowLabel = t("wizard.pairs.row");
  function setRow(index: number, next: string) {
    const copy = rows.slice();
    copy[index] = next;
    onChange(copy.join(","));
  }
  function addRow() {
    onChange(rows.concat("").join(","));
  }
  function removeRow(index: number) {
    if (rows.length <= 1) {
      onChange("");
      return;
    }
    onChange(rows.filter((_, i) => i !== index).join(","));
  }
  return (
    <div className="pair-list-field">
      <span className="field-label">{t("wizard.pairs.label")}</span>
      {rows.map((row, index) => (
        <div className="pair-row" key={index}>
          <span className="input-wrap pair-input-wrap">
            <input aria-label={`${rowLabel} ${index + 1}`} value={row} onChange={(event) => setRow(index, event.target.value)} />
          </span>
          <button
            type="button"
            className="secondary-button pair-remove"
            aria-label={`${rowLabel} ${index + 1} ${t("wizard.pairs.remove")}`}
            onClick={() => removeRow(index)}
          >
            ×
          </button>
        </div>
      ))}
      <button type="button" className="secondary-button pair-add" onClick={addRow}>
        {t("wizard.pairs.add")}
      </button>
    </div>
  );
}

function stepError(step: number, draft: WizardDraft, t: (key: string) => string): string {
  if (step === 0) {
    if (!IDENTIFIER.test(draft.botId.trim())) return "Bot kimliği geçersiz (harf/rakam/._:- , 1-100 karakter).";
    if (draft.name.trim().length === 0) return "Bot adı boş olamaz.";
    const pairs = parseCsv(draft.pairs);
    if (pairs.length === 0 || pairs.length > 32) return "Pair listesi 1-32 sembol olmalıdır.";
    if (new Set(pairs).size !== pairs.length) return "Pair listesi benzersiz semboller içermelidir.";
    if (!pairs.every((s) => SYMBOL.test(s))) return "Sembol biçimi geçersiz (A-Z/0-9, 3-20 karakter).";
    for (const [label, raw] of [["Blacklist", draft.blacklist], ["Favoriler", draft.favorites]] as const) {
      const list = parseCsv(raw);
      if (list.length > 32 || new Set(list).size !== list.length) return `${label}: en fazla 32 benzersiz sembol.`;
      if (!list.every((s) => SYMBOL.test(s))) return `${label}: sembol biçimi geçersiz.`;
    }
    if (draft.startCondition === "indicator") {
      const fast = draft.fastWindow.trim();
      const slow = draft.slowWindow.trim();
      if (!COUNT.test(fast) || Number(fast) < 1) return `${t("wizard.indicator.fast.label")}: ${t("wizard.indicator.invalid")}`;
      if (!COUNT.test(slow) || Number(slow) < 1) return `${t("wizard.indicator.slow.label")}: ${t("wizard.indicator.invalid")}`;
    }
    return "";
  }
  if (step === 1) {
    const checks: [string, string, boolean][] = [
      [t("dca.baseOrder.label"), draft.baseQty.trim(), false],
      [t("dca.safetyOrder.label"), draft.safetyQty.trim(), false],
      [t("dca.deviation.label"), draft.deviation.trim(), false],
      [t("dca.volumeMultiplier.label"), draft.volumeMult.trim(), false],
      [t("dca.stepMultiplier.label"), draft.stepMult.trim(), false],
    ];
    for (const [label, value] of checks) {
      if (!DECIMAL.test(value)) return `${label} exact decimal metni olmalıdır (negatif yok).`;
    }
    if (!COUNT.test(draft.safetyCount.trim())) {
      return `${t("dca.safetyCount.label")} tam sayı olmalıdır (0-50).`;
    }
    const count = Number(draft.safetyCount.trim());
    if (count > 50) return `${t("dca.safetyCount.label")} en fazla 50 olabilir.`;
    return "";
  }
  if (step === 2) {
    if (!DECIMAL.test(draft.takeProfit.trim())) {
      return `${t("exit.takeProfit.label")} exact decimal metni olmalıdır (negatif yok).`;
    }
    const optionals: [string, string][] = [
      [t("exit.stopLoss.label"), draft.stopLoss.trim()],
      [t("exit.trailingStop.label"), draft.trailingStop.trim()],
    ];
    for (const [label, value] of optionals) {
      if (value !== "" && !DECIMAL.test(value)) return `${label} boş ya da exact decimal metni olmalıdır.`;
    }
    return "";
  }
  if (step === 3) {
    if (!DECIMAL.test(draft.budget.trim())) return "Bütçe exact decimal metni olmalıdır (negatif yok).";
    return "";
  }
  return "";
}

export type OptimizePresetId = "deviation_tp" | "safety";

export const OPTIMIZE_PRESETS: Record<string, Record<string, unknown>> = {
  deviation_tp: {
    deviation: { kind: "categorical", choices: ["0.01", "0.02", "0.05"] },
    take_profit: { kind: "categorical", choices: ["0.005", "0.01", "0.02"] },
  },
  safety: {
    safety_count: { kind: "int", low: 1, high: 3 },
    safety_qty: { kind: "categorical", choices: ["0.001", "0.002", "0.005"] },
    volume_multiplier: { kind: "categorical", choices: ["1", "1.5", "2"] },
  },
};

const OPTIMIZE_FIELD_MAP: Record<string, "baseQty" | "safetyQty" | "safetyCount" | "deviation" | "stepMult" | "volumeMult" | "takeProfit"> = {
  base_qty: "baseQty",
  safety_qty: "safetyQty",
  safety_count: "safetyCount",
  deviation: "deviation",
  step_multiplier: "stepMult",
  volume_multiplier: "volumeMult",
  take_profit: "takeProfit",
};

type OptimizeResultView = {
  trial_count: number;
  skipped_count?: number;
  best_metric: string;
  best_recipe_id: string;
  best_overrides: Record<string, string | number>;
};

function isOptimizeResultView(value: unknown): value is OptimizeResultView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  if (typeof body.trial_count !== "number" || typeof body.best_metric !== "string" || typeof body.best_recipe_id !== "string") return false;
  if (body.skipped_count !== undefined && typeof body.skipped_count !== "number") return false;
  if (typeof body.best_overrides !== "object" || body.best_overrides === null || Array.isArray(body.best_overrides)) return false;
  return Object.values(body.best_overrides).every(
    (entry) => typeof entry === "string" || typeof entry === "number",
  );
}

type CrossPreviewEvent = { index: number; direction: string };

function isCrossPreviewEvents(value: unknown): value is CrossPreviewEvent[] {
  if (!Array.isArray(value)) return false;
  return value.every((entry) => {
    if (typeof entry !== "object" || entry === null) return false;
    const row = entry as Record<string, unknown>;
    return typeof row.index === "number" && typeof row.direction === "string";
  });
}

export function BotWizard({
  busy,
  error,
  onRegister,
  onOpenBacktest,
  chartBars,
  botType,
  optimizeDatasetId,
  optimizeProfileId,
}: {
  busy: boolean;
  error: string;
  onRegister: (payload: BotRegisterPayload) => void;
  onOpenBacktest?: () => void;
  chartBars?: HistoricalChartBar[];
  botType?: string;
  optimizeDatasetId?: string;
  optimizeProfileId?: string;
}) {
  const { t } = useI18n();
  const [draft, setDraft] = useState<WizardDraft>(INITIAL_DRAFT);
  const [step, setStep] = useState(0);
  const [stepIssue, setStepIssue] = useState("");
  const [presetOpen, setPresetOpen] = useState(false);
  const [presetMetas, setPresetMetas] = useState<TemplateMeta[] | null>(null);
  const [presetId, setPresetId] = useState("");
  const [presetStatus, setPresetStatus] = useState("");
  const [presetBusy, setPresetBusy] = useState(false);
  const [previewEvents, setPreviewEvents] = useState<CrossPreviewEvent[] | null>(null);
  const [previewIssue, setPreviewIssue] = useState("");
  const [previewSliced, setPreviewSliced] = useState(false);
  const [previewBusy, setPreviewBusy] = useState(false);

  function update(key: keyof WizardDraft, value: string) {
    setDraft((current) => ({ ...current, [key]: value }));
    setStepIssue("");
  }

  function generateName() {
    const prefix = (botType ?? "DCA").toLowerCase();
    const taken = new Set<string>();
    try {
      for (let index = 0; index < window.localStorage.length; index++) {
        const key = window.localStorage.key(index);
        if (!key || !key.startsWith(STRATEGY_DRAFT_PREFIX)) continue;
        taken.add(key.slice(STRATEGY_DRAFT_PREFIX.length));
        try {
          const parsed = JSON.parse(window.localStorage.getItem(key) ?? "null") as { name?: unknown };
          if (typeof parsed?.name === "string") taken.add(parsed.name);
        } catch {
          /* bozuk taslak ad listesine girmez */
        }
      }
    } catch {
      /* private mode: tarama atlanır */
    }
    for (let n = 1; n < 10000; n++) {
      const candidate = `${prefix}-bot-${n}`;
      if (!taken.has(candidate)) {
        update("name", candidate);
        return;
      }
    }
  }

  async function previewSignal() {
    const bars = chartBars ?? [];
    if (bars.length === 0) {
      setPreviewEvents(null);
      setPreviewIssue(t("wizard.indicator.preview.empty"));
      return;
    }
    const fast = Number(draft.fastWindow.trim());
    const slow = Number(draft.slowWindow.trim());
    if (!COUNT.test(draft.fastWindow.trim()) || fast < 1 || !COUNT.test(draft.slowWindow.trim()) || slow < 1) {
      setPreviewEvents(null);
      setPreviewIssue(t("wizard.indicator.invalid"));
      return;
    }
    setPreviewBusy(true);
    setPreviewIssue("");
    try {
      const closes = bars.map((bar) => bar.close);
      const sliced = closes.length > 1000;
      const response = await fetch("/api/signals/indicators/cross", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ closes: closes.slice(-1000), fast_window: fast, slow_window: slow, kind: draft.indicatorKind }),
      });
      const parsed = (await response.json()) as { data?: { events?: unknown } };
      if (!response.ok || !isCrossPreviewEvents(parsed.data?.events)) {
        setPreviewEvents(null);
        setPreviewIssue(t("wizard.indicator.preview.error"));
        return;
      }
      setPreviewEvents(parsed.data.events);
      setPreviewSliced(sliced);
      setPreviewIssue(parsed.data.events.length === 0 ? t("wizard.indicator.preview.none") : "");
    } catch {
      setPreviewEvents(null);
      setPreviewIssue(t("wizard.indicator.preview.error"));
    } finally {
      setPreviewBusy(false);
    }
  }

  function crossDirectionLabel(direction: string): string {
    if (direction === "GOLDEN") return t("wizard.indicator.condition.up");
    if (direction === "DEATH") return t("wizard.indicator.condition.down");
    return direction;
  }

  const optimizeReady = (optimizeDatasetId ?? "") !== "" && (optimizeProfileId ?? "") !== "";
  const [optimizePreset, setOptimizePreset] = useState<OptimizePresetId>("deviation_tp");
  const [optimizeTrials, setOptimizeTrials] = useState("9");
  const [optimizeBusy, setOptimizeBusy] = useState(false);
  const [optimizeIssue, setOptimizeIssue] = useState("");
  const [optimizeResult, setOptimizeResult] = useState<OptimizeResultView | null>(null);

  async function runOptimize() {
    if (!optimizeReady) return;
    const trials = Number(optimizeTrials.trim());
    if (!COUNT.test(optimizeTrials.trim()) || trials < 1 || trials > 32) {
      setOptimizeResult(null);
      setOptimizeIssue(t("wizard.optimize.trials.invalid"));
      return;
    }
    setOptimizeBusy(true);
    setOptimizeIssue("");
    try {
      const response = await fetch("/api/sweeps/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: optimizeDatasetId,
          profile_id: optimizeProfileId,
          space: OPTIMIZE_PRESETS[optimizePreset],
          max_trials: trials,
          sampler: "grid",
          seed: 0,
        }),
      });
      const parsed = (await response.json()) as { data?: unknown };
      if (!response.ok || !isOptimizeResultView(parsed.data)) {
        setOptimizeResult(null);
        setOptimizeIssue(t("wizard.optimize.error"));
        return;
      }
      setOptimizeResult(parsed.data);
      setOptimizeIssue("");
    } catch {
      setOptimizeResult(null);
      setOptimizeIssue(t("wizard.optimize.error"));
    } finally {
      setOptimizeBusy(false);
    }
  }

  function applyOptimize() {
    if (!optimizeResult) return;
    for (const [name, value] of Object.entries(optimizeResult.best_overrides)) {
      const field = OPTIMIZE_FIELD_MAP[name];
      if (field) update(field, String(value));
    }
    setOptimizeIssue(t("wizard.optimize.applied"));
  }

  function go(delta: number) {
    if (delta > 0) {
      const issue = stepError(step, draft, t);
      if (issue) {
        setStepIssue(issue);
        return;
      }
    }
    setStepIssue("");
    setStep((current) => Math.min(Math.max(current + delta, 0), STEP_KEYS.length - 1));
  }

  async function openPreset() {
    const next = !presetOpen;
    setPresetOpen(next);
    if (!next || presetMetas !== null) return;
    setPresetBusy(true);
    setPresetStatus("");
    try {
      const response = await fetch("/api/templates");
      const body = (await response.json()) as { data?: unknown };
      if (!response.ok || !isTemplateMetaList(body.data)) {
        setPresetStatus(t("wizard.preset.error"));
        return;
      }
      setPresetMetas(body.data);
      setPresetId(body.data[0]?.template_id ?? "");
    } catch {
      setPresetStatus(t("wizard.preset.error"));
    } finally {
      setPresetBusy(false);
    }
  }

  async function applyPreset() {
    if (presetId === "") return;
    setPresetBusy(true);
    setPresetStatus("");
    try {
      const response = await fetch(`/api/templates/${encodeURIComponent(presetId)}`);
      const body = (await response.json()) as { data?: unknown };
      if (!response.ok || !isTemplateDetail(body.data)) {
        setPresetStatus(t("wizard.preset.error"));
        return;
      }
      const payload = body.data.payload;
      const updates: Partial<WizardDraft> = {};
      for (const { key, draft: field } of PRESET_FIELD_MAP) {
        const raw: unknown = payload[key];
        if (typeof raw === "string" && raw !== "") updates[field] = raw;
        else if (field === "safetyCount" && typeof raw === "number" && Number.isInteger(raw)) updates[field] = String(raw);
      }
      setDraft((current) => ({ ...current, ...updates }));
      setPresetStatus(`${t("wizard.preset.applied")}: ${Object.keys(updates).length}`);
    } catch {
      setPresetStatus(t("wizard.preset.error"));
    } finally {
      setPresetBusy(false);
    }
  }

  function submit() {
    for (let s = 0; s < STEP_KEYS.length - 1; s += 1) {
      const issue = stepError(s, draft, t);
      if (issue) {
        setStep(s);
        setStepIssue(issue);
        return;
      }
    }
    const botId = draft.botId.trim();
    try {
      window.localStorage.setItem(
        `${STRATEGY_DRAFT_PREFIX}${botId}`,
        JSON.stringify({
          ...(botType === undefined ? {} : { botType }),
          startCondition: draft.startCondition,
          indicatorKind: draft.indicatorKind,
          fastWindow: draft.fastWindow.trim(),
          slowWindow: draft.slowWindow.trim(),
          crossCondition: draft.crossCondition,
          baseQty: draft.baseQty.trim(),
          safetyQty: draft.safetyQty.trim(),
          safetyCount: draft.safetyCount.trim(),
          deviation: draft.deviation.trim(),
          volumeMult: draft.volumeMult.trim(),
          stepMult: draft.stepMult.trim(),
          takeProfit: draft.takeProfit.trim(),
          stopLoss: draft.stopLoss.trim(),
          trailingStop: draft.trailingStop.trim(),
        }),
      );
    } catch {
      /* private mode: kayıt yine de sunucuya gider */
    }
    onRegister({
      bot_id: botId,
      name: draft.name.trim(),
      pairs: parseCsv(draft.pairs),
      blacklist: parseCsv(draft.blacklist),
      favorites: parseCsv(draft.favorites),
      virtual_quote_budget: draft.budget.trim(),
    });
  }

  const pairCount = parseCsv(draft.pairs).length;

  return (
    <section className="panel rebalance-panel" aria-labelledby="bot-wizard-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">YENİ BOT</p>
          <h2 id="bot-wizard-title">Bot oluştur</h2>
        </div>
        <span className="state-label" aria-live="polite">Adım {step + 1}/{STEP_KEYS.length} · {t(STEP_KEYS[step])}</span>
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {stepIssue && <div className="form-error" role="alert">{stepIssue}</div>}
      <div className="wizard-layout">
        <div className="wizard-steps">
          {step === 0 && <FieldGroup label={`1 · ${t(STEP_KEYS[0])}`}>
            <TextParameter label="Bot kimliği" name="wizard_bot_id" value={draft.botId} onChange={(v) => update("botId", v)} />
            <TextParameter label="Bot adı" name="wizard_bot_name" value={draft.name} onChange={(v) => update("name", v)} />
            <button type="button" className="secondary-button" onClick={generateName}>
              {t("wizard.name.auto")}
            </button>
            <PairListInput value={draft.pairs} onChange={(v) => update("pairs", v)} />
            <button type="button" className="preset-link" onClick={() => void openPreset()}>
              {t("wizard.preset.link")}
            </button>
            {presetOpen && (
              <div className="preset-panel">
                {presetStatus !== "" && <p className="helper-text" role="status">{presetStatus}</p>}
                {presetMetas === null ? (
                  <p className="helper-text">{presetBusy ? "…" : t("wizard.preset.error")}</p>
                ) : presetMetas.length === 0 ? (
                  <p className="helper-text">{t("wizard.preset.empty")}</p>
                ) : (
                  <div className="preset-row">
                    <span className="input-wrap">
                      <select aria-label={t("wizard.preset.link")} value={presetId} onChange={(event) => setPresetId(event.target.value)}>
                        {presetMetas.map((meta) => (
                          <option key={meta.template_id} value={meta.template_id}>{meta.template_id}</option>
                        ))}
                      </select>
                    </span>
                    <button type="button" className="secondary-button" disabled={presetBusy || presetId === ""} onClick={() => void applyPreset()}>
                      {t("wizard.preset.apply")}
                    </button>
                  </div>
                )}
              </div>
            )}
            <SegmentedControl
              label={t("bot.startCondition.label")}
              name="wizard_start_condition"
              value={draft.startCondition}
              options={[
                { value: "immediate", label: t("bot.startCondition.immediate") },
                { value: "indicator", label: t("bot.startCondition.indicator") },
                { value: "webhook", label: t("bot.startCondition.webhook") },
              ]}
              onChange={(next) => update("startCondition", next)}
            />
            <ConditionalField when={draft.startCondition === "indicator"}>
              <SegmentedControl
                label={t("wizard.indicator.kind.label")}
                name="wizard_indicator_kind"
                value={draft.indicatorKind}
                options={[
                  { value: "sma", label: "SMA" },
                  { value: "ema", label: "EMA" },
                ]}
                onChange={(next) => update("indicatorKind", next)}
              />
              <NumericParameter label={t("wizard.indicator.fast.label")} name="wizard_fast_window" value={draft.fastWindow} integer min="1" onChange={(v) => update("fastWindow", v)} />
              <NumericParameter label={t("wizard.indicator.slow.label")} name="wizard_slow_window" value={draft.slowWindow} integer min="1" onChange={(v) => update("slowWindow", v)} />
              <SegmentedControl
                label={t("wizard.indicator.condition.label")}
                name="wizard_cross_condition"
                value={draft.crossCondition}
                options={[
                  { value: "up", label: t("wizard.indicator.condition.up") },
                  { value: "down", label: t("wizard.indicator.condition.down") },
                ]}
                onChange={(next) => update("crossCondition", next)}
              />
              <button type="button" className="secondary-button" disabled={previewBusy} onClick={() => void previewSignal()}>
                {t("wizard.indicator.preview.label")}
              </button>
              {previewSliced && previewEvents !== null && (
                <p className="helper-text">{t("wizard.indicator.preview.sliced")}</p>
              )}
              {previewIssue !== "" && <p className="helper-text" role="status">{previewIssue}</p>}
              {previewEvents !== null && previewEvents.length > 0 && (
                <ul className="cross-preview-list">
                  {previewEvents.map((event) => (
                    <li key={event.index}>{`Bar ${event.index} · ${crossDirectionLabel(event.direction)}`}</li>
                  ))}
                </ul>
              )}
            </ConditionalField>
            <ConditionalField when={draft.startCondition === "webhook"}>
              <p className="helper-text">
                {t("bot.startCondition.webhookUrl.label")}: <code>{SIGNAL_WEBHOOK_PATH}</code>
              </p>
              <p className="helper-text">{t("bot.startCondition.webhookUrl.note")}</p>
            </ConditionalField>
            <AdvancedDetails title="Gelişmiş: liste yönetimi">
              <TextParameter label="Blacklist" name="wizard_blacklist" value={draft.blacklist} onChange={(v) => update("blacklist", v)} />
              <TextParameter label="Favoriler" name="wizard_favorites" value={draft.favorites} onChange={(v) => update("favorites", v)} />
            </AdvancedDetails>
          </FieldGroup>}
          {step === 1 && <FieldGroup label={`2 · ${t(STEP_KEYS[1])}`}>
            <NumericParameter label={t("dca.baseOrder.label")} name="wizard_base_qty" value={draft.baseQty} onChange={(v) => update("baseQty", v)} />
            <NumericParameter label={t("dca.safetyOrder.label")} name="wizard_safety_qty" value={draft.safetyQty} onChange={(v) => update("safetyQty", v)} />
            <StepperInput label={t("dca.safetyCount.label")} name="wizard_safety_count" value={draft.safetyCount} min="0" max="50" step="1" onChange={(v) => update("safetyCount", v)} />
            <NumericParameter label={t("dca.deviation.label")} name="wizard_deviation" value={draft.deviation} suffix="oran" onChange={(v) => update("deviation", v)} />
            <LabeledSlider label={t("dca.volumeMultiplier.label")} name="wizard_volume_mult" value={draft.volumeMult} stops={MULTIPLIER_STOPS} minLabel={t("multiplier.off.label")} maxLabel="×2" onChange={(v) => update("volumeMult", v)} />
            <LabeledSlider label={t("dca.stepMultiplier.label")} name="wizard_step_mult" value={draft.stepMult} stops={MULTIPLIER_STOPS} minLabel={t("multiplier.off.label")} maxLabel="×2" onChange={(v) => update("stepMult", v)} />
            {optimizeReady ? (
              <>
                <SegmentedControl
                  label={t("wizard.optimize.preset.label")}
                  name="wizard_optimize_preset"
                  value={optimizePreset}
                  options={[
                    { value: "deviation_tp", label: t("wizard.optimize.preset.deviationTp") },
                    { value: "safety", label: t("wizard.optimize.preset.safety") },
                  ]}
                  onChange={(next) => setOptimizePreset(next as OptimizePresetId)}
                />
                <NumericParameter label={t("wizard.optimize.trials.label")} name="wizard_optimize_trials" value={optimizeTrials} integer min="1" onChange={setOptimizeTrials} />
                <button type="button" className="secondary-button" disabled={optimizeBusy} onClick={() => void runOptimize()}>
                  {t("wizard.optimize.label")}
                </button>
                {optimizeIssue !== "" && <p className="helper-text" role="status">{optimizeIssue}</p>}
                {optimizeResult && (
                  <div className="optimize-result">
                    <p className="helper-text">
                      {`${t("wizard.optimize.best.label")}: ${optimizeResult.best_metric} (${optimizeResult.trial_count} ${t("wizard.optimize.trials.unit")}${(optimizeResult.skipped_count ?? 0) > 0 ? ` · ${optimizeResult.skipped_count} ${t("wizard.optimize.skipped.unit")}` : ""})`}
                    </p>
                    <ul className="cross-preview-list">
                      {Object.entries(optimizeResult.best_overrides).map(([name, value]) => (
                        <li key={name}>{`${name}: ${String(value)}`}</li>
                      ))}
                    </ul>
                    <button type="button" className="secondary-button" onClick={applyOptimize}>
                      {t("wizard.optimize.apply")}
                    </button>
                  </div>
                )}
              </>
            ) : (
              <p className="helper-text">{t("wizard.optimize.unavailable")}</p>
            )}
          </FieldGroup>}
          {step === 2 && <FieldGroup label={`3 · ${t(STEP_KEYS[2])}`}>
            <NumericParameter label={t("exit.takeProfit.label")} name="wizard_take_profit" value={draft.takeProfit} suffix="oran" onChange={(v) => update("takeProfit", v)} />
            <QuickPercentChips label={t("chips.percent.label")} options={TAKE_PROFIT_CHIPS} onSelect={(ratio) => update("takeProfit", ratio)} />
            <ToggleSwitchRow label={t("exit.stopLoss.label")} checked={draft.stopLoss.trim() !== ""} onChange={(checked) => update("stopLoss", checked ? (draft.stopLoss.trim() === "" ? "0.01" : draft.stopLoss) : "")} />
            <ConditionalField when={draft.stopLoss.trim() !== ""}>
              <NumericParameter label={t("exit.stopLoss.label")} name="wizard_stop_loss" value={draft.stopLoss} suffix="oran" onChange={(v) => update("stopLoss", v)} />
            </ConditionalField>
            <ToggleSwitchRow label={t("exit.trailingStop.label")} checked={draft.trailingStop.trim() !== ""} onChange={(checked) => update("trailingStop", checked ? (draft.trailingStop.trim() === "" ? "0.01" : draft.trailingStop) : "")} />
            <ConditionalField when={draft.trailingStop.trim() !== ""}>
              <NumericParameter label={t("exit.trailingStop.label")} name="wizard_trailing_stop" value={draft.trailingStop} suffix="oran" onChange={(v) => update("trailingStop", v)} />
            </ConditionalField>
            <p className="helper-text">Kapalı anahtar taslakta "ayarlanmadı" sayılır; açılınca görünür bir varsayılan oran yazılır.</p>
          </FieldGroup>}
          {step === 3 && <FieldGroup label={`4 · ${t(STEP_KEYS[3])}`}>
            <RiskCritical label={t("setup.investment.label")}>
              <BudgetSlider label={t("setup.investment.label")} name="wizard_budget" value={draft.budget} max="10000" step="10" onChange={(v) => update("budget", v)} />
            </RiskCritical>
          </FieldGroup>}
          {step === 4 && <FieldGroup label={`5 · ${t(STEP_KEYS[4])} ve onay`}>
            {botType !== undefined && <CalculatedPreview label={t("fleet.type.label")} value={botType} />}
            <CalculatedPreview label="Bot" value={draft.botId.trim() || "—"} note={draft.name.trim() || "adsız"} />
            <CalculatedPreview label="Pair sayısı" value={String(pairCount)} />
            <CalculatedPreview label={t("dca.baseOrder.label")} value={draft.baseQty.trim()} />
            <CalculatedPreview label={t("dca.safetyOrder.label")} value={`${draft.safetyQty.trim()} × ${draft.safetyCount.trim()}`} />
            <CalculatedPreview label={t("exit.takeProfit.label")} value={draft.takeProfit.trim()} />
            <CalculatedPreview label={t("setup.investment.label")} value={draft.budget.trim() || "—"} unit="USDT" />
            <p className="helper-text">Kayıt yalnız yerel bot kaydını oluşturur; emir vermez, session bağlamaz. Giriş/çıkış değerleri istemci taslağıdır.</p>
            {chartBars && chartBars.length > 0 && (
              <CandleChart bars={chartBars} status="ready" error="" />
            )}
            {onOpenBacktest && (
              <button className="secondary-button" type="button" onClick={onOpenBacktest}>{t("backtest.button.label")}</button>
            )}
          </FieldGroup>}
          <div className="wizard-nav">
            <button className="secondary-button" type="button" disabled={step === 0 || busy} onClick={() => go(-1)}>Geri</button>
            {step < STEP_KEYS.length - 1
              ? <button className="secondary-button" type="button" disabled={busy} onClick={() => go(1)}>İleri</button>
              : <button className="primary-button" type="button" disabled={busy} onClick={submit}>Botu kaydet</button>}
          </div>
        </div>
        <aside className="wizard-preview" aria-label="Canlı önizleme">
          <h3 className="paper-subheading">Canlı önizleme</h3>
          <CalculatedPreview label="Kimlik" value={draft.botId.trim() || "—"} note="girilen değer" />
          <CalculatedPreview label="Pair" value={String(pairCount)} note="virgülle ayrılmış" />
          <CalculatedPreview label={t("dca.baseOrder.label")} value={draft.baseQty.trim()} />
          <CalculatedPreview label={t("exit.takeProfit.label")} value={draft.takeProfit.trim()} />
          <CalculatedPreview label={t("setup.investment.label")} value={draft.budget.trim() || "—"} unit="USDT" />
        </aside>
      </div>
    </section>
  );
}
