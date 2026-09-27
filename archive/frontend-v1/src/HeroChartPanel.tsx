import { lazy, Suspense } from "react";
import type { ChartPriceLine, ChartStatus } from "./TradingChart";
import type { HistoricalChartBar } from "./datasetCatalog";

// lightweight-charts is a real charting library (~250KB) -- lazy-loaded so it
// only enters the bundle when a chart is actually shown, per Faz 11's
// code-splitting rule (App.tsx already does this for DatasetCatalogPanel/
// SavedRunsPanel).
const TradingChart = lazy(() => import("./TradingChart").then((m) => ({ default: m.TradingChart })));

/**
 * Faz 15.1 + 16.1: grafik hero eleman, artık gerçek TradingView Lightweight
 * Charts kütüphanesiyle (Arda'nın kendi teknoloji kararı, bkz. docs/
 * ARASTIRMA_FAZ16_QWEN_VIZYON_HARITASI.md §1 madde 5). Bar özeti burada
 * hesaplanır (yalnız görüntü amaçlı sayaç, ekonomik karar değil); canlı
 * baskı fiyatı bir referans price-line olarak grafiğe işlenir.
 */
export function HeroChartPanel({
  bars,
  status,
  error,
  livePrice,
  symbolLabel,
  canLoad,
  loadBusy,
  onLoad,
  overlayLines,
}: {
  bars: HistoricalChartBar[];
  status: ChartStatus;
  error: string;
  livePrice: string | null;
  symbolLabel: string;
  canLoad: boolean;
  loadBusy: boolean;
  onLoad: () => void;
  /** Faz 17 A.3: parametre-overlay çizgileri (backend hesabının çizimi). */
  overlayLines?: ChartPriceLine[];
}) {
  const showChart = status === "loading" || status === "ready" || status === "error";
  let upCount = 0;
  let downCount = 0;
  for (const bar of bars) {
    const open = Number(bar.open);
    const close = Number(bar.close);
    if (close > open) upCount += 1;
    else if (close < open) downCount += 1;
  }
  const flatCount = bars.length - upCount - downCount;
  const priceLines: ChartPriceLine[] = [
    ...(overlayLines ?? []),
    ...(livePrice !== null ? [{ id: "live", price: livePrice, color: "#fbbf24", title: "Canlı", lineStyle: "dashed" } as ChartPriceLine] : []),
  ];
  return (
    <section className="panel hero-chart-panel" aria-labelledby="hero-chart-title">
      <div className="panel-heading hero-chart-head">
        <div>
          <p className="eyebrow">HERO CHART</p>
          <h2 id="hero-chart-title">Piyasa grafiği · {symbolLabel}</h2>
        </div>
        {status === "ready" ? (
          <span className="state-label ready">Güncel</span>
        ) : status === "loading" ? (
          <span className="state-label pending">Yükleniyor</span>
        ) : status === "error" ? (
          <span className="state-label error">Hata</span>
        ) : (
          <span className="state-label">Veri bekleniyor</span>
        )}
      </div>
      {showChart ? (
        <>
          <Suspense fallback={<div className="empty-state" role="status">Grafik motoru yükleniyor…</div>}>
            <TradingChart bars={bars} status={status} error={error} priceLines={priceLines} />
          </Suspense>
          {status === "ready" && (
            <p className="table-note">
              {bars.length} bar · {upCount} yükselen · {downCount} düşen · {flatCount} yatay
              {livePrice !== null ? ` · canlı: ${livePrice}` : ""}
            </p>
          )}
        </>
      ) : (
        <>
          <div className="empty-state" role="status">
            Grafik için veri seçilmedi.
          </div>
          <p className="helper-text">
            Backtest bölümünden bir dataset seçip ön-uçuşu tamamlayın, sonra grafiği yükleyin —
            simülasyon zincirini beklemek gerekmez.
            {livePrice !== null ? ` Son canlı baskı: ${livePrice}.` : ""}
          </p>
          <button
            className="secondary-button"
            type="button"
            disabled={!canLoad || loadBusy}
            onClick={onLoad}
          >
            {loadBusy ? "Yükleniyor…" : "Grafiği yükle"}
          </button>
        </>
      )}
    </section>
  );
}
