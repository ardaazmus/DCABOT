/* Faz 17 AA.7: equity-eğrisi çizgi-grafiği (salt render katmanı).
 * Bar-başına exact equity metinleri BigInt ile ölçeklenir; `Number`
 * yalnız piksel koordinatına çevrimde kullanılır (CandleChart ile aynı
 * disiplin). Finansal hesap yapılmaz; eksen-etiketleri sunucu-metni
 * aynen. `points` çağrıcıda `isEquityCurve` ile doğrulanır. */

const DECIMAL_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
const WIDTH = 1000;
const HEIGHT = 300;
const PLOT_LEFT = 12;
const PLOT_RIGHT = 988;
const PLOT_TOP = 34;
const PLOT_BOTTOM = 258;
const DISPLAY_SCALE = 1_000_000n;

const INVALID_MESSAGE = "Equity eğrisi güvenli biçimde çizilemedi; equity metni bozuk.";

type FixedDecimal = { coefficient: bigint; scale: number };

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

function pointX(index: number, count: number): number {
  if (count === 1) return (PLOT_LEFT + PLOT_RIGHT) / 2;
  return roundCoordinate(PLOT_LEFT + (index / (count - 1)) * (PLOT_RIGHT - PLOT_LEFT));
}

function pointY(value: bigint, minimum: bigint, range: bigint): number {
  if (range === 0n) return (PLOT_TOP + PLOT_BOTTOM) / 2;
  const units = ((value - minimum) * DISPLAY_SCALE) / range;
  const ratio = Number(units) / Number(DISPLAY_SCALE);
  return roundCoordinate(PLOT_BOTTOM - ratio * (PLOT_BOTTOM - PLOT_TOP));
}

type EquityCurveChartProps = {
  points: string[];
};

export function EquityCurveChart({ points }: EquityCurveChartProps) {
  if (points.length === 0) return <div className="empty-state" role="status">Equity eğrisi yok.</div>;

  let scale = 0;
  const parsed: (FixedDecimal | null)[] = points.map((point) => {
    const field = parseFixedDecimal(point);
    if (field) scale = Math.max(scale, field.scale);
    return field;
  });
  if (parsed.some((field) => field === null)) {
    return <div className="form-error" role="alert">{INVALID_MESSAGE}</div>;
  }
  const values = (parsed as FixedDecimal[]).map((field) => scaleTo(field, scale));
  let minimum = values[0];
  let maximum = values[0];
  for (const value of values) {
    if (value < minimum) minimum = value;
    if (value > maximum) maximum = value;
  }
  const range = maximum - minimum;
  const coords = values.map((value, index) => ({ x: pointX(index, values.length), y: pointY(value, minimum, range) }));
  const minIndex = values.indexOf(minimum);
  const maxIndex = values.indexOf(maximum);

  return (
    <div className="equity-chart-wrap">
      <svg
        className="equity-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Equity eğrisi: ${values.length} nokta, aralık ${points[minIndex]}–${points[maxIndex]}.`}
      >
        <line x1={PLOT_LEFT} y1={PLOT_BOTTOM + 8} x2={PLOT_RIGHT} y2={PLOT_BOTTOM + 8} stroke="var(--color-border)" strokeWidth={1} />
        {coords.length === 1 ? (
          <circle cx={coords[0].x} cy={coords[0].y} r={4} fill="var(--color-accent)" />
        ) : (
          <polyline
            points={coords.map(({ x, y }) => `${x},${y}`).join(" ")}
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth={2}
          />
        )}
        <text x={PLOT_RIGHT} y={pointY(maximum, minimum, range) - 6} textAnchor="end" className="equity-chart-label">{points[maxIndex]}</text>
        <text x={PLOT_RIGHT} y={pointY(minimum, minimum, range) + 16} textAnchor="end" className="equity-chart-label">{points[minIndex]}</text>
      </svg>
    </div>
  );
}
