import { useMemo, useState } from "react";

import type { VenuePriceStatus, VenueSymbol, VenueSymbolListStatus } from "./SymbolSelector";

/**
 * Faz AB.1: üst çubuktaki TEK global sembol seçici. SymbolSelector ile aynı
 * veriyi kullanır (liste + son fiyat); fiyat exact-metindir, aynen yazılır.
 * Tanımsız fiyat "" gösterilir, 0 uydurulmaz.
 */
export function GlobalSymbolSelect({
  symbols,
  count,
  status,
  error,
  selectedSymbol,
  lastPrice,
  priceStatus,
  onSelect,
  onRetry,
}: {
  symbols: VenueSymbol[];
  count: number;
  status: VenueSymbolListStatus;
  error: string;
  selectedSymbol: string | null;
  lastPrice: { symbol: string; price: string } | null;
  priceStatus: VenuePriceStatus;
  onSelect: (symbol: string) => void;
  onRetry: () => void;
}) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const needle = query.trim().toUpperCase();
    if (needle === "") return symbols;
    return symbols.filter((entry) => entry.symbol.toUpperCase().includes(needle));
  }, [symbols, query]);
  const price = lastPrice !== null && lastPrice.symbol === selectedSymbol ? lastPrice.price : "";
  return (
    <div className="topbar-symbol" role="group" aria-label="Global sembol">
      <input
        className="symbol-search"
        type="search"
        aria-label="Sembol ara"
        placeholder="Ara"
        value={query}
        disabled={status === "loading"}
        onChange={(event) => setQuery(event.target.value)}
      />
      <select
        aria-label="Global sembol seç"
        value={selectedSymbol ?? ""}
        disabled={status === "loading" || filtered.length === 0}
        onChange={(event) => {
          if (event.target.value !== "") onSelect(event.target.value);
        }}
      >
        {selectedSymbol === null && <option value="">Sembol seç</option>}
        {filtered.map((entry) => (
          <option key={entry.symbol} value={entry.symbol}>
            {entry.symbol}
          </option>
        ))}
      </select>
      <span className="chip" aria-label="Son fiyat" title={priceStatus === "error" ? "Fiyat alınamadı" : undefined}>
        {price}
      </span>
      {status === "error" && (
        <button className="btn" type="button" onClick={onRetry} title={error || undefined}>
          Tekrar dene
        </button>
      )}
      <span className="helper-text" aria-label="Sembol sayısı">
        {status === "ready" ? `${count}` : ""}
      </span>
    </div>
  );
}
