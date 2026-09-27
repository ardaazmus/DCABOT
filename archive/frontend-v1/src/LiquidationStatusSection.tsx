// D.2 (=8.3): bot detayındaki venue pozisyon-riski bölümü. Dört gereksinim
// birebir: (1) canlı venue değeri, (2) değişkenlik notu, (3) hızlı-hareket
// uyarısı, (4) veri yoksa dürüst boş. Hesap yok, yalnız gösterim.

export type LiquidationStateView =
  | "NO_POSITION"
  | "DATA_OK"
  | "WATCH"
  | "STALE"
  | "INCONSISTENT"
  | "SIMULATED_ONLY";

export type LiquidationStatusView = {
  state: LiquidationStateView;
  liquidation_price: string | null;
  margin_ratio: string | null;
  is_fast_move: boolean;
  reason: string | null;
};

const STATES: readonly string[] = [
  "NO_POSITION",
  "DATA_OK",
  "WATCH",
  "STALE",
  "INCONSISTENT",
  "SIMULATED_ONLY",
];

export function isLiquidationStatusView(value: unknown): value is LiquidationStatusView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.state === "string" &&
    (STATES as readonly string[]).includes(body.state) &&
    (typeof body.liquidation_price === "string" || body.liquidation_price === null) &&
    (typeof body.margin_ratio === "string" || body.margin_ratio === null) &&
    typeof body.is_fast_move === "boolean" &&
    (typeof body.reason === "string" || body.reason === null)
  );
}

const STATE_LABEL: Record<LiquidationStateView, string> = {
  NO_POSITION: "○ Pozisyon yok",
  DATA_OK: "✓ Güncel",
  WATCH: "● İzleniyor",
  STALE: "… Eski veri",
  INCONSISTENT: "! Tutarsız",
  SIMULATED_ONLY: "○ Veri yok",
};

export function LiquidationStatusSection({
  symbol,
  pairCount,
  status,
  busy,
  error,
  onRefresh,
}: {
  symbol: string | null;
  pairCount: number;
  status: LiquidationStatusView | null;
  busy: boolean;
  error: string;
  onRefresh: () => void;
}) {
  const showValues =
    status !== null &&
    (status.state === "DATA_OK" ||
      status.state === "WATCH" ||
      status.state === "STALE" ||
      status.state === "INCONSISTENT");
  return (
    <section className="panel" aria-labelledby="liq-status-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">POZİSYON RİSKİ · VENUE</p>
          <h2 id="liq-status-title">Likidasyon durumu{symbol ? ` · ${symbol}` : ""}</h2>
        </div>
      </div>
      {symbol === null && <p className="helper-text">Pair yok — sorgulanamadı.</p>}
      {symbol !== null && pairCount > 1 && (
        <p className="helper-text">Botun ilk pair&apos;i sorgulanıyor.</p>
      )}
      {symbol !== null && busy && (
        <p className="helper-text" role="status">
          Okunuyor…
        </p>
      )}
      {symbol !== null && !busy && error !== "" && (
        <>
          <div className="form-error" role="alert">
            {error}
          </div>
          <button className="secondary-button" type="button" onClick={onRefresh}>
            Yenile
          </button>
        </>
      )}
      {symbol !== null && !busy && error === "" && status === null && (
        <>
          <p className="helper-text">Durum henüz okunmadı.</p>
          <button className="secondary-button" type="button" onClick={onRefresh}>
            Yenile
          </button>
        </>
      )}
      {symbol !== null && status !== null && status.state === "SIMULATED_ONLY" && (
        <>
          <p className="helper-text">Veri yok — venue pozisyon verisi bağlı değil.</p>
          {status.reason && (
            <p className="helper-text">
              <code>{status.reason}</code>
            </p>
          )}
          <button className="secondary-button" type="button" onClick={onRefresh}>
            Yenile
          </button>
        </>
      )}
      {symbol !== null && status !== null && status.state === "NO_POSITION" && (
        <>
          <p className="helper-text">Açık pozisyon yok (venue bildirimi).</p>
          <button className="secondary-button" type="button" onClick={onRefresh}>
            Yenile
          </button>
        </>
      )}
      {symbol !== null && showValues && status !== null && (
        <>
          <dl className="dataset-facts">
            <div>
              <dt>Durum</dt>
              <dd>{STATE_LABEL[status.state]}</dd>
            </div>
            <div>
              <dt>Likidasyon fiyatı (venue)</dt>
              <dd>
                {status.liquidation_price ??
                  (status.reason === "LIQUIDATION_PRICE_NOT_MEANINGFUL"
                    ? "anlamsız (venue 0 bildirdi)"
                    : "—")}
              </dd>
            </div>
            <div>
              <dt>Marjin oranı (türetilmiş)</dt>
              <dd>{status.margin_ratio ?? "—"}</dd>
            </div>
          </dl>
          {status.state === "STALE" && (
            <p className="helper-text">Son bilinen değerler gösteriliyor (eski veri).</p>
          )}
          {status.state === "INCONSISTENT" && status.reason && (
            <p className="helper-text">
              Tutarsız okuma: <code>{status.reason}</code>
            </p>
          )}
          {status.is_fast_move && (
            <p className="liq-fastmove" role="alert">
              Hızlı hareket: bu veri daha az güvenilir olabilir.
            </p>
          )}
          <p className="helper-text">Bu değer borsanın anlık raporudur, sabit değildir.</p>
          <button className="secondary-button" type="button" onClick={onRefresh}>
            Yenile
          </button>
        </>
      )}
    </section>
  );
}
