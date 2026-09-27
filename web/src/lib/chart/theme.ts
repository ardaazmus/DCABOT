import {
  ColorType,
  type ChartOptions,
  type DeepPartial,
  type TickMarkType,
  type Time,
} from "lightweight-charts";

export type ChartPalette = {
  profit: string;
  loss: string;
  safety: string;
  entry: string;
  accent: string;
  border: string;
  muted: string;
};

/** Token renkleri yalnız CSS'ten okunur; bileşende ham renk yok. */
const EMPTY_PALETTE: ChartPalette = {
  profit: "",
  loss: "",
  safety: "",
  entry: "",
  accent: "",
  border: "",
  muted: "",
};

/**
 * Sunucuda ön-çizim sırasında `document` yoktur; grafik efektleri yalnız
 * istemcide çalıştığı için boş palet zararsızdır (DOM'a yazılmaz).
 */
export function paletteSnapshot(): ChartPalette {
  if (typeof document === "undefined") return EMPTY_PALETTE;
  return readPalette();
}

const LAB_PATTERN =
  /^lab\(\s*([\d.]+)%?\s+(-?[\d.eE+-]+)\s+(-?[\d.eE+-]+)\s*(?:\/\s*([\d.]+%?)\s*)?\)$/;

/**
 * Hesaplanmış `lab()` rengini sRGB `rgb()/rgba()` metnine çevirir.
 * Chromium `oklch()` token'ları `lab()` olarak verir; grafik
 * kütüphanesi yalnız sRGB renkleri kabul eder. Renk hesabı piksel
 * işidir, finans disiplininin dışındadır.
 */
export function labToRgb(raw: string): string {
  const match = LAB_PATTERN.exec(raw);
  if (match === null) return raw;
  const l = Number(match[1]) / 100;
  const a = Number(match[2]);
  const b = Number(match[3]);
  const alphaRaw = match[4];
  const alpha =
    alphaRaw === undefined
      ? 1
      : alphaRaw.endsWith("%")
        ? Number(alphaRaw.slice(0, -1)) / 100
        : Number(alphaRaw);
  if (![l, a, b, alpha].every((v) => Number.isFinite(v))) return raw;

  // CIELAB → XYZ (D65).
  const epsilon = 216 / 24389;
  const kappa = 24389 / 27;
  const fy = (l * 100 + 16) / 116;
  const fx = fy + a / 500;
  const fz = fy - b / 200;
  const pivot = (t: number) =>
    t ** 3 > epsilon ? t ** 3 : (116 * t - 16) / kappa;
  const x = 0.95047 * pivot(fx);
  const y = pivot(fy);
  const z = 1.08883 * pivot(fz);

  // XYZ → doğrusal sRGB → gama sRGB.
  const linear = [
    3.2404542 * x - 1.5371385 * y - 0.4985314 * z,
    -0.969266 * x + 1.8760108 * y + 0.041556 * z,
    0.0556434 * x - 0.2040259 * y + 1.0572252 * z,
  ];
  const gamma = (c: number) =>
    c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055;
  const [r, g, bl] = linear.map((c) =>
    Math.min(255, Math.max(0, Math.round(gamma(c) * 255))),
  );
  return alpha >= 1
    ? `rgb(${r}, ${g}, ${bl})`
    : `rgba(${r}, ${g}, ${bl}, ${alpha})`;
}

const RGB_PATTERN = /^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)$/;

/**
 * `rgb()/rgba()` renge opaklık uygular (kısmi ay solukluğu).
 * Ayrıştırılamayan renk aynen döner. Piksel işidir.
 */
export function withAlpha(color: string, alpha: number): string {
  const match = RGB_PATTERN.exec(color);
  if (match === null) return color;
  const [r, g, b] = [match[1], match[2], match[3]].map(Number);
  if (![r, g, b].every((v) => Number.isFinite(v))) return color;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function readPalette(): ChartPalette {
  const css = getComputedStyle(document.documentElement);
  const read = (name: string) => labToRgb(css.getPropertyValue(name).trim());
  return {
    profit: read("--profit"),
    loss: read("--loss"),
    safety: read("--safety"),
    entry: read("--entry"),
    accent: read("--accent"),
    border: read("--border"),
    muted: read("--muted-foreground"),
  };
}

/**
 * Grafik fiyat ekseni etiketi. Kütüphane sayıyı verir, biz metni
 * yerelleştiririz: TR `84.396,04`, EN `84,396.04`. Piksel işidir.
 */
/**
 * Günlük x-ekseni biçimleyici: aynı günün tekrar eden etiketini
 * bastırır ("14 14" yerine "14"). Durum tek grafik+veri içindir;
 * veri değişince yeniden kurulur.
 */
export function createDayTickFormatter(): (
  time: Time,
  tickMarkType: TickMarkType,
  locale: string,
) => string {
  let lastDay = "";
  return (time: Time) => {
    const date =
      typeof time === "number"
        ? new Date(time * 1000)
        : typeof time === "string"
          ? new Date(`${time}T00:00:00Z`)
          : new Date(Date.UTC(time.year, time.month - 1, time.day));
    const day = `${date.getUTCFullYear()}-${date.getUTCMonth()}-${date.getUTCDate()}`;
    if (day === lastDay) return "";
    lastDay = day;
    return String(date.getUTCDate());
  };
}

export function formatPriceAxis(value: number, locale: string): string {
  if (!Number.isFinite(value)) return "—";
  const negative = value < 0;
  const [integer, fraction] = Math.abs(value).toFixed(2).split(".");
  const grouper = locale === "tr" ? "." : ",";
  const grouped = (integer ?? "0").replace(/\B(?=(\d{3})+(?!\d))/g, grouper);
  const decimal = locale === "tr" ? "," : ".";
  return `${negative ? "-" : ""}${grouped}${decimal}${fraction ?? "00"}`;
}

export function baseChartOptions(
  height: number,
  palette: ChartPalette,
  locale: string,
): DeepPartial<ChartOptions> {
  return {
    height,
    layout: {
      background: { type: ColorType.Solid, color: "transparent" },
      textColor: palette.muted,
      fontFamily: "'Inter Variable', ui-sans-serif, system-ui, sans-serif",
      fontSize: 11,
    },
    grid: {
      vertLines: { color: palette.border },
      horzLines: { color: palette.border },
    },
    crosshair: {
      vertLine: { color: palette.border, labelBackgroundColor: palette.muted },
      horzLine: { color: palette.border, labelBackgroundColor: palette.muted },
    },
    timeScale: { borderColor: palette.border },
    rightPriceScale: { borderColor: palette.border },
    localization: { locale, priceFormatter: (value: number) => formatPriceAxis(value, locale) },
  };
}
