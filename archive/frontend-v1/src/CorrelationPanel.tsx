import { useState } from "react";
import type { DatasetSummary } from "./datasetCatalog";

/* Faz 17 AA.10b: korelasyon kapısı sekmesi (qwen sec-risk corrGrid'in GERÇEK
 * karşılığı — `POST /api/risk/correlation`). İki datasetin kapanış-serileri
 * sunucudan gelir, UI SON-N barı seçip sayıya ÇEVİRİR (uç float-listesi
 * ister; çevirim girdi-kodlamadır, SweepOptimizePanel emsali). Getiri/
 * varyans/karar TAMAMEN sunucuda; UI yalnız kararı dizer. Seriler sondan
 * hizalanır — zaman-çakışması doğrulanmaz, not olarak yazılır. */

export type CorrelationGatePayload = {
  prices_x: number[];
  prices_y: number[];
  windows: number[];
  threshold_numerator: number;
  threshold_denominator: number;
  scale: number;
};

export type CorrelationGateResult = {
  decision: string;
  reason: string;
  worst_window: number | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isCorrelationGateResponse(value: unknown): value is { data: CorrelationGateResult } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.decision === "string"
    && typeof data.reason === "string"
    && (typeof data.worst_window === "number" || data.worst_window === null);
}

const COUNT = /^(?:0|[1-9]\d*)$/;

function parseWindows(text: string): number[] | null {
  const parts = text.split(",").map((part) => part.trim()).filter((part) => part !== "");
  if (parts.length === 0 || parts.length > 16) return null;
  const windows: number[] = [];
  for (const part of parts) {
    if (!COUNT.test(part)) return null;
    const value = Number(part);
    if (value < 2) return null;
    windows.push(value);
  }
  return windows;
}

function toPrices(closes: string[], count: number): number[] | null {
  const slice = closes.slice(-count);
  const prices: number[] = [];
  for (const close of slice) {
    const value = Number(close);
    if (!Number.isFinite(value)) return null;
    prices.push(value);
  }
  return prices;
}

type CorrelationPanelProps = {
  datasets: DatasetSummary[];
  closesX: string[];
  closesY: string[];
  labelX: string;
  labelY: string;
  seriesBusy: boolean;
  seriesError: string;
  busy: boolean;
  error: string;
  result: CorrelationGateResult | null;
  onSelectSeries: (slot: "x" | "y", datasetId: string) => void;
  onRun: (payload: CorrelationGatePayload) => void;
};

