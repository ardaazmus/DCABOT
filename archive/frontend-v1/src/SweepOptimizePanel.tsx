import { useState } from "react";
import { Badge } from "./Badge";
import { shortSha256 } from "./datasetCatalog";

/* Faz 17 AA.7b: sweep/optimize sekmesi (qwen sec-backtest OPT dizilimi).
 * `sweep_orchestrator._SWEEPABLE` allowlist'inin birebir karşılığı — bu
 * 7 anahtar-dışı alan FORMA KONULMAZ (sunucu reddeder, ölü-alan yasağı).
 * Aday-değer örneklemesi sunucuda float ile yapılır (repr-exact metin);
 * sıralama metriği exact-Fraction net'tir — ikisi ayrı rozetlenir. */

export const SWEEPABLE_FIELDS = [
  { key: "take_profit", label: "TP", kind: "float" },
  { key: "deviation", label: "Sapma", kind: "float" },
  { key: "step_multiplier", label: "Step çarpanı", kind: "float" },
  { key: "volume_multiplier", label: "Volume çarpanı", kind: "float" },
  { key: "base_qty", label: "Base miktar", kind: "float" },
  { key: "safety_qty", label: "Safety miktar", kind: "float" },
  { key: "safety_count", label: "SO adedi", kind: "int" },
] as const;

export type SweepSpaceSpec =
  | { kind: "float"; low: number; high: number }
  | { kind: "int"; low: number; high: number };

export type SweepOptimizePayload = {
  space: Record<string, SweepSpaceSpec>;
  sampler: "grid" | "random";
  max_trials: number;
  seed: number;
};

export type SweepTrialOverrides = Record<string, string | number>;

export type SweepTrial = {
  recipe_id: string;
  overrides: SweepTrialOverrides;
  execution_status: string;
  realized_net_after_all_costs: string;
  config_hash: string;
  win_rate: string | null;
  profit_factor: string | null;
  roi: string | null;
  safety_order_fill_rate: string | null;
};

export type SweepSkipped = {
  recipe_id: string;
  overrides: SweepTrialOverrides;
  code: string;
};

export type SweepOptimizeResult = {
  sampler: string;
  seed: number;
  suggested_count: number;
  trial_count: number;
  trials: SweepTrial[];
  skipped_count: number;
  skipped: SweepSkipped[];
  best_recipe_id: string;
  best_overrides: SweepTrialOverrides;
  best_metric: string;
  dataset_id: string;
  profile_id: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isOverrides(value: unknown): value is SweepTrialOverrides {
  if (!isRecord(value)) return false;
  return Object.values(value).every(
    (entry) => typeof entry === "string" || (typeof entry === "number" && Number.isInteger(entry)),
  );
}

function isTrial(value: unknown): value is SweepTrial {
  if (!isRecord(value)) return false;
  return typeof value.recipe_id === "string"
    && isOverrides(value.overrides)
    && typeof value.execution_status === "string"
    && typeof value.realized_net_after_all_costs === "string"
    && typeof value.config_hash === "string"
    && (typeof value.win_rate === "string" || value.win_rate === null)
    && (typeof value.profit_factor === "string" || value.profit_factor === null)
    && (typeof value.roi === "string" || value.roi === null)
    && (typeof value.safety_order_fill_rate === "string" || value.safety_order_fill_rate === null);
}

function isSkipped(value: unknown): value is SweepSkipped {
  if (!isRecord(value)) return false;
  return typeof value.recipe_id === "string"
    && isOverrides(value.overrides)
    && typeof value.code === "string";
}

export function isSweepOptimizeResponse(value: unknown): value is { data: SweepOptimizeResult } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.sampler === "string"
    && typeof data.seed === "number"
    && Number.isInteger(data.seed)
    && typeof data.suggested_count === "number"
    && typeof data.trial_count === "number"
    && Array.isArray(data.trials)
    && data.trials.every(isTrial)
    && typeof data.skipped_count === "number"
    && Array.isArray(data.skipped)
    && data.skipped.every(isSkipped)
    && typeof data.best_recipe_id === "string"
    && isOverrides(data.best_overrides)
    && typeof data.best_metric === "string"
    && typeof data.dataset_id === "string"
    && typeof data.profile_id === "string";
}

/* Girdi-doğrulama desenleri (BotWizard emsali — finansal hesap değil). */
const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;
const COUNT = /^(?:0|[1-9]\d*)$/;
const SIGNED_INT = /^-?(?:0|[1-9]\d*)$/;

