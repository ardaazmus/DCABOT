import { type KeyboardEvent } from "react";
import { type HistoricalChartBar, type HistoricalChartData, type HistoricalSimulationResult } from "./datasetCatalog";

type HistoricalChartStatus = "idle" | "loading" | "ready" | "error";

type HistoricalChartProps = {
  data: HistoricalChartData | null;
  status: HistoricalChartStatus;
  error: string;
  simulation: HistoricalSimulationResult | null;
  selectedBarIndex?: number | null;
  onSelectBarIndex?: (barIndex: number) => void;
};

type FixedDecimal = {
  coefficient: bigint;
  scale: number;
};

type ParsedChartBar = {
  source: HistoricalChartBar;
  open: bigint;
  high: bigint;
  low: bigint;
  close: bigint;
};

type ChartGeometry = {
  path: string;
  markers: ChartMarker[];
  markerError: string;
  boundary: ChartBoundary | null;
  boundaryError: string;
  accessibleSummary: string;
};

type ChartMarker = {
  barIndex: number;
  x: number;
};

type ChartBoundary = {
  barIndex: number;
  x: number;
  labelX: number;
  textAnchor: "start" | "end";
};

const MAX_CHART_BARS = 1000;
const DISPLAY_SCALE = 1_000_000n;
const DECIMAL_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
const CHART_WIDTH = 1000;
const CHART_HEIGHT = 320;
const PLOT_LEFT = 12;
const PLOT_RIGHT = 988;
const PLOT_TOP = 18;
const PLOT_BOTTOM = 302;
const MARKER_LANE_Y = 9;
const MARKER_RADIUS = 3;
const MARKER_ERROR = "Aksiyon marker görünümü güvenli biçimde oluşturulamadı; ayrıntılar aksiyon tablosunda.";
const BOUNDARY_ERROR = "Incomplete boundary görünümü güvenli biçimde oluşturulamadı; warning ve prefix tablosu korunur.";

function parseFixedDecimal(text: string): FixedDecimal | null {
  if (!DECIMAL_PATTERN.test(text) || text.length > 256) return null;
  const negative = text.startsWith("-");
  const unsigned = negative ? text.slice(1) : text;
  const [integerPart, fractionalPart = ""] = unsigned.split(".");
  const coefficientText = `${integerPart}${fractionalPart}`;
  const coefficient = BigInt(coefficientText);
  return { coefficient: negative ? -coefficient : coefficient, scale: fractionalPart.length };
}

function scaleCoefficient(value: FixedDecimal, targetScale: number): bigint {
  return value.coefficient * 10n ** BigInt(targetScale - value.scale);
}

