import { CandleChart, type CandleStatus } from "./CandleChart";
import type { HistoricalChartBar } from "./datasetCatalog";

/**
 * Faz 15.1: grafik hero eleman. Referansların tamamında (3Commas/Pionex/
 * Bitsgap) mum grafiği formun yanında HER ZAMAN görünür; DCABOT'ta zincir
 * sonundaydı. Bu panel mevcut `chart-data` sözleşmesini + `CandleChart`'ı
 * yeniden kullanır — yeni veri modeli yok, yalnız yerleşim. Simülasyon
 * zinciri gerekmez: ön-uçuş hazırsa grafik yüklenebilir (sözleşme kanıtı:
 * evidence/F15.1/SONUC.md).
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
}: {
  bars: HistoricalChartBar[];
  status: CandleStatus;
  error: string;
  livePrice: string | null;
  symbolLabel: string;
  canLoad: boolean;
  loadBusy: boolean;
  onLoad: () => void;
}) {
  const showChart = status === "loading" || status === "ready" || status === "error";
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
        <CandleChart bars={bars} status={status} error={error} livePrice={livePrice} />
      ) : (
        <>
          <div className="empty-state" role="status">
            Grafik için veri seçilmedi.
          </div>
          <p className="helper-text">
            Piyasa &amp; Veri bölümünden bir dataset seçip ön-uçuşu tamamlayın, sonra grafiği yükleyin —
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
