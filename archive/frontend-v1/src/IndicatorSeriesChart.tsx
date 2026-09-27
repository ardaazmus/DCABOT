/* Faz 17 AA.2d: indikatör seri-grafiği (salt render katmanı).
 * Exact-desimal metinler BigInt ile ölçeklenir; `Number` yalnız piksel
 * koordinatına çevrimde kullanılır (CandleChart/EquityCurveChart ile aynı
 * disiplin). Çizgiler aynı closes dizisinden geldiği için pozisyonla
 * hizalanır; null noktalar (ısınma-boşluğu) segmenti böler, birleştirilmez.
 * Finansal hesap yapılmaz; etiketler sunucu-metni aynen. */

export type IndicatorLine = {
  id: string;
  label: string;
  color: string;
  values: (string | null)[];
};

const DECIMAL_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;
const WIDTH = 1000;
const HEIGHT = 300;
const PLOT_LEFT = 12;
const PLOT_RIGHT = 988;
const PLOT_TOP = 34;
const PLOT_BOTTOM = 258;
const DISPLAY_SCALE = 1_000_000n;

const INVALID_MESSAGE = "İndikatör grafiği güvenli biçimde çizilemedi; seri metni bozuk.";

type FixedDecimal = { coefficient: bigint; scale: number };

function parseFixedDecimal(text: string): FixedDecimal | null {
  if (typeof text !== "string" || !DECIMAL_PATTERN.test(text) || text.length > 256) return null;
  const negative = text.startsWith("-");
  const unsigned = negative ? text.slice(1) : text;
  const [integerPart, fractionalPart = ""] = unsigned.split(".");
  const coefficient = BigInt(`${integerPart}${fractionalPart}`);
  return { coefficient: negative ? -coefficient : coefficient, scale: fractionalPart.length };
}

function roundCoordinate(value: number): number {
  return Math.round(value * 1000) / 1000;
}

function pointX(index: number, count: number): number {
  if (count <= 1) return (PLOT_LEFT + PLOT_RIGHT) / 2;
  return roundCoordinate(PLOT_LEFT + (index / (count - 1)) * (PLOT_RIGHT - PLOT_LEFT));
}

function pointY(value: bigint, minimum: bigint, range: bigint): number {
  if (range === 0n) return (PLOT_TOP + PLOT_BOTTOM) / 2;
  const units = ((value - minimum) * DISPLAY_SCALE) / range;
  const ratio = Number(units) / Number(DISPLAY_SCALE);
  return roundCoordinate(PLOT_BOTTOM - ratio * (PLOT_BOTTOM - PLOT_TOP));
}

type IndicatorSeriesChartProps = {
  lines: IndicatorLine[];
};

export function IndicatorSeriesChart({ lines }: IndicatorSeriesChartProps) {
  const count = lines.reduce((max, line) => Math.max(max, line.values.length), 0);
  if (lines.length === 0 || count === 0) return <div className="empty-state" role="status">Grafik serisi yok.</div>;

  let scale = 0;
  const parsed: (FixedDecimal | null | undefined)[][] = lines.map((line) =>
    line.values.map((entry) => {
      if (entry === null) return undefined;
      const field = parseFixedDecimal(entry);
      if (field) scale = Math.max(scale, field.scale);
      return field;
    }),
  );
  if (parsed.some((line) => line.some((field) => field === null))) {
    return <div className="form-error" role="alert">{INVALID_MESSAGE}</div>;
  }
  const values: (bigint | undefined)[][] = parsed.map((line) =>
    line.map((field) => (field === undefined ? undefined : (field as FixedDecimal).coefficient * 10n ** BigInt(scale - (field as FixedDecimal).scale))),
  );
  let minimum: bigint | null = null;
  let maximum: bigint | null = null;
  for (const line of values) {
    for (const value of line) {
      if (value === undefined) continue;
      if (minimum === null || value < minimum) minimum = value;
      if (maximum === null || value > maximum) maximum = value;
    }
  }
  if (minimum === null || maximum === null) return <div className="empty-state" role="status">Grafik serisi yok.</div>;
  const range = maximum - minimum;

  return (
    <div className="indicator-chart-wrap">
      <svg
        className="indicator-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`İndikatör grafiği: ${lines.length} çizgi, ${count} nokta.`}
      >
        <line x1={PLOT_LEFT} y1={PLOT_BOTTOM + 8} x2={PLOT_RIGHT} y2={PLOT_BOTTOM + 8} stroke="var(--color-border)" strokeWidth={1} />
        {lines.map((line, lineIndex) => {
          const segments: { x: number; y: number }[][] = [];
          let current: { x: number; y: number }[] = [];
          values[lineIndex].forEach((value, index) => {
            if (value === undefined) {
              if (current.length > 0) segments.push(current);
              current = [];
              return;
            }
            current.push({ x: pointX(index, count), y: pointY(value, minimum as bigint, range) });
          });
          if (current.length > 0) segments.push(current);
          return (
            <g key={line.id} stroke={line.color} fill="none" strokeWidth={2}>
              {segments.map((points, segmentIndex) =>
                points.length === 1 ? (
                  <circle key={segmentIndex} cx={points[0].x} cy={points[0].y} r={3} fill={line.color} stroke="none" />
                ) : (
                  <polyline key={segmentIndex} points={points.map(({ x, y }) => `${x},${y}`).join(" ")} />
                ),
              )}
            </g>
          );
        })}
      </svg>
      <ul className="indicator-chart-legend" aria-label="Çizgi açıklaması">
        {lines.map((line) => {
          const last = [...line.values].reverse().find((entry) => entry !== null) ?? null;
          return (
            <li key={line.id}>
              <span className="indicator-chart-swatch" style={{ backgroundColor: line.color }} aria-hidden="true" />
              {line.label}: {last ?? "—"}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
