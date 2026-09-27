import { IndicatorSeriesChart, type IndicatorLine } from "./IndicatorSeriesChart";

export type IndicatorKind = "sma" | "ema" | "macd" | "stoch_rsi" | "bollinger";

export type IndicatorPoint = {
  index: number;
  value: string;
  exact: boolean;
};

export type MacdPoint = {
  index: number;
  macd: string | null;
  signal: string | null;
  histogram: string | null;
};

export type StochRsiPoint = {
  index: number;
  rsi: string | null;
  stoch_rsi: string | null;
};

export type BollingerPoint = {
  index: number;
  middle: string | null;
  middle_exact: boolean;
  variance: string | null;
  variance_exact: boolean;
  upper: string | null;
  lower: string | null;
  percent_b: string | null;
};

export type IndicatorSeries =
  | { kind: "sma" | "ema"; points: IndicatorPoint[] }
  | { kind: "macd"; points: MacdPoint[] }
  | { kind: "stoch_rsi"; points: StochRsiPoint[] }
  | { kind: "bollinger"; points: BollingerPoint[] };

export type IndicatorStatus = "idle" | "loading" | "ready" | "error";

/** Uç-yolu eşlemesi (`stoch_rsi` → tireli rota) + backend-test-kanonik
 * gövde kurucusu (MACD 3/6/3·s8, StochRSI 5/5·s8, BB 3·"2"). */
export const INDICATOR_ROUTES: Record<IndicatorKind, string> = {
  sma: "sma",
  ema: "ema",
  macd: "macd",
  stoch_rsi: "stoch-rsi",
  bollinger: "bollinger",
};

export function indicatorRequestBody(kind: IndicatorKind, closes: string[]): Record<string, unknown> {
  switch (kind) {
    case "sma":
      return { closes, window: 20 };
    case "ema":
      return { closes, window: 50 };
    case "macd":
      return { closes, fast: 3, slow: 6, signal: 3, scale: 8 };
    case "stoch_rsi":
      return { closes, rsi_window: 5, stoch_window: 5, scale: 8 };
    case "bollinger":
      return { closes, window: 3, num_std: "2" };
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringOrNull(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function isIndicatorPoint(value: unknown): value is IndicatorPoint {
  if (!isRecord(value)) return false;
  return typeof value.index === "number"
    && typeof value.value === "string"
    && typeof value.exact === "boolean";
}

function isMacdPoint(value: unknown): value is MacdPoint {
  if (!isRecord(value)) return false;
  return typeof value.index === "number"
    && isStringOrNull(value.macd)
    && isStringOrNull(value.signal)
    && isStringOrNull(value.histogram);
}

function isStochRsiPoint(value: unknown): value is StochRsiPoint {
  if (!isRecord(value)) return false;
  return typeof value.index === "number"
    && isStringOrNull(value.rsi)
    && isStringOrNull(value.stoch_rsi);
}

function isBollingerPoint(value: unknown): value is BollingerPoint {
  if (!isRecord(value)) return false;
  return typeof value.index === "number"
    && isStringOrNull(value.middle)
    && typeof value.middle_exact === "boolean"
    && isStringOrNull(value.variance)
    && typeof value.variance_exact === "boolean"
    && isStringOrNull(value.upper)
    && isStringOrNull(value.lower)
    && isStringOrNull(value.percent_b);
}

export function isIndicatorSeries(value: unknown): value is { points: IndicatorPoint[] } {
  if (!isRecord(value)) return false;
  return Array.isArray(value.points) && value.points.every(isIndicatorPoint);
}

export function isIndicatorResponse(value: unknown): value is { data: { points: IndicatorPoint[] } } {
  if (!isRecord(value)) return false;
  return isIndicatorSeries(value.data);
}

export function isMacdResponse(value: unknown): value is { data: { points: MacdPoint[] } } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return Array.isArray(data.points) && data.points.every(isMacdPoint);
}

export function isStochRsiResponse(value: unknown): value is { data: { points: StochRsiPoint[] } } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return Array.isArray(data.points) && data.points.every(isStochRsiPoint);
}

export function isBollingerResponse(value: unknown): value is { data: { points: BollingerPoint[] } } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return Array.isArray(data.points) && data.points.every(isBollingerPoint);
}

type IndicatorPanelProps = {
  kind: IndicatorKind;
  series: IndicatorSeries | null;
  status: IndicatorStatus;
  error: string;
  barCount: number;
  onSelect: (kind: IndicatorKind) => void;
  onRetry: () => void;
};

const CHIPS: { kind: IndicatorKind; label: string }[] = [
  { kind: "sma", label: "SMA 20" },
  { kind: "ema", label: "EMA 50" },
  { kind: "macd", label: "MACD 3/6/3" },
  { kind: "stoch_rsi", label: "StochRSI 5/5" },
  { kind: "bollinger", label: "BB 3·2σ" },
];

const LINE_COLORS = ["var(--color-accent)", "var(--color-success)", "var(--color-x9fc2dc)"];

