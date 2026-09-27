import { useEffect, useMemo, useRef, useState } from "react";

export type VenueSymbol = {
  symbol: string;
  status: string;
  base_asset: string;
  quote_asset: string;
};

export type VenueSymbolList = {
  environment: "BINANCE_SPOT";
  symbols: VenueSymbol[];
  count: number;
  observed_at_us: number;
  read_only: true;
  credential_required: false;
};

export type VenueLastPrice = {
  environment: "BINANCE_SPOT";
  symbol: string;
  price: string;
  event_id: string;
  event_time_us: number;
  read_only: true;
  credential_required: false;
};

export type VenueSymbolListStatus = "idle" | "loading" | "ready" | "error";
export type VenuePriceStatus = "idle" | "loading" | "ready" | "error";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isVenueSymbol(value: unknown): value is VenueSymbol {
  if (!isRecord(value)) return false;
  return typeof value.symbol === "string"
    && typeof value.status === "string"
    && typeof value.base_asset === "string"
    && typeof value.quote_asset === "string";
}

export function isVenueSymbolList(value: unknown): value is VenueSymbolList {
  if (!isRecord(value)) return false;
  return value.environment === "BINANCE_SPOT"
    && Array.isArray(value.symbols)
    && value.symbols.every(isVenueSymbol)
    && typeof value.count === "number"
    && typeof value.observed_at_us === "number"
    && value.read_only === true
    && value.credential_required === false;
}

export function isVenueLastPrice(value: unknown): value is VenueLastPrice {
  if (!isRecord(value)) return false;
  return value.environment === "BINANCE_SPOT"
    && typeof value.symbol === "string"
    && typeof value.price === "string"
    && typeof value.event_id === "string"
    && typeof value.event_time_us === "number"
    && value.read_only === true
    && value.credential_required === false;
}

type SymbolSelectorProps = {
  symbols: VenueSymbol[];
  count: number;
  status: VenueSymbolListStatus;
  error: string;
  selectedSymbol: string | null;
  lastPrice: { symbol: string; price: string } | null;
  priceStatus: VenuePriceStatus;
  onSelect: (symbol: string) => void;
  onRetry: () => void;
};

/**
 * Faz 17 A.1: aranabilir borsa sembol seçici (qwen `marketPanel`/`mktSearch`
 * deseninin gerçek karşılığı). Liste ve fiyat yalnız public, credential-free
 * backend uçlarından gelir; bu bileşen hiçbir değer üretmez, yalnız gösterir.
 */
export function SymbolSelector({
  symbols,
  count,
  status,
  error,
  selectedSymbol,
  lastPrice,
  priceStatus,
  onSelect,
  onRetry,
}: SymbolSelectorProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (wrapRef.current && !wrapRef.current.contains(event.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open ]);

  const filtered = useMemo(() => {
    const needle = query.trim().toUpperCase();
    if (needle === "") return symbols;
    return symbols.filter((entry) => entry.symbol.toUpperCase().includes(needle));
  }, [symbols, query]);

  function close() {
    setOpen(false);
    setQuery("");
  }

  function choose(symbol: string) {
    onSelect(symbol);
    close();
  }

  const priceShown = lastPrice !== null && lastPrice.symbol === selectedSymbol ? lastPrice.price : null;

  return <section className="panel venue-selector-panel" aria-labelledby="venue-selector-title">
    <div className="panel-heading">
      <div><p className="eyebrow">CANLI PİYASA · BINANCE SPOT</p><h2 id="venue-selector-title">Sembol seçici</h2></div>
      {status === "ready" ? (
        <span className="state-label ready">Güncel</span>
      ) : status === "loading" ? (
        <span className="state-label pending">Okunuyor</span>
      ) : status === "error" ? (
        <span className="state-label error">Hata</span>
      ) : (
        <span className="state-label">Hazır değil</span>
      )}
    </div>
    <p className="venue-selector-intro">Borsanın public listesinden bir çift seçin. Seçim, anlık fiyatı ve venue snapshot kartını günceller; tarihsel dataset grafiği değişmez.</p>
    {status === "loading" && symbols.length === 0 && <div className="venue-selector-message" role="status">Sembol listesi okunuyor…</div>}
    {status === "error" && <div className="venue-selector-message error" role="alert"><strong>Sembol listesi alınamadı.</strong><p>{error}</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Tekrar dene</button></div>}
    {status === "idle" && <div className="venue-selector-message" role="status"><p>Sembol listesi henüz yüklenmedi.</p><button className="catalog-secondary-button" type="button" onClick={onRetry}>Listeyi yükle</button></div>}
    {(status === "ready" || symbols.length > 0) && <>
      <div className="venue-selector-wrap" ref={wrapRef}>
        <button
          className="venue-selector-button"
          type="button"
          aria-expanded={open}
          aria-haspopup="listbox"
          onClick={() => (open ? close() : setOpen(true))}
        >
          <span className="venue-selector-symbol">{selectedSymbol ?? "Sembol seç"}</span>
          {priceStatus === "loading" ? (
            <span className="venue-selector-price pending">fiyat okunuyor…</span>
          ) : priceShown !== null ? (
            <span className="venue-selector-price">{priceShown}</span>
          ) : null}
          <span className="venue-selector-caret" aria-hidden="true">▾</span>
        </button>
        {open && <div className="venue-selector-panel-drop">
          <label className="venue-selector-search-label" htmlFor="venue-symbol-search">Sembol ara</label>
          <input
            id="venue-symbol-search"
            className="venue-selector-search"
            type="text"
            autoComplete="off"
            spellCheck={false}
            placeholder="örn. BTCUSDT, ETH"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && filtered.length > 0) choose(filtered[0].symbol);
              else if (event.key === "Escape") close();
            }}
          />
          {filtered.length === 0 ? (
            <p className="venue-selector-empty" role="status">Sonuç yok.</p>
          ) : (
            <ul className="venue-selector-list" role="listbox" aria-label="Borsa sembolleri">
              {filtered.map((entry) => (
                <li key={entry.symbol}>
                  <button
                    className="venue-selector-row"
                    type="button"
                    role="option"
                    aria-selected={entry.symbol === selectedSymbol}
                    onClick={() => choose(entry.symbol)}
                  >
                    <span className="venue-selector-row-symbol">{entry.symbol}</span>
                    <span className="venue-selector-row-pair">{entry.base_asset} / {entry.quote_asset}</span>
                    <span className={`state-label${entry.status === "TRADING" ? " ready" : ""}`}>{entry.status}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <p className="venue-selector-count" role="status">
            {query.trim() === "" ? `${count} çift listelendi` : `${filtered.length} sonuç / ${count} çift`} · Binance spot
          </p>
        </div>}
      </div>
      {selectedSymbol !== null && priceStatus === "error" && (
        <p className="helper-text" role="status">Seçili sembol için canlı fiyat alınamadı; liste ve snapshot yine de güncel.</p>
      )}
    </>}
  </section>;
}