function coordinate(value: bigint, minimum: bigint, range: bigint): number {
  if (range === 0n) return (PLOT_TOP + PLOT_BOTTOM) / 2;
  const verticalUnits = ((value - minimum) * DISPLAY_SCALE) / range;
  const ratio = Number(verticalUnits) / Number(DISPLAY_SCALE);
  return roundCoordinate(PLOT_BOTTOM - ratio * (PLOT_BOTTOM - PLOT_TOP));
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function barX(index: number, count: number): number {
  return count === 1 ? (PLOT_LEFT + PLOT_RIGHT) / 2 : PLOT_LEFT + (index / (count - 1)) * (PLOT_RIGHT - PLOT_LEFT);
}

function parseBars(data: HistoricalChartData): ParsedChartBar[] | null {
  if (data.model_id !== "historical_ohlcv_v1" || data.bars.length === 0 || data.bars.length > MAX_CHART_BARS || data.processed_bar_count !== data.bars.length) return null;
  const parsed: Array<{ source: HistoricalChartBar; values: [FixedDecimal, FixedDecimal, FixedDecimal, FixedDecimal] }> = [];
  let targetScale = 0;
  for (const bar of data.bars) {
    const values = [parseFixedDecimal(bar.open), parseFixedDecimal(bar.high), parseFixedDecimal(bar.low), parseFixedDecimal(bar.close)];
    const [open, high, low, close] = values;
    if (open === null || high === null || low === null || close === null) return null;
    const parsedValues: [FixedDecimal, FixedDecimal, FixedDecimal, FixedDecimal] = [open, high, low, close];
    targetScale = Math.max(targetScale, ...parsedValues.map((value) => value.scale));
    parsed.push({ source: bar, values: parsedValues });
  }
  const normalized = parsed.map((bar, index) => {
    const [open, high, low, close] = bar.values;
    const normalizedBar = { source: bar.source, open: scaleCoefficient(open, targetScale), high: scaleCoefficient(high, targetScale), low: scaleCoefficient(low, targetScale), close: scaleCoefficient(close, targetScale) };
    if (normalizedBar.low > normalizedBar.high || normalizedBar.open < normalizedBar.low || normalizedBar.open > normalizedBar.high || normalizedBar.close < normalizedBar.low || normalizedBar.close > normalizedBar.high) return null;
    if (normalizedBar.source.bar_index !== index + 1 || !Number.isSafeInteger(normalizedBar.source.open_time_us) || !Number.isSafeInteger(normalizedBar.source.close_time_us) || normalizedBar.source.close_time_us <= normalizedBar.source.open_time_us) return null;
    const previous = index > 0 ? data.bars[index - 1] : null;
    if (previous && (normalizedBar.source.bar_index <= previous.bar_index || normalizedBar.source.open_time_us <= previous.open_time_us || normalizedBar.source.close_time_us <= previous.close_time_us)) return null;
    return normalizedBar;
  });
  return normalized.every((bar) => bar !== null) ? normalized as ParsedChartBar[] : null;
}

function chartGeometry(data: HistoricalChartData, simulation: HistoricalSimulationResult | null): ChartGeometry | null {
  const bars = parseBars(data);
  if (!bars) return null;
  const minimum = bars.reduce((value, bar) => value < bar.low ? value : bar.low, bars[0].low);
  const maximum = bars.reduce((value, bar) => value > bar.high ? value : bar.high, bars[0].high);
  const range = maximum - minimum;
  const slotWidth = (PLOT_RIGHT - PLOT_LEFT) / bars.length;
  const tickWidth = Math.min(4, Math.max(0.8, slotWidth * 0.28));
  const segments: string[] = [];
  for (const [index, bar] of bars.entries()) {
    const x = barX(index, bars.length);
    const low = coordinate(bar.low, minimum, range);
    const high = coordinate(bar.high, minimum, range);
    const open = coordinate(bar.open, minimum, range);
    const close = coordinate(bar.close, minimum, range);
    segments.push(`M${roundCoordinate(x)} ${low}V${high}M${roundCoordinate(x - tickWidth)} ${open}H${roundCoordinate(x)}M${roundCoordinate(x)} ${close}H${roundCoordinate(x + tickWidth)}`);
  }
  const markerResult = buildMarkers(data, simulation);
  const boundaryResult = buildBoundary(data, simulation);
  const markerSummary = markerResult.markerError
    ? "Aksiyon marker katmanı gösterilmiyor; ayrıntılar aşağıdaki aksiyon tablosunda korunur."
    : markerResult.markers.length === 0
      ? "Bu koşuda gösterilecek aksiyon marker’ı yok."
      : `${markerResult.markers.length.toLocaleString("tr-TR")} nötr aksiyon marker’ı; ayrıntılar aşağıdaki aksiyon tablosunda korunur.`;
  const boundarySummary = boundaryResult.error
    ? "Incomplete boundary katmanı gösterilmiyor; ambiguity ve cutoff bilgisi metin ve prefix tablosunda korunur."
    : boundaryResult.boundary
      ? `INCOMPLETE boundary: ambiguity barı ${boundaryResult.boundary.barIndex}; bu bar commit edilmedi.`
      : "";
  return {
    path: segments.join(""),
    markers: markerResult.markers,
    markerError: markerResult.markerError,
    boundary: boundaryResult.boundary,
    boundaryError: boundaryResult.error,
    accessibleSummary: `${data.bars.length.toLocaleString("tr-TR")} kapalı bar; dönem ${data.period_start} ile ${data.period_end} arasında. Grafik yalnızca read-only tarihsel OHLC overview gösterir; intrabar işlem sırası çıkarılmamıştır. ${markerSummary} ${boundarySummary}`,
  };
}

function buildMarkers(data: HistoricalChartData, simulation: HistoricalSimulationResult | null): { markers: ChartMarker[]; markerError: string } {
  if (!simulation || simulation.execution_status !== "COMPLETED") return { markers: [], markerError: "" };
  if (simulation.dataset.dataset_id !== data.dataset_id || simulation.dataset.artifact_sha256 !== data.artifact_sha256 || simulation.dataset.processed_bar_count !== data.processed_bar_count) return { markers: [], markerError: MARKER_ERROR };
  if (!Array.isArray(simulation.actions)) return { markers: [], markerError: MARKER_ERROR };
  const seenBars = new Set<number>();
  const markers: ChartMarker[] = [];
  for (const action of simulation.actions) {
    if (typeof action !== "object" || action === null || !Number.isSafeInteger(action.bar_index) || action.bar_index < 1 || action.bar_index > data.bars.length || seenBars.has(action.bar_index) || !Number.isSafeInteger(action.open_time_us)) return { markers: [], markerError: MARKER_ERROR };
    const bar = data.bars[action.bar_index - 1];
    if (!bar || bar.bar_index !== action.bar_index || bar.open_time_us !== action.open_time_us) return { markers: [], markerError: MARKER_ERROR };
    seenBars.add(action.bar_index);
    markers.push({ barIndex: action.bar_index, x: barX(action.bar_index - 1, data.bars.length) });
  }
  return { markers, markerError: "" };
}

function buildBoundary(data: HistoricalChartData, simulation: HistoricalSimulationResult | null): { boundary: ChartBoundary | null; error: string } {
  if (!simulation || simulation.execution_status !== "INDETERMINATE" || simulation.marker_authority !== "PREFIX_BOUNDARY_ONLY" || simulation.marker_kind !== "INCOMPLETE_BOUNDARY") return { boundary: null, error: "" };
  const authority = simulation.action_authority;
  const ambiguity = simulation.ambiguity;
  if (!authority || authority.mode !== "COMMITTED_PREFIX" || !ambiguity || !Number.isSafeInteger(ambiguity.bar_index) || !Number.isSafeInteger(ambiguity.open_time_us) || authority.ambiguity_bar_index !== ambiguity.bar_index || authority.committed_through_bar_index === null || authority.committed_through_bar_index >= ambiguity.bar_index || simulation.dataset.dataset_id !== data.dataset_id || simulation.dataset.artifact_sha256 !== data.artifact_sha256 || simulation.dataset.processed_bar_count > data.processed_bar_count || ambiguity.bar_index > data.bars.length) return { boundary: null, error: BOUNDARY_ERROR };
  const bar = data.bars[ambiguity.bar_index - 1];
  if (!bar || bar.bar_index !== ambiguity.bar_index || bar.open_time_us !== ambiguity.open_time_us) return { boundary: null, error: BOUNDARY_ERROR };
  if (!Array.isArray(simulation.actions) || simulation.actions.length !== authority.action_count || simulation.actions.length === 0 || authority.committed_through_event_sequence === null) return { boundary: null, error: BOUNDARY_ERROR };
  const seenBars = new Set<number>();
  for (const action of simulation.actions) {
    const eventSequence = action.event_sequence;
    if (typeof action !== "object" || action === null || !Number.isSafeInteger(action.bar_index) || action.bar_index < 1 || action.bar_index >= ambiguity.bar_index || action.bar_index > authority.committed_through_bar_index || seenBars.has(action.bar_index) || !Number.isSafeInteger(action.open_time_us) || typeof eventSequence !== "number" || !Number.isSafeInteger(eventSequence) || eventSequence > authority.committed_through_event_sequence) return { boundary: null, error: BOUNDARY_ERROR };
    const actionBar = data.bars[action.bar_index - 1];
    if (!actionBar || actionBar.open_time_us !== action.open_time_us) return { boundary: null, error: BOUNDARY_ERROR };
    seenBars.add(action.bar_index);
  }
  const x = barX(ambiguity.bar_index - 1, data.bars.length);
  const nearRightEdge = x > CHART_WIDTH - 150;
  return { boundary: { barIndex: ambiguity.bar_index, x, labelX: nearRightEdge ? x - 7 : x + 7, textAnchor: nearRightEdge ? "end" : "start" }, error: "" };
}

export function HistoricalChart({ data, status, error, simulation, selectedBarIndex = null, onSelectBarIndex }: HistoricalChartProps) {
  if (status === "idle") return null;
  const titleId = "historical-chart-title";
  const descriptionId = "historical-chart-description";
  const captionId = "historical-chart-caption";
  const geometry = status === "ready" && data ? chartGeometry(data, simulation) : null;
  const renderError = status === "ready" && !geometry;
  const interactive = typeof onSelectBarIndex === "function";

  function onMarkerKeyDown(event: KeyboardEvent<SVGCircleElement>, barIndex: number) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onSelectBarIndex?.(barIndex);
  }
  return <section className={`historical-chart ${renderError ? "error" : status}`} aria-labelledby={titleId}>
    <div className="historical-chart-heading"><div><p className="preflight-section-label">TARİHSEL OHLC GÖRÜNÜMÜ</p><h6 id={titleId}>Kapalı bar grafiği</h6></div><span className="historical-chart-badge">READ-ONLY</span></div>
    {status === "loading" && <div className="historical-chart-state" role="status" aria-live="polite">Grafik verisi hazırlanıyor…</div>}
    {status === "error" && <div className="historical-chart-state error" role="alert">{error || "Tarihsel OHLC görünümü güvenli biçimde oluşturulamadı."}</div>}
    {renderError && <div className="historical-chart-state error" role="alert">Tarihsel OHLC görünümü güvenli biçimde oluşturulamadı.</div>}
    {geometry && data && <figure className="historical-chart-figure">
      <svg className="historical-chart-svg" viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} role="img" aria-labelledby={`${titleId} ${descriptionId}`} focusable="false">
        <title id={titleId}>Kapalı bar tarihsel OHLC grafiği</title>
        <desc id={descriptionId}>{geometry.accessibleSummary}</desc>
        <path className="historical-chart-path" d={geometry.path} vectorEffect="non-scaling-stroke" />
        <g className="historical-chart-markers" aria-hidden={interactive ? undefined : true}>
          {geometry.markers.map((marker, index) => {
            const selected = selectedBarIndex === marker.barIndex;
            return <circle
              className={`historical-chart-marker${interactive ? " historical-chart-marker-interactive" : ""}${selected ? " historical-chart-marker-selected" : ""}`}
              key={`${marker.barIndex}-${index}`}
              cx={roundCoordinate(marker.x)}
              cy={MARKER_LANE_Y}
              r={MARKER_RADIUS}
              role={interactive ? "button" : undefined}
              tabIndex={interactive ? 0 : undefined}
              aria-label={interactive ? `Bar ${marker.barIndex} aksiyonunu seç` : undefined}
              aria-pressed={interactive ? selected : undefined}
              onClick={interactive ? () => onSelectBarIndex?.(marker.barIndex) : undefined}
              onKeyDown={interactive ? (event) => onMarkerKeyDown(event, marker.barIndex) : undefined}
            />;
          })}
          {geometry.boundary && <><line className="historical-chart-boundary" x1={roundCoordinate(geometry.boundary.x)} y1={PLOT_TOP} x2={roundCoordinate(geometry.boundary.x)} y2={PLOT_BOTTOM} /><text className="historical-chart-boundary-label" x={roundCoordinate(geometry.boundary.labelX)} y={PLOT_TOP + 14} textAnchor={geometry.boundary.textAnchor}>INCOMPLETE · BAR {geometry.boundary.barIndex}</text></>}
        </g>
      </svg>
      <figcaption id={captionId} className="historical-chart-caption">{geometry.accessibleSummary} Kesin fill zamanı ve intrabar sıra gösterilmez.</figcaption>
    </figure>}
    {geometry?.markerError && <div className="historical-chart-marker-warning" role="status">{geometry.markerError}</div>}
    {geometry?.boundaryError && <div className="historical-chart-marker-warning" role="status">{geometry.boundaryError}</div>}
  </section>;
}
