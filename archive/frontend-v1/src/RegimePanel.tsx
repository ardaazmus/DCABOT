import { useState } from "react";
import type { DatasetSummary, HistoricalChartBar } from "./datasetCatalog";

/* Faz 17 AA.8: regime-detection kartı (qwen sec-modules'in GERÇEK karşılığı
 * — `POST /api/risk/regime`). Dataset barları sunucudan gelir (chart-data),
 * UI SON-N barı {high,low,close} seçip aynen POST'lar (verbatim, çevirim
 * yok — uç exact-string ister). state/direction/confidence TAMAMEN
 * sunucuda; UI yalnız dizer. confidence OLASILIK DEĞİLDİR (sunucu
 * kural-etiketi) — not olarak yazılır. */

export type RegimeBarInput = {
  high: string;
  low: string;
  close: string;
};

export type RegimeGatePayload = {
  bars: RegimeBarInput[];
  adx_window: number;
  bb_window: number;
  bb_num_std: string;
  trend_threshold: string;
  range_threshold: string;
  squeeze_threshold: string;
};

export type RegimeGateResult = {
  state: string;
  direction: string | null;
  confidence: string;
  adx: string | null;
  plus_di: string | null;
  minus_di: string | null;
  bb_width: string | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringOrNull(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

export function isRegimeGateResponse(value: unknown): value is { data: RegimeGateResult } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.state === "string"
    && isStringOrNull(data.direction)
    && typeof data.confidence === "string"
    && isStringOrNull(data.adx)
    && isStringOrNull(data.plus_di)
    && isStringOrNull(data.minus_di)
    && isStringOrNull(data.bb_width);
}

const COUNT = /^(?:0|[1-9]\d*)$/;
const EXACT_DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

function toBarInputs(bars: HistoricalChartBar[], count: number): RegimeBarInput[] | null {
  const slice = bars.slice(-count);
  if (slice.length < count) return null;
  const inputs: RegimeBarInput[] = [];
  for (const bar of slice) {
    if (typeof bar.high !== "string" || typeof bar.low !== "string" || typeof bar.close !== "string") return null;
    inputs.push({ high: bar.high, low: bar.low, close: bar.close });
  }
  return inputs;
}

type RegimePanelProps = {
  datasets: DatasetSummary[];
  bars: HistoricalChartBar[];
  label: string;
  seriesBusy: boolean;
  seriesError: string;
  busy: boolean;
  error: string;
  result: RegimeGateResult | null;
  onSelectSeries: (datasetId: string) => void;
  onRun: (payload: RegimeGatePayload) => void;
};

export function RegimePanel({
  datasets,
  bars,
  label,
  seriesBusy,
  seriesError,
  busy,
  error,
  result,
  onSelectSeries,
  onRun,
}: RegimePanelProps) {
  const [datasetId, setDatasetId] = useState("");
  const [barCount, setBarCount] = useState("120");
  const [adxWindow, setAdxWindow] = useState("3");
  const [bbWindow, setBbWindow] = useState("5");
  const [bbNumStd, setBbNumStd] = useState("2");
  const [trendThreshold, setTrendThreshold] = useState("20");
  const [rangeThreshold, setRangeThreshold] = useState("15");
  const [squeezeThreshold, setSqueezeThreshold] = useState("0.01");
  const [formError, setFormError] = useState("");
  const ready = bars.length > 0 && !seriesBusy && !busy;

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
    for (const [name, raw] of [["ADX penceresi", adxWindow], ["BB penceresi", bbWindow]] as const) {
      if (!COUNT.test(raw.trim()) || Number(raw.trim()) < 1) {
        setFormError(`${name} pozitif tamsayı olmalıdır.`);
        return;
      }
    }
    for (const [name, raw] of [["BB std", bbNumStd], ["Trend eşiği", trendThreshold], ["Range eşiği", rangeThreshold], ["Squeeze eşiği", squeezeThreshold]] as const) {
      if (!EXACT_DECIMAL.test(raw.trim())) {
        setFormError(`${name} exact-ondalık olmalıdır.`);
        return;
      }
    }
    const inputs = toBarInputs(bars, count);
    if (inputs === null) {
      setFormError(`Seçili seride ${count} bar yok veya bar bozuk (${label === "" ? "seri yüklenmedi" : `${label}: ${bars.length} bar`}).`);
      return;
    }
    setFormError("");
    onRun({
      bars: inputs,
      adx_window: Number(adxWindow.trim()),
      bb_window: Number(bbWindow.trim()),
      bb_num_std: bbNumStd.trim(),
      trend_threshold: trendThreshold.trim(),
      range_threshold: rangeThreshold.trim(),
      squeeze_threshold: squeezeThreshold.trim(),
    });
  }

  return <section className="panel regime-panel" aria-labelledby="regime-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">RİSK · REJİM</p>
        <h2 id="regime-title">Regime-detection kartı</h2>
      </div>
      <span className="revision">{result === null ? "koşulmadı" : result.state}</span>
    </div>
    <label className="field">
      <span className="field-label">Bar serisi dataseti</span>
      <span className="input-wrap">
        <select
          aria-label="Bar serisi dataseti"
          value={datasetId}
          onChange={(event) => { setDatasetId(event.target.value); if (event.target.value !== "") onSelectSeries(event.target.value); }}
        >
          <option value="">Seçin…</option>
          {datasets.map((dataset) => <option key={dataset.dataset_id} value={dataset.dataset_id}>{dataset.dataset_id} · {dataset.instrument} {dataset.interval}</option>)}
        </select>
      </span>
      <span className="helper-text">{label === "" ? "seri yüklenmedi" : `${label}: ${bars.length} bar`}</span>
    </label>
    {seriesBusy && <div className="empty-state" role="status">Seri yükleniyor…</div>}
    {seriesError && <div className="form-error" role="alert">{seriesError}</div>}
    <label className="field">
      <span className="field-label">Bar sayısı — sondan (2-5000)</span>
      <span className="input-wrap">
        <input aria-label="Bar sayısı — sondan (2-5000)" value={barCount} onChange={(event) => setBarCount(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">ADX / BB penceresi (≥1)</span>
      <span className="input-wrap">
        <input aria-label="ADX penceresi" value={adxWindow} onChange={(event) => setAdxWindow(event.target.value)} />
        <input aria-label="BB penceresi" value={bbWindow} onChange={(event) => setBbWindow(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">BB std / Trend / Range / Squeeze eşikleri</span>
      <span className="input-wrap">
        <input aria-label="BB std" value={bbNumStd} onChange={(event) => setBbNumStd(event.target.value)} />
        <input aria-label="Trend eşiği" value={trendThreshold} onChange={(event) => setTrendThreshold(event.target.value)} />
        <input aria-label="Range eşiği" value={rangeThreshold} onChange={(event) => setRangeThreshold(event.target.value)} />
        <input aria-label="Squeeze eşiği" value={squeezeThreshold} onChange={(event) => setSqueezeThreshold(event.target.value)} />
      </span>
    </label>
    {formError && <div className="form-error" role="alert">{formError}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary-button" type="button" disabled={!ready} onClick={submit}>
      {busy ? "Değerlendiriliyor…" : "Rejimi değerlendir"}
    </button>
    {result !== null && (
      <dl className="preflight-facts">
        <div><dt>Durum</dt><dd><span className="state-label ready">{result.state}</span></dd></div>
        <div><dt>Yön</dt><dd>{result.direction === null ? "—" : result.direction}</dd></div>
        <div><dt>Güven</dt><dd>{result.confidence}</dd></div>
        <div><dt>ADX</dt><dd>{result.adx === null ? "—" : result.adx}</dd></div>
        <div><dt>+DI</dt><dd>{result.plus_di === null ? "—" : result.plus_di}</dd></div>
        <div><dt>−DI</dt><dd>{result.minus_di === null ? "—" : result.minus_di}</dd></div>
        <div><dt>BB genişliği</dt><dd>{result.bb_width === null ? "—" : result.bb_width}</dd></div>
      </dl>
    )}
    <p className="paper-note">Varsayılanlar backend-test-kanonik (3/5, 2, 20/15, 0.01). Güven skoru olasılık DEĞİLDİR (sunucu kural-etiketi). Son-N bar sondan alınır.</p>
  </section>;
}