function seriesLines(series: IndicatorSeries): IndicatorLine[] {
  switch (series.kind) {
    case "sma":
    case "ema":
      return [{ id: series.kind, label: series.kind.toUpperCase(), color: LINE_COLORS[0], values: series.points.map((point) => point.value) }];
    case "macd":
      return [
        { id: "macd", label: "MACD", color: LINE_COLORS[0], values: series.points.map((point) => point.macd) },
        { id: "signal", label: "Sinyal", color: LINE_COLORS[1], values: series.points.map((point) => point.signal) },
        { id: "histogram", label: "Histogram", color: LINE_COLORS[2], values: series.points.map((point) => point.histogram) },
      ];
    case "stoch_rsi":
      return [
        { id: "rsi", label: "RSI", color: LINE_COLORS[0], values: series.points.map((point) => point.rsi) },
        { id: "stoch_rsi", label: "StochRSI", color: LINE_COLORS[1], values: series.points.map((point) => point.stoch_rsi) },
      ];
    case "bollinger":
      return [
        { id: "upper", label: "Üst", color: LINE_COLORS[0], values: series.points.map((point) => point.upper) },
        { id: "middle", label: "Orta", color: LINE_COLORS[1], values: series.points.map((point) => point.middle) },
        { id: "lower", label: "Alt", color: LINE_COLORS[2], values: series.points.map((point) => point.lower) },
      ];
  }
}

function dash(value: string | null): string {
  return value ?? "—";
}

/**
 * Faz 17 AA.2c+AA.2d: gösterge son-değerleri + seri-grafiği (qwen
 * indikatör-çubuğunun GERÇEK karşılığı — `/api/indicators/*`, exact
 * backend). Seri kendi panel-grafiğine bağlanır (fiyat-grafiği üstüne
 * bindirme YOK — osilatör ölçekleri fiyattan farklıdır, ayrı eksen bu
 * dilimde kapsam-dışı). Histogram çizgiyle gösterilir (bar değil).
 */
export function IndicatorPanel({
  kind,
  series,
  status,
  error,
  barCount,
  onSelect,
  onRetry,
}: IndicatorPanelProps) {
  const activeLabel = CHIPS.find((chip) => chip.kind === kind)?.label ?? kind;
  const hasPoints = series !== null && series.kind === kind && series.points.length > 0;
  return <section className="panel indicator-panel" aria-labelledby="indicator-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">GÖSTERGELER · EXACT BACKEND</p>
        <h2 id="indicator-title">İndikatörler</h2>
      </div>
      <span className="revision">{barCount} bar</span>
    </div>
    <div className="chipbar" role="group" aria-label="Gösterge seçimi">
      {CHIPS.map((chip) => (
        <button
          key={chip.kind}
          type="button"
          className={chip.kind === kind ? "chip chip-active" : "chip"}
          aria-pressed={chip.kind === kind}
          onClick={() => onSelect(chip.kind)}
        >
          {chip.label}
        </button>
      ))}
    </div>
    {barCount < 2 && (
      <div className="empty-state" role="status">Hesaplanacak grafik verisi yok — veri kataloğundan bir dataset grafiği yükleyin.</div>
    )}
    {barCount >= 2 && status === "loading" && !hasPoints && (
      <div className="venue-selector-message" role="status">{activeLabel} hesaplanıyor…</div>
    )}
    {barCount >= 2 && status === "error" && (
      <div className="venue-selector-message error" role="alert">
        <strong>{activeLabel} hesaplanamadı.</strong>
        <p>{error}</p>
        <button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button>
      </div>
    )}
    {series !== null && series.kind === kind && series.points.length > 0 && (
      <>
        <dl className="dataset-facts">
          <div><dt>Bar</dt><dd>#{series.points[series.points.length - 1].index}</dd></div>
          {(series.kind === "sma" || series.kind === "ema") && (
            <>
              <div><dt>Son değer ({activeLabel})</dt><dd>{series.points[series.points.length - 1].value}</dd></div>
              <div><dt>Kesinlik</dt><dd>{series.points[series.points.length - 1].exact ? "EXACT" : "FLOAT-SINIRI"}</dd></div>
            </>
          )}
          {series.kind === "macd" && (
            <>
              <div><dt>MACD</dt><dd>{dash(series.points[series.points.length - 1].macd)}</dd></div>
              <div><dt>Sinyal</dt><dd>{dash(series.points[series.points.length - 1].signal)}</dd></div>
              <div><dt>Histogram</dt><dd>{dash(series.points[series.points.length - 1].histogram)}</dd></div>
            </>
          )}
          {series.kind === "stoch_rsi" && (
            <>
              <div><dt>RSI</dt><dd>{dash(series.points[series.points.length - 1].rsi)}</dd></div>
              <div><dt>StochRSI</dt><dd>{dash(series.points[series.points.length - 1].stoch_rsi)}</dd></div>
            </>
          )}
          {series.kind === "bollinger" && (
            <>
              <div><dt>Üst bant</dt><dd>{dash(series.points[series.points.length - 1].upper)}</dd></div>
              <div><dt>Orta bant</dt><dd>{dash(series.points[series.points.length - 1].middle)}</dd></div>
              <div><dt>Alt bant</dt><dd>{dash(series.points[series.points.length - 1].lower)}</dd></div>
              <div><dt>%B</dt><dd>{dash(series.points[series.points.length - 1].percent_b)}</dd></div>
              <div><dt>Kesinlik (orta)</dt><dd>{series.points[series.points.length - 1].middle_exact ? "EXACT" : "FLOAT-SINIRI"}</dd></div>
            </>
          )}
        </dl>
        <IndicatorSeriesChart lines={seriesLines(series)} />
      </>
    )}
    <p className="helper-text">Değerler sunucuda hesaplanır, istemcide türetilmez. Seri kendi grafiğine bağlıdır; histogram çizgiyle gösterilir.</p>
  </section>;
}
