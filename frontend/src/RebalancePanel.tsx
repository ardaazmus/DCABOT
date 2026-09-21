export type RebalancePosition = {
  asset: string;
  qty: string;
  price: string;
  value: string;
};

export type RebalanceValuation = {
  valuation_asset: string;
  total_equity: string;
  positions: RebalancePosition[];
};

export type RebalanceStatus = "idle" | "pending" | "ready" | "error";

function isPosition(value: unknown): value is RebalancePosition {
  if (typeof value !== "object" || value === null) return false;
  const row = value as Record<string, unknown>;
  return (
    typeof row.asset === "string" &&
    typeof row.qty === "string" &&
    typeof row.price === "string" &&
    typeof row.value === "string"
  );
}

export function isRebalanceValuation(value: unknown): value is RebalanceValuation {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.valuation_asset === "string" &&
    typeof body.total_equity === "string" &&
    Array.isArray(body.positions) &&
    body.positions.every(isPosition)
  );
}

export type PairLine = [string, string];

export function parsePairLines(text: string): { rows: PairLine[]; error: string } {
  const rows: PairLine[] = [];
  const lines = text.split("\n");
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) continue;
    const parts = line.split(/\s+/);
    if (parts.length !== 2) {
      return { rows: [], error: `Satır ${index + 1}: "ASSET DEĞER" biçiminde olmalı.` };
    }
    rows.push([parts[0], parts[1]]);
  }
  return { rows, error: "" };
}

export function RebalancePanel({
  valuation,
  status,
  error,
  holdingsText,
  pricesText,
  onHoldingsChange,
  onPricesChange,
  onCalculate,
}: {
  valuation: RebalanceValuation | null;
  status: RebalanceStatus;
  error: string;
  holdingsText: string;
  pricesText: string;
  onHoldingsChange: (value: string) => void;
  onPricesChange: (value: string) => void;
  onCalculate: () => void;
}) {
  return (
    <section className="panel rebalance-panel" aria-labelledby="rebalance-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">REBALANCE</p>
          <h2 id="rebalance-title">Rebalancing değerlemesi</h2>
        </div>
        <span className={`state-label ${status}`}>
          {status === "pending" ? "Hesaplanıyor" : status === "error" ? "Hata" : status === "ready" ? "Güncel" : "Hazır"}
        </span>
      </div>
      <label className="field">
        <span className="field-label">Varlıklar (satır başına: ASSET MİKTAR)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Varlıklar"
          rows={3}
          value={holdingsText}
          onChange={(event) => onHoldingsChange(event.target.value)}
        />
      </label>
      <label className="field">
        <span className="field-label">Fiyatlar, USDT karşılığı (satır başına: ASSET FİYAT)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Fiyatlar"
          rows={3}
          value={pricesText}
          onChange={(event) => onPricesChange(event.target.value)}
        />
      </label>
      <button className="primary-button" type="button" disabled={status === "pending"} onClick={onCalculate}>
        {status === "pending" ? "Hesaplanıyor…" : "Değerlemeyi hesapla"}
      </button>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {valuation && status === "ready" && (
        <>
          <div className="table-wrap rebalance-result">
            <table>
              <thead>
                <tr>
                  <th>Varlık</th>
                  <th>Miktar</th>
                  <th>Fiyat (USDT)</th>
                  <th>Değer (USDT)</th>
                </tr>
              </thead>
              <tbody>
                {valuation.positions.map((row) => (
                  <tr key={row.asset}>
                    <td>{row.asset}</td>
                    <td>{row.qty}</td>
                    <td>{row.price}</td>
                    <td>{row.value}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td>TOPLAM</td>
                  <td>—</td>
                  <td>—</td>
                  <td>{valuation.total_equity}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <div className="table-note">
            <span className="note-icon">↳</span> Bu ekran salt okunur projeksiyondur; emir, rezerv veya dolum yetkisi yoktur.
          </div>
        </>
      )}
    </section>
  );
}
