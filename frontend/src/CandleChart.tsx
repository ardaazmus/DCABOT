import type { HistoricalChartBar } from "./datasetCatalog";

export type CandleStatus = "idle" | "loading" | "ready" | "error";

export type CandleMarker = {
  barIndex: number;
  kind: "buy" | "sell" | "info";
  label?: string;
};

export type CandleChartProps = {
  bars: HistoricalChartBar[];
  status: CandleStatus;
  error: string;
  markers?: CandleMarker[];
  livePrice?: string | null;
  selectedBarIndex?: number | null;
  onSelectBarIndex?: (barIndex: number) => void;
};

const MAX_CANDLES = 300;
const DISPLAY_SCALE = 1_000_000n;
const DECIMAL_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
const WIDTH = 1000;
const HEIGHT = 360;
const PLOT_LEFT = 12;
const PLOT_RIGHT = 988;
const PRICE_TOP = 26;
const PRICE_BOTTOM = 252;
const VOLUME_TOP = 268;
const VOLUME_BOTTOM = 348;
const MARKER_Y = 12;

const INVALID_MESSAGE = "Mum grafiği güvenli biçimde oluşturulamadı; fiyat/hacim metni bozuk.";

type FixedDecimal = { coefficient: bigint; scale: number };

type ParsedBar = {
  source: HistoricalChartBar;
  open: bigint;
  high: bigint;
  low: bigint;
  close: bigint;
  volume: bigint;
};

function parseFixedDecimal(text: string): FixedDecimal | null {
  if (typeof text !== "string" || !DECIMAL_PATTERN.test(text) || text.length > 256) return null;
  const negative = text.startsWith("-");
  const unsigned = negative ? text.slice(1) : text;
  const [integerPart, fractionalPart = ""] = unsigned.split(".");
  const coefficient = BigInt(`${integerPart}${fractionalPart}`);
  return { coefficient: negative ? -coefficient : coefficient, scale: fractionalPart.length };
}