function formatOverrides(overrides: SweepTrialOverrides): string {
  return Object.entries(overrides).map(([key, value]) => `${key}=${String(value)}`).join(", ");
}

type SweepOptimizePanelProps = {
  datasetId: string | null;
  profileId: string | null;
  busy: boolean;
  error: string;
  result: SweepOptimizeResult | null;
  onRun: (payload: SweepOptimizePayload) => void;
  onFillWizard: (overrides: SweepTrialOverrides) => void;
};

export function SweepOptimizePanel({
  datasetId,
  profileId,
  busy,
  error,
  result,
  onRun,
  onFillWizard,
}: SweepOptimizePanelProps) {
  const [bounds, setBounds] = useState<Record<string, { min: string; max: string }>>(() =>
    Object.fromEntries(SWEEPABLE_FIELDS.map((field) => [field.key, { min: "", max: "" }])),
  );
  const [sampler, setSampler] = useState<"grid" | "random">("grid");
  const [maxTrials, setMaxTrials] = useState("8");
  const [seed, setSeed] = useState("0");
  const [formError, setFormError] = useState("");
  const ready = datasetId !== null && profileId !== null && !busy;

  function setBound(key: string, side: "min" | "max", value: string) {
    setBounds((current) => ({ ...current, [key]: { ...current[key], [side]: value } }));
  }

  function submit() {
    const space: Record<string, SweepSpaceSpec> = {};
    for (const field of SWEEPABLE_FIELDS) {
      const row = bounds[field.key];
      const min = row.min.trim();
      const max = row.max.trim();
      if (min === "" && max === "") continue;
      const pattern = field.kind === "int" ? COUNT : DECIMAL;
      if (!pattern.test(min) || !pattern.test(max)) {
        setFormError(`"${field.label}" aralığı sayı olmalıdır (boş = tarama-dışı).`);
        return;
      }
      const low = Number(min);
      const high = Number(max);
      if (field.kind === "int" ? low > high : low >= high) {
        setFormError(`"${field.label}" aralığı geçersiz (${field.kind === "int" ? "min≤max" : "min<max"} olmalı).`);
        return;
      }
      space[field.key] = field.kind === "int"
        ? { kind: "int", low, high }
        : { kind: "float", low, high };
    }
    if (Object.keys(space).length === 0) {
      setFormError("En az bir parametre aralığı girin (hepsi boş = taranacak uzay yok).");
      return;
    }
    if (!COUNT.test(maxTrials.trim()) || Number(maxTrials.trim()) < 1 || Number(maxTrials.trim()) > 32) {
      setFormError("Deneme sayısı 1-32 arası tam sayı olmalıdır.");
      return;
    }
    if (!SIGNED_INT.test(seed.trim())) {
      setFormError("Seed tam sayı olmalıdır.");
      return;
    }
    setFormError("");
    onRun({ space, sampler, max_trials: Number(maxTrials.trim()), seed: Number(seed.trim()) });
  }

  return <section className="panel sweep-optimize-panel" aria-labelledby="sweep-optimize-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">BACKTEST · PARAMETRE OPTİMİZASYONU</p>
        <h2 id="sweep-optimize-title">OPT sekmesi</h2>
      </div>
      <span className="revision">{result === null ? "koşulmadı" : `${result.trial_count} deneme`}</span>
    </div>
    {(datasetId === null || profileId === null) && (
      <div className="empty-state" role="status">Dataset + profil seçilmeden tarama koşulamaz — katalogdan seçin.</div>
    )}
    {datasetId !== null && profileId !== null && (
      <p className="helper-text">Dataset: {datasetId} · Profil: {profileId}</p>
    )}
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col">Parametre</th>
            <th scope="col">Min</th>
            <th scope="col">Max</th>
          </tr>
        </thead>
        <tbody>
          {SWEEPABLE_FIELDS.map((field) => (
            <tr key={field.key}>
              <td>{field.label} <span className="helper-text">({field.key})</span></td>
              <td>
                <input aria-label={`${field.label} min`} value={bounds[field.key].min} onChange={(event) => setBound(field.key, "min", event.target.value)} />
              </td>
              <td>
                <input aria-label={`${field.label} max`} value={bounds[field.key].max} onChange={(event) => setBound(field.key, "max", event.target.value)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <label className="field">
      <span className="field-label">Tarama tipi</span>
      <span className="input-wrap">
        <select aria-label="Tarama tipi" value={sampler} onChange={(event) => setSampler(event.target.value as "grid" | "random")}>
          <option value="grid">Izgara (deterministik)</option>
          <option value="random">Rastgele (seed'li)</option>
        </select>
      </span>
    </label>
    <label className="field">
      <span className="field-label">Deneme sayısı (1-32)</span>
      <span className="input-wrap">
        <input aria-label="Deneme sayısı (1-32)" value={maxTrials} onChange={(event) => setMaxTrials(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">Seed (rastgele için)</span>
      <span className="input-wrap">
        <input aria-label="Seed (rastgele için)" value={seed} onChange={(event) => setSeed(event.target.value)} />
      </span>
    </label>
    {formError && <div className="form-error" role="alert">{formError}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary-button" type="button" disabled={!ready} onClick={submit}>
      {busy ? "Taranıyor…" : "Optimizasyonu başlat"}
    </button>
    <p className="helper-text">Boş aralık = o parametre taranmaz. Amaç fonksiyonu sabittir: exact net (sunucu sıralar).</p>
    {result !== null && (
      <>
        <p className="eyebrow">SONUÇLAR (SUNUCU-SIRALI)</p>
        <dl className="preflight-facts">
          <div><dt>Önerilen / koşulan / atlanan</dt><dd>{result.suggested_count} / {result.trial_count} / {result.skipped_count}</dd></div>
          <div><dt>En iyi tarif</dt><dd>{result.best_recipe_id} (net {result.best_metric}) <Badge tone="ok" label="EXACT" title="Sıralama metriği exact-Fraction net'tir" /></dd></div>
          <div><dt>En iyi değerler</dt><dd>{formatOverrides(result.best_overrides)}</dd></div>
        </dl>
        <button className="secondary-button" type="button" onClick={() => onFillWizard(result.best_overrides)}>
          En iyiyi sihirbaza doldur
        </button>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Tarif</th>
                <th scope="col">Değerler</th>
                <th scope="col">Durum</th>
                <th scope="col">Net</th>
                <th scope="col">Win rate</th>
                <th scope="col">PF</th>
                <th scope="col">ROI</th>
                <th scope="col">SO-oranı</th>
                <th scope="col">Config</th>
                <th scope="col">Sihirbaz</th>
              </tr>
            </thead>
            <tbody>
              {result.trials.map((trial, index) => (
                <tr key={trial.recipe_id}>
                  <td>{trial.recipe_id === result.best_recipe_id ? `★${index + 1}` : String(index + 1)}</td>
                  <td title={trial.recipe_id}>{trial.recipe_id}</td>
                  <td>{formatOverrides(trial.overrides)}</td>
                  <td>{trial.execution_status}</td>
                  <td>{trial.realized_net_after_all_costs}</td>
                  <td>{trial.win_rate ?? "—"}</td>
                  <td>{trial.profit_factor ?? "—"}</td>
                  <td>{trial.roi ?? "—"}</td>
                  <td>{trial.safety_order_fill_rate ?? "—"}</td>
                  <td title={trial.config_hash}>{shortSha256(trial.config_hash)}</td>
                  <td>
                    <button className="secondary-button" type="button" onClick={() => onFillWizard(trial.overrides)}>
                      Doldur
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {result.skipped.length > 0 && (
          <>
            <p className="eyebrow">ATLANANLAR (SUNUCU-REDDİ)</p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Tarif</th>
                    <th scope="col">Değerler</th>
                    <th scope="col">Kod</th>
                  </tr>
                </thead>
                <tbody>
                  {result.skipped.map((row) => (
                    <tr key={row.recipe_id}>
                      <td title={row.recipe_id}>{row.recipe_id}</td>
                      <td>{formatOverrides(row.overrides)}</td>
                      <td>{row.code}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </>
    )}
    <p className="paper-note">Aday değerler float-örneklemeden gelir (repr-exact metin) <Badge tone="warn" label="FLOAT-SINIRI" title="Örnekleme float'tır; exact değildir" /> · sıralama metriği exact net <Badge tone="ok" label="EXACT" title="Sıralama metriği exact-Fraction net'tir" />. Isı-haritası yok (hücre-skoru istemci-hesabı olurdu); WF/MC sekmeleri uç bekliyor.</p>
  </section>;
}
