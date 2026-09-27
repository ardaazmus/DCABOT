import { useState } from "react";
import { Badge } from "./Badge";
import { SWEEPABLE_FIELDS, type SweepSpaceSpec } from "./SweepOptimizePanel";

/* Faz 17 AA.7c: WF/MC overfitting sekmesi (qwen sec-backtest WF/MC
 * dizilimi — `POST /api/sweeps/overfitting`). Form SweepOptimizePanel
 * deseninin aynısı + `block_count`; PBO/DSR TAMAMEN sunucuda (Bailey
 * et al., float64-sınırı), UI yalnız dizer. Boş-aralık/uzay kuralları
 * OPT ile birebir (ölü-alan yasağı). */

export type OverfittingPayload = {
  space: Record<string, SweepSpaceSpec>;
  sampler: "grid" | "random";
  max_trials: number;
  seed: number;
  block_count: number;
};

export type OverfittingSkipped = {
  recipe_id: string;
  code: string;
};

export type OverfittingResult = {
  sampler: string;
  seed: number;
  suggested_count: number;
  trial_count: number;
  succeeded_count: number;
  skipped_count: number;
  skipped: OverfittingSkipped[];
  return_series_length: number | null;
  block_count: number;
  pbo: string | null;
  dsr_by_trial: Record<string, string | null>;
  dataset_id: string;
  profile_id: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isSkipped(value: unknown): value is OverfittingSkipped {
  return isRecord(value) && typeof value.recipe_id === "string" && typeof value.code === "string";
}

function isDsrMap(value: unknown): value is Record<string, string | null> {
  if (!isRecord(value)) return false;
  return Object.values(value).every((entry) => typeof entry === "string" || entry === null);
}

export function isOverfittingResponse(value: unknown): value is { data: OverfittingResult } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.sampler === "string"
    && typeof data.seed === "number" && Number.isInteger(data.seed)
    && typeof data.suggested_count === "number"
    && typeof data.trial_count === "number"
    && typeof data.succeeded_count === "number"
    && typeof data.skipped_count === "number"
    && Array.isArray(data.skipped) && data.skipped.every(isSkipped)
    && (typeof data.return_series_length === "number" || data.return_series_length === null)
    && typeof data.block_count === "number"
    && (typeof data.pbo === "string" || data.pbo === null)
    && isDsrMap(data.dsr_by_trial)
    && typeof data.dataset_id === "string"
    && typeof data.profile_id === "string";
}

const DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;
const COUNT = /^(?:0|[1-9]\d*)$/;
const SIGNED_INT = /^-?(?:0|[1-9]\d*)$/;

type OverfittingPanelProps = {
  datasetId: string | null;
  profileId: string | null;
  busy: boolean;
  error: string;
  result: OverfittingResult | null;
  onRun: (payload: OverfittingPayload) => void;
};

export function OverfittingPanel({
  datasetId,
  profileId,
  busy,
  error,
  result,
  onRun,
}: OverfittingPanelProps) {
  const [bounds, setBounds] = useState<Record<string, { min: string; max: string }>>(() =>
    Object.fromEntries(SWEEPABLE_FIELDS.map((field) => [field.key, { min: "", max: "" }])),
  );
  const [sampler, setSampler] = useState<"grid" | "random">("grid");
  const [maxTrials, setMaxTrials] = useState("4");
  const [seed, setSeed] = useState("0");
  const [blockCount, setBlockCount] = useState("4");
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
    const blocks = Number(blockCount.trim());
    if (!COUNT.test(blockCount.trim()) || blocks < 2 || blocks % 2 !== 0) {
      setFormError("Blok sayısı çift ve ≥2 tam sayı olmalıdır.");
      return;
    }
    setFormError("");
    onRun({ space, sampler, max_trials: Number(maxTrials.trim()), seed: Number(seed.trim()), block_count: blocks });
  }

  const dsrEntries = result === null ? [] : Object.entries(result.dsr_by_trial);

  return <section className="panel overfitting-panel" aria-labelledby="overfitting-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">BACKTEST · OVERFITTING (WF/MC)</p>
        <h2 id="overfitting-title">WF/MC sekmesi</h2>
      </div>
      <span className="revision">{result === null ? "koşulmadı" : `${result.succeeded_count} deneme`}</span>
    </div>
    {(datasetId === null || profileId === null) && (
      <div className="empty-state" role="status">Dataset + profil seçilmeden değerlendirme koşulamaz — katalogdan seçin.</div>
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
    <label className="field">
      <span className="field-label">Blok sayısı (çift, ≥2)</span>
      <span className="input-wrap">
        <input aria-label="Blok sayısı (çift, ≥2)" value={blockCount} onChange={(event) => setBlockCount(event.target.value)} />
      </span>
    </label>
    {formError && <div className="form-error" role="alert">{formError}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary-button" type="button" disabled={!ready} onClick={submit}>
      {busy ? "Değerlendiriliyor…" : "Overfitting değerlendirmesi başlat"}
    </button>
    {result !== null && (
      <>
        <p className="eyebrow">SONUÇLAR (SUNUCU-HESABI)</p>
        <dl className="preflight-facts">
          <div><dt>PBO</dt><dd>{result.pbo ?? "—"} <Badge tone="warn" label="FLOAT-SINIRI" title="PBO/DSR float64-sınırında hesaplanır; exact değildir" /></dd></div>
          <div><dt>Önerilen / koşulan / başarılı / atlanan</dt><dd>{result.suggested_count} / {result.trial_count} / {result.succeeded_count} / {result.skipped_count}</dd></div>
          <div><dt>Getiri-serisi uzunluğu</dt><dd>{result.return_series_length ?? "—"}</dd></div>
          <div><dt>Blok sayısı</dt><dd>{result.block_count}</dd></div>
        </dl>
        <div className="table-wrap">
          <table>
            <caption className="sr-only">Deneme-bazında DSR</caption>
            <thead>
              <tr>
                <th scope="col">Deneme</th>
                <th scope="col">DSR</th>
              </tr>
            </thead>
            <tbody>
              {dsrEntries.map(([trialId, dsr]) => (
                <tr key={trialId}>
                  <td title={trialId}>{trialId}</td>
                  <td>{dsr ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {result.skipped.length > 0 && (
          <dl className="preflight-facts">
            <div><dt>Atlanan tarifler</dt><dd>{result.skipped.map((row) => `${row.recipe_id} (${row.code})`).join(", ")}</dd></div>
          </dl>
        )}
      </>
    )}
    <p className="paper-note">PBO/DSR Bailey et al. istatistikleridir (sunucu, float64-sınırı); null = tanımsız payda, uydurma-0 yok. Tam-CPCV (purge/embargo walk-forward) bu sekmede YOK — ayrı dilim.</p>
  </section>;
}
