import { useState } from "react";

/* Faz 17 AA.14: gerçek order-book (qwen'in SAHTE derinliğinin yerine —
 * `GET /api/public/depth`, credentialsız public veri). Fiyat/miktar
 * exact-metin aynen dizilir; toplam/derinlik hesabı YOK. Limit yalnız
 * sunucunun kabul ettiği 8 değerden seçilir (verbatim). */

export type DepthLevel = [string, string];

export type DepthBook = {
  symbol: string;
  last_update_id: number;
  bids: DepthLevel[];
  asks: DepthLevel[];
  observed_at_us: number;
  read_only: boolean;
  credential_required: boolean;
};

export const DEPTH_LIMITS = [5, 10, 20, 50, 100, 500, 1000, 5000] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isLevel(value: unknown): value is DepthLevel {
  return Array.isArray(value) && value.length === 2
    && typeof value[0] === "string" && typeof value[1] === "string";
}

export function isDepthBookResponse(value: unknown): value is { data: DepthBook } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.symbol === "string"
    && typeof data.last_update_id === "number"
    && Array.isArray(data.bids) && data.bids.every(isLevel)
    && Array.isArray(data.asks) && data.asks.every(isLevel)
    && typeof data.observed_at_us === "number"
    && typeof data.read_only === "boolean"
    && typeof data.credential_required === "boolean";
}

const SYMBOL = /^[A-Z0-9]+$/;

function renderLevels(caption: string, levels: DepthLevel[]) {
  return (
    <div className="table-wrap">
      <table>
        <caption>{caption} ({levels.length} seviye)</caption>
        <thead><tr><th>Fiyat</th><th>Miktar</th></tr></thead>
        <tbody>{levels.map(([price, qty], index) => <tr key={`${price}-${index}`}><td>{price}</td><td>{qty}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

type DepthPanelProps = {
  book: DepthBook | null;
  initialSymbol: string;
  busy: boolean;
  error: string;
  onLoad: (symbol: string, limit: number) => void;
};

export function DepthPanel({ book, initialSymbol, busy, error, onLoad }: DepthPanelProps) {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [limit, setLimit] = useState("20");
  const [formError, setFormError] = useState("");

  function submit() {
    const trimmed = symbol.trim();
    if (!SYMBOL.test(trimmed)) {
      setFormError("Sembol büyük-harf alfanumerik olmalıdır.");
      return;
    }
    const numeric = Number(limit);
    if (!DEPTH_LIMITS.includes(numeric as (typeof DEPTH_LIMITS)[number])) {
      setFormError("Limit yalnız listeden seçilir.");
      return;
    }
    setFormError("");
    onLoad(trimmed, numeric);
  }

  return <section className="panel depth-panel" aria-labelledby="depth-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">PİYASA · DERİNLİK</p>
        <h2 id="depth-title">Order-book (gerçek)</h2>
      </div>
      <span className="revision">{book === null ? (busy ? "okunuyor" : "yüklenmedi") : book.symbol}</span>
    </div>
    <label className="field">
      <span className="field-label">Sembol</span>
      <span className="input-wrap">
        <input aria-label="Sembol" value={symbol} onChange={(event) => setSymbol(event.target.value)} />
      </span>
    </label>
    <label className="field">
      <span className="field-label">Seviye limiti</span>
      <span className="input-wrap">
        <select aria-label="Seviye limiti" value={limit} onChange={(event) => setLimit(event.target.value)}>
          {DEPTH_LIMITS.map((value) => <option key={value} value={String(value)}>{value}</option>)}
        </select>
      </span>
    </label>
    {formError && <div className="form-error" role="alert">{formError}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary-button" type="button" disabled={busy} onClick={submit}>
      {busy ? "Okunuyor…" : "Derinliği getir"}
    </button>
    {book !== null && (
      <>
        <dl className="preflight-facts">
          <div><dt>Son güncelleme</dt><dd>{book.last_update_id}</dd></div>
          <div><dt>Gözlem</dt><dd>{new Date(book.observed_at_us / 1000).toLocaleString("tr-TR")}</dd></div>
          <div><dt>Erişim</dt><dd>{book.read_only && !book.credential_required ? "salt-okunur · credentialsız" : "kısıtlı"}</dd></div>
        </dl>
        {renderLevels("Satış (asks)", book.asks)}
        {renderLevels("Alış (bids)", book.bids)}
      </>
    )}
    <p className="paper-note">Binance public derinlik anlık-görüntüsü; emir-verme bu ekranda YOK. Seviyeler venue-metni aynen.</p>
  </section>;
}