function scaleTo(value: FixedDecimal, targetScale: number): bigint {
  return value.coefficient * 10n ** BigInt(targetScale - value.scale);
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function priceY(value: bigint, minimum: bigint, range: bigint): number {
  if (range === 0n) return (PRICE_TOP + PRICE_BOTTOM) / 2;
  const units = ((value - minimum) * DISPLAY_SCALE) / range;
  const ratio = Number(units) / Number(DISPLAY_SCALE);
  return roundCoordinate(PRICE_BOTTOM - ratio * (PRICE_BOTTOM - PRICE_TOP));
}

function volumeHeight(value: bigint, maximum: bigint): number {
  if (maximum <= 0n) return 0;
  const units = (value * DISPLAY_SCALE) / maximum;
  const ratio = Number(units) / Number(DISPLAY_SCALE);
  return roundCoordinate(ratio * (VOLUME_BOTTOM - VOLUME_TOP));
}

function barX(index: number, count: number): number {
  if (count === 1) return (PLOT_LEFT + PLOT_RIGHT) / 2;
  return roundCoordinate(PLOT_LEFT + (index / (count - 1)) * (PLOT_RIGHT - PLOT_LEFT));
}

function slotWidth(count: number): number {
  if (count === 1) return 40;
  return Math.max(2, roundCoordinate(((PLOT_RIGHT - PLOT_LEFT) / count) * 0.62));
}

function markerFill(kind: CandleMarker["kind"]): string {
  if (kind === "buy") return "var(--color-success)";
  if (kind === "sell") return "var(--color-danger)";
  return "var(--color-accent)";
}

/**
 * Faz 12.1: gerçek mum + hacim grafiği (salt render katmanı).
 * Fiyat/hacim metinleri BigInt ile ölçeklenir; `Number` yalnız piksel
 * koordinatına çevrimde kullanılır (HistoricalChart ile aynı disiplin).
 * Finansal hesap yapılmaz; çekirdek tek doğruluk kaynağıdır.
 */
export function CandleChart({
  bars,
  status,
  error,
  markers = [],
  livePrice = null,
  selectedBarIndex = null,
  onSelectBarIndex,
}: CandleChartProps) {
  if (status === "loading") return <div className="empty-state" role="status">Grafik yükleniyor…</div>;
  if (status === "error") return <div className="form-error" role="alert">{error || "Grafik yüklenemedi."}</div>;
  if (status === "idle" || bars.length === 0) return <div className="empty-state" role="status">Grafik için veri seçilmedi.</div>;

  const windowed = bars.length > MAX_CANDLES ? bars.slice(bars.length - MAX_CANDLES) : bars;

  let priceScale = 0;
  let volumeScale = 0;
  const parsedPrices: (FixedDecimal | null)[] = [];
  const parsedVolumes: (FixedDecimal | null)[] = [];
  for (const bar of windowed) {
    const fields = [bar.open, bar.high, bar.low, bar.close].map(parseFixedDecimal);
    const volume = parseFixedDecimal(bar.base_volume);
    parsedPrices.push(...fields);
    parsedVolumes.push(volume);
    for (const field of fields) if (field) priceScale = Math.max(priceScale, field.scale);
    if (volume) volumeScale = Math.max(volumeScale, volume.scale);
  }
  const liveParsed = livePrice === null || livePrice === "" ? null : parseFixedDecimal(livePrice);
  if (liveParsed) priceScale = Math.max(priceScale, liveParsed.scale);
  const liveInvalid = livePrice !== null && livePrice !== "" && liveParsed === null;
  if (parsedPrices.some((field) => field === null) || parsedVolumes.some((field) => field === null) || liveInvalid) {
    return <div className="form-error" role="alert">{INVALID_MESSAGE}</div>;
  }

  const parsed: ParsedBar[] = windowed.map((source, index) => ({
    source,
    open: scaleTo(parsedPrices[index * 4] as FixedDecimal, priceScale),
    high: scaleTo(parsedPrices[index * 4 + 1] as FixedDecimal, priceScale),
    low: scaleTo(parsedPrices[index * 4 + 2] as FixedDecimal, priceScale),
    close: scaleTo(parsedPrices[index * 4 + 3] as FixedDecimal, priceScale),
    volume: scaleTo(parsedVolumes[index] as FixedDecimal, volumeScale),
  }));
  if (parsed.some((bar) => bar.volume < 0n)) {
    return <div className="form-error" role="alert">{INVALID_MESSAGE}</div>;
  }

  let minimum = parsed[0].low;
  let maximum = parsed[0].high;
  let maxVolume = parsed[0].volume;
  for (const bar of parsed) {
    if (bar.low < minimum) minimum = bar.low;
    if (bar.high > maximum) maximum = bar.high;
    if (bar.volume > maxVolume) maxVolume = bar.volume;
  }
  const liveValue = liveParsed ? scaleTo(liveParsed, priceScale) : null;
  if (liveValue !== null) {
    if (liveValue < minimum) minimum = liveValue;
    if (liveValue > maximum) maximum = liveValue;
  }
  const range = maximum - minimum;

  let upCount = 0;
  let downCount = 0;
  for (const bar of parsed) {
    if (bar.close > bar.open) upCount += 1;
    else if (bar.close < bar.open) downCount += 1;
  }
  const flatCount = parsed.length - upCount - downCount;

  const bodyWidth = slotWidth(parsed.length);
  const markerByBar = new Map<number, CandleMarker[]>();
  for (const marker of markers) {
    const list = markerByBar.get(marker.barIndex) ?? [];
    list.push(marker);
    markerByBar.set(marker.barIndex, list);
  }

  const liveY = liveValue === null ? null : priceY(liveValue, minimum, range);

  return (
    <div className="candle-chart-wrap">
      <svg
        className="candle-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Mum grafiği: ${parsed.length} bar, ${upCount} yükselen, ${downCount} düşen, ${flatCount} yatay.`}
      >
        <line x1={PLOT_LEFT} y1={VOLUME_TOP - 8} x2={PLOT_RIGHT} y2={VOLUME_TOP - 8} stroke="var(--color-border)" strokeWidth={1} />
        {parsed.map((bar, index) => {
          const x = barX(index, parsed.length);
          const direction = bar.close > bar.open ? "up" : bar.close < bar.open ? "down" : "flat";
          const fill = direction === "up" ? "var(--color-success)" : direction === "down" ? "var(--color-danger)" : "var(--color-text-muted)";
          const top = priceY(bar.close > bar.open ? bar.close : bar.open, minimum, range);
          const bottom = priceY(bar.close > bar.open ? bar.open : bar.close, minimum, range);
          const height = Math.max(1, roundCoordinate(bottom - top));
          const vHeight = volumeHeight(bar.volume, maxVolume);
          const selected = selectedBarIndex === bar.source.bar_index;
          return (
            <g key={bar.source.bar_index} data-candle={direction}>
              <line x1={x} y1={priceY(bar.high, minimum, range)} x2={x} y2={priceY(bar.low, minimum, range)} stroke={fill} strokeWidth={direction === "flat" ? 2 : 1.5} />
              {direction === "flat" ? (
                <line x1={roundCoordinate(x - bodyWidth / 2)} y1={top} x2={roundCoordinate(x + bodyWidth / 2)} y2={top} stroke={fill} strokeWidth={2.5} />
              ) : (
                <rect x={roundCoordinate(x - bodyWidth / 2)} y={top} width={bodyWidth} height={height} fill={fill} />
              )}
              <rect
                x={roundCoordinate(x - bodyWidth / 2)}
                y={roundCoordinate(VOLUME_BOTTOM - vHeight)}
                width={bodyWidth}
                height={vHeight}
                fill="var(--color-accent)"
                fillOpacity={0.35}
                data-volume="true"
              />
              {(markerByBar.get(bar.source.bar_index) ?? []).map((marker, markerIndex) => (
                <circle key={markerIndex} cx={x} cy={MARKER_Y} r={4} fill={markerFill(marker.kind)} data-marker={marker.kind}>
                  <title>{marker.label ?? marker.kind}</title>
                </circle>
              ))}
              {selected && (
                <rect x={roundCoordinate(x - bodyWidth / 2 - 2)} y={PRICE_TOP - 6} width={bodyWidth + 4} height={PRICE_BOTTOM - PRICE_TOP + 12} fill="none" stroke="var(--color-focus)" strokeWidth={1.5} strokeDasharray="4 2" />
              )}
            </g>
          );
        })}
        {liveY !== null && liveValue !== null && (
          <g data-live-price="true">
            <line x1={PLOT_LEFT} y1={liveY} x2={PLOT_RIGHT} y2={liveY} stroke="var(--color-focus)" strokeWidth={1.5} strokeDasharray="6 3" />
            <text x={PLOT_RIGHT - 4} y={roundCoordinate(liveY - 5)} textAnchor="end" fontSize={13} fill="var(--color-focus)">
              {livePrice}
            </text>
          </g>
        )}
      </svg>
      <p className="helper-text">
        {parsed.length} bar · {upCount} yükselen · {downCount} düşen · {flatCount} yatay
        {bars.length > MAX_CANDLES ? ` · son ${MAX_CANDLES} bar gösteriliyor (toplam ${bars.length})` : ""}
        {liveValue !== null ? ` · canlı: ${livePrice}` : ""}
      </p>
      {onSelectBarIndex && (
        <div className="candle-bar-select" role="group" aria-label="Bar seçimi">
          {parsed.map((bar) => (
            <button
              key={bar.source.bar_index}
              className="candle-bar-button"
              type="button"
              aria-pressed={selectedBarIndex === bar.source.bar_index}
              aria-label={`Bar ${bar.source.bar_index}: açılış ${bar.source.open}, kapanış ${bar.source.close}`}
              onClick={() => onSelectBarIndex(bar.source.bar_index)}
            >
              {bar.source.bar_index}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export type TickStripProps = {
  ticks: { price: string }[];
  label: string;
};

const TICK_WIDTH = 1000;
const TICK_HEIGHT = 120;
const TICK_TOP = 12;
const TICK_BOTTOM = 108;

/**
 * Canlı baskı şeridi: paper print'ler tick çizgisi olarak akar.
 * Mum uydurulmaz — yalnız gözlenen fiyatlar, aynı exact parse disipliniyle.
 */
export function LiveTickStrip({ ticks, label }: TickStripProps) {
  if (ticks.length === 0) return <div className="empty-state" role="status">Henüz baskı yok.</div>;
  const windowed = ticks.length > MAX_CANDLES ? ticks.slice(ticks.length - MAX_CANDLES) : ticks;
  const fields = windowed.map((tick) => parseFixedDecimal(tick.price));
  if (fields.some((field) => field === null)) {
    return <div className="form-error" role="alert">{INVALID_MESSAGE}</div>;
  }
  const scale = Math.max(...(fields as FixedDecimal[]).map((field) => field.scale));
  const values = (fields as FixedDecimal[]).map((field) => scaleTo(field, scale));
  let minimum = values[0];
  let maximum = values[0];
  for (const value of values) {
    if (value < minimum) minimum = value;
    if (value > maximum) maximum = value;
  }
  const range = maximum - minimum;
  function tickY(value: bigint): number {
    if (range === 0n) return (TICK_TOP + TICK_BOTTOM) / 2;
    const units = ((value - minimum) * DISPLAY_SCALE) / range;
    const ratio = Number(units) / Number(DISPLAY_SCALE);
    return roundCoordinate(TICK_BOTTOM - ratio * (TICK_BOTTOM - TICK_TOP));
  }
  function tickX(index: number): number {
    if (values.length === 1) return (PLOT_LEFT + PLOT_RIGHT) / 2;
    return roundCoordinate(PLOT_LEFT + (index / (values.length - 1)) * (PLOT_RIGHT - PLOT_LEFT));
  }
  const points = values.map((value, index) => `${tickX(index)},${tickY(value)}`).join(" ");
  const last = windowed[windowed.length - 1].price;
  return (
    <div className="tick-strip-wrap">
      <svg className="tick-strip" viewBox={`0 0 ${TICK_WIDTH} ${TICK_HEIGHT}`} role="img" aria-label={`${label}: ${values.length} baskı, son fiyat ${last}.`}>
        <polyline points={points} fill="none" stroke="var(--color-accent)" strokeWidth={2} data-ticks={values.length} />
        <circle cx={tickX(values.length - 1)} cy={tickY(values[values.length - 1])} r={4} fill="var(--color-focus)" data-live-dot="true" />
        <text x={PLOT_RIGHT - 4} y={roundCoordinate(tickY(values[values.length - 1]) - 8)} textAnchor="end" fontSize={14} fill="var(--color-focus)">
          {last}
        </text>
      </svg>
      <p className="helper-text">{values.length} baskı · son: {last}</p>
    </div>
  );
}