export function CorrelationPanel({
  datasets,
  closesX,
  closesY,
  labelX,
  labelY,
  seriesBusy,
  seriesError,
  busy,
  error,
  result,
  onSelectSeries,
  onRun,
}: CorrelationPanelProps) {
  const [datasetX, setDatasetX] = useState("");
  const [datasetY, setDatasetY] = useState("");
  const [barCount, setBarCount] = useState("120");
  const [windowsText, setWindowsText] = useState("20,60");
  const [numerator, setNumerator] = useState("8");
  const [denominator, setDenominator] = useState("10");
  const [scale, setScale] = useState("1000000");
  const [formError, setFormError] = useState("");
  const ready = closesX.length > 0 && closesY.length > 0 && !seriesBusy && !busy;

  function submit() {
    if (!COUNT.test(barCount.trim())) {
      setFormError("Bar sayısı 2-5000 arası tam sayı olmalıdır.");
      return;
    }
    const count = Number(barCount.trim());
    if (count < 2 || count > 5000) {
      setFormError("Bar sayısı 2-5000 arası tam sayı olmalıdır.");
      return;
    }
    if (closesX.length < count || closesY.length < count) {
      setFormError(`Seçili serilerde ${count} bar yok (X: ${closesX.length}, Y: ${closesY.length}).`);
      return;
    }
    const windows = parseWindows(windowsText);
    if (windows === null) {
      setFormError("Pencereler virgüllü, her biri ≥2 tamsayı olmalıdır (en fazla 16).");
      return;
    }
    for (const [label, raw] of [["Pay", numerator], ["Payda", denominator], ["Scale", scale]] as const) {
      if (!COUNT.test(raw.trim()) || Number(raw.trim()) <= 0) {
        setFormError(`${label} pozitif tamsayı olmalıdır.`);
        return;
      }
    }
    const pricesX = toPrices(closesX, count);
    const pricesY = toPrices(closesY, count);
    if (pricesX === null || pricesY === null) {
      setFormError("Seri sayıya çevrilemedi (sunucu-verisi bozuk olabilir).");
      return;
    }
    setFormError("");
    onRun({
      prices_x: pricesX,
      prices_y: pricesY,
      windows,
      threshold_numerator: Number(numerator.trim()),
      threshold_denominator: Number(denominator.trim()),
      scale: Number(scale.trim()),
    });
  }

  function renderSeriesSelect(slot: "x" | "y", value: string, setValue: (next: string) => void, label: string, loaded: string, count: number) {
    return (
      <label className="field">
        <span className="field-label">{label}</span>
        <span className="input-wrap">
          <select
            aria-label={label}
            value={value}
            onChange={(event) => { setValue(event.target.value); if (event.target.value !== "") onSelectSeries(slot, event.target.value); }}
          >
            <option value="">Seçin…</option>
            {datasets.map((dataset) => <option key={dataset.dataset_id} value={dataset.dataset_id}>{dataset.dataset_id} · {dataset.instrument} {dataset.interval}</option>)}
          </select>
        </span>
        <span className="helper-text">{loaded === "" ? "seri yüklenmedi" : `${loaded}: ${count} bar`}</span>
      </label>
    );
  }

  return <section className="panel correlation-panel" aria-labelledby="correlation-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">RİSK · KORELASYON KAPISI</p>
        <h2 id="correlation-title">İki-seri kapı-değerlendirmesi</h2>
      </div>
      <span className="revision">{result === null ? "koşulmadı" : result.decision}</span>
    </div>
    {renderSeriesSelect("x", datasetX, setDatasetX, "X serisi dataseti", labelX, closesX.length)}
    {renderSeriesSelect("y", datasetY, setDatasetY, "Y serisi dataseti", labelY, closesY.length)}
    {seriesBusy && <div className="empty-state" role="status">Seri yükleniyor…</div>}
    {seriesError && <div className="form-error" role="alert">{seriesError}</div>}
    <label className="field">
      <span className="field-label">Bar sayısı — sondan (2-5000)</span>
      <span className="input-wrap">
        <input aria-label="Bar sayısı — sondan (2-5000)" value={barCount} onChange={(event) => setBarCount(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">Pencereler (virgüllü, ≥2)</span>
      <span className="input-wrap">
        <input aria-label="Pencereler (virgüllü, ≥2)" value={windowsText} onChange={(event) => setWindowsText(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">Eşik pay / payda (oran)</span>
      <span className="input-wrap">
        <input aria-label="Eşik pay" value={numerator} onChange={(event) => setNumerator(event.target.value)} />
        <input aria-label="Eşik payda" value={denominator} onChange={(event) => setDenominator(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">Scale (sabit-nokta)</span>
      <span className="input-wrap">
        <input aria-label="Scale (sabit-nokta)" value={scale} onChange={(event) => setScale(event.target.value)} />
      </span>
    </label>
    {formError && <div className="form-error" role="alert">{formError}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary-button" type="button" disabled={!ready} onClick={submit}>
      {busy ? "Değerlendiriliyor…" : "Kapıyı değerlendir"}
    </button>
    {result !== null && (
      <dl className="preflight-facts">
        <div><dt>Karar</dt><dd><span className={result.decision === "ALLOW" ? "state-label ready" : "state-label error"}>{result.decision}</span></dd></div>
        <div><dt>Gerekçe</dt><dd>{result.reason}</dd></div>
        <div><dt>En-kötü pencere</dt><dd>{result.worst_window === null ? "—" : result.worst_window}</dd></div>
      </dl>
    )}
    <p className="paper-note">Getiri-logaritması float-sınırında, eşik-karşılaştırma tamsayı-exact (sunucu, B-disiplini). Seriler sondan hizalanır; zaman-çakışması doğrulanmaz — aynı aralıklı iki dataset seçin.</p>
  </section>;
}
