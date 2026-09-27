import type { ChartPriceLine } from "./TradingChart";

/** Backend `/api/preview` yanıtındaki seviye satırının overlay için yeterli altkümesi. */
export type PreviewOverlayLevel = {
  index: number;
  price: string;
};

const ENTRY_COLOR = "#94a3b8";
const SO_COLOR = "rgba(251,191,36,.85)";

/**
 * Faz 17 A.3: backend `/api/preview` yanıtını (hizalanmış `anchor` + SO
 * merdiveni) grafik price-line'larına çevirir. Renk/etiket/stil qwen Bot Kur
 * bölümünden verbatim (RG-QWEN-HTML `updateDcaPreview`): GİRİŞ gri düz çizgi,
 * SO'lar kesikli amber, tek numaralı + son SO etiketli.
 *
 * Hesap YOK — yalnız çizim. TP/SL/ortalama-maliyet/likidasyon çizgisi
 * özellikle YOK: backend `preview` yanıtı bu alanları vermiyor, UI'da
 * finansal hesap yasak (AGENTS.md para kuralı). Bozuk satır atlanır.
 */
export function previewToPriceLines(
  anchor: string | null | undefined,
  levels: readonly PreviewOverlayLevel[] | null | undefined,
): ChartPriceLine[] {
  const lines: ChartPriceLine[] = [];
  if (typeof anchor === "string" && anchor.trim() !== "") {
    lines.push({ id: "entry", price: anchor, color: ENTRY_COLOR, title: "GİRİŞ", lineStyle: "solid" });
  }
  if (!Array.isArray(levels)) return lines;
  const valid = levels.filter(
    (level): level is PreviewOverlayLevel =>
      typeof level === "object" && level !== null
      && Number.isInteger(level.index) && level.index >= 1
      && typeof level.price === "string" && level.price.trim() !== "",
  );
  if (valid.length === 0) return lines;
  const last = Math.max(...valid.map((level) => level.index));
  for (const level of valid) {
    const labeled = level.index % 2 === 1 || level.index === last;
    lines.push({
      id: `so-${level.index}`,
      price: level.price,
      color: SO_COLOR,
      title: labeled ? `SO#${level.index}` : "",
      lineStyle: "dashed",
    });
  }
  return lines;
}
