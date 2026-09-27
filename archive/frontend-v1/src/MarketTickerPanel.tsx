export type VenueTicker24h = {
  environment: "BINANCE_SPOT";
  symbol: string;
  last_price: string;
  price_change_percent: string;
  quote_volume: string;
  observed_at_us: number;
  read_only: true;
  credential_required: false;
};

export type VenueTicker24hStatus = "idle" | "loading" | "ready" | "error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isVenueTicker24h(value: unknown): value is VenueTicker24h {
  if (!isRecord(value)) return false;
  return value.environment === "BINANCE_SPOT"
    && typeof value.symbol === "string"
    && typeof value.last_price === "string"
    && typeof value.price_change_percent === "string"
    && typeof value.quote_volume === "string"
    && typeof value.observed_at_us === "number"
    && value.read_only === true
    && value.credential_required === false;
}

type MarketTickerPanelProps = {
  ticker: VenueTicker24h | null;
  symbol: string;
  status: VenueTicker24hStatus;
  error: string;
  onRetry: () => void;
};

/**
 * Faz 17 AA.2b: seçili sembolün 24s piyasa özeti (qwen `marketPanel`
 * satır-sütunlarının gerçek karşılığı — yalnız SEÇİLİ sembol için okunur;
 * tüm-liste için N+1 istek YOK). Değerler yalnız gösterilir, türetilmez.
 */
export function MarketTickerPanel({
  ticker,
  symbol,
  status,
  error,
  onRetry,
}: MarketTickerPanelProps) {
  const shown = ticker !== null && ticker.symbol === symbol ? ticker : null;
  return <section className="panel venue-ticker-panel" aria-labelledby="venue-ticker-title">
    <div className="panel-heading">
      <div><p className="eyebrow">24S PİYASA · BINANCE SPOT</p><h2 id="venue-ticker-title">Piyasa özeti</h2></div>
      {status === "ready" && shown !== null ? (
        <span className="state-label ready">Güncel</span>
      ) : status === "loading" ? (
        <span className="state-label pending">Okunuyor</span>
      ) : status === "error" ? (
        <span className="state-label error">Hata</span>
      ) : (
        <span className="state-label">Hazır değil</span>
      )}
    </div>
    {status === "loading" && shown === null && <div className="venue-selector-message" role="status">Piyasa özeti okunuyor…</div>}
    {status === "error" && <div className="venue-selector-message error" role="alert"><strong>Piyasa özeti alınamadı.</strong><p>{error}</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button></div>}
    {status === "idle" && <div className="venue-selector-message" role="status"><p>Piyasa özeti henüz yüklenmedi.</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Özeti yükle</button></div>}
    {shown !== null && (
      <dl className="dataset-facts">
        <div><dt>Sembol</dt><dd>{shown.symbol}</dd></div>
        <div><dt>Son fiyat</dt><dd>{shown.last_price}</dd></div>
        <div><dt>24s değişim (%)</dt><dd>{shown.price_change_percent}</dd></div>
        <div><dt>24s hacim (quote)</dt><dd>{shown.quote_volume}</dd></div>
      </dl>
    )}
    <p className="helper-text">Salt-okunur public veri; credentialsız. Liste-satırları için toplu-ticker yok — yalnız seçili sembol okunur.</p>
  </section>;
}
