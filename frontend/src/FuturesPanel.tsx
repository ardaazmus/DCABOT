import { useState } from "react";

export type FuturesGridView = {
  levels: string[];
  arithmetic_step: string | null;
  level_mode: string;
};

export type FuturesPnlView = {
  effective_quantity: string;
  position_value: string;
  unrealized_pnl: string;
  settlement_asset: string;
};

export type FuturesTrailingView = {
  status: string;
  activation_price: string;
  distance: string;
  stop_price: string | null;
  // The backend only includes the water-mark field for the armed side:
  // high_water for LONG, low_water for SHORT (POST /api/futures/trailing/arm,
  // /observe). Only one of the two is ever present on a given response.
  high_water?: string | null;
  low_water?: string | null;
};

export type FuturesFundingView = {
  amount: string;
  core_expense: string;
  settlement_asset: string;
};

export type FuturesGridPayload = {
  direction: string;
  level_mode: string;
  lower_price: string;
  upper_price: string;
  interval_count: number;
  price_tick: string;
  tick_origin: string;
};

export type FuturesPnlPayload = {
  side: string;
  quantity: string;
  contract_size: string;
  entry_price: string;
  mark_price: string;
  settlement_asset: string;
};

export type FuturesTrailingArmPayload = {
  side: string;
  activation_price: string;
  distance: string;
};

export type FuturesTrailingObservePayload = {
  side: string;
  state: Record<string, unknown>;
  price: string;
};

export type FuturesFundingPayload = {
  position: FuturesPnlPayload;
  funding_rate: string;
  effective_time_us: number;
};

function isStringOrNull(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

export function isFuturesGridView(value: unknown): value is FuturesGridView {
  return (
    typeof value === "object" &&
    value !== null &&
    Array.isArray((value as Record<string, unknown>).levels) &&
    ((value as Record<string, unknown>).levels as unknown[]).every((l) => typeof l === "string") &&
    isStringOrNull((value as Record<string, unknown>).arithmetic_step) &&
    typeof (value as Record<string, unknown>).level_mode === "string"
  );
}

export function isFuturesPnlView(value: unknown): value is FuturesPnlView {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).effective_quantity === "string" &&
    typeof (value as Record<string, unknown>).position_value === "string" &&
    typeof (value as Record<string, unknown>).unrealized_pnl === "string" &&
    typeof (value as Record<string, unknown>).settlement_asset === "string"
  );
}

export function isFuturesTrailingView(value: unknown): value is FuturesTrailingView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  const hasHighWater = body.high_water !== undefined;
  const hasLowWater = body.low_water !== undefined;
  return (
    typeof body.status === "string" &&
    typeof body.activation_price === "string" &&
    typeof body.distance === "string" &&
    isStringOrNull(body.stop_price) &&
    hasHighWater !== hasLowWater &&
    (!hasHighWater || isStringOrNull(body.high_water)) &&
    (!hasLowWater || isStringOrNull(body.low_water))
  );
}

export function isFuturesFundingView(value: unknown): value is FuturesFundingView {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).amount === "string" &&
    typeof (value as Record<string, unknown>).core_expense === "string" &&
    typeof (value as Record<string, unknown>).settlement_asset === "string"
  );
}

export function FuturesPanel({
  grid,
  pnl,
  trailing,
  funding,
  busy,
  error,
  onGrid,
  onPnl,
  onTrailingArm,
  onTrailingObserve,
  onFunding,
}: {
  grid: FuturesGridView | null;
  pnl: FuturesPnlView | null;
  trailing: FuturesTrailingView | null;
  funding: FuturesFundingView | null;
  busy: boolean;
  error: string;
  onGrid: (payload: FuturesGridPayload) => void;
  onPnl: (payload: FuturesPnlPayload) => void;
  onTrailingArm: (payload: FuturesTrailingArmPayload) => void;
  onTrailingObserve: (payload: FuturesTrailingObservePayload) => void;
  onFunding: (payload: FuturesFundingPayload) => void;
}) {
  const [direction, setDirection] = useState("LONG");
  const [levelMode, setLevelMode] = useState("ARITHMETIC");
  const [lowerPrice, setLowerPrice] = useState("100");
  const [upperPrice, setUpperPrice] = useState("200");
  const [intervalCount, setIntervalCount] = useState("2");
  const [priceTick, setPriceTick] = useState("1");
  const [side, setSide] = useState("LONG");
  const [quantity, setQuantity] = useState("2");
  const [contractSize, setContractSize] = useState("0.5");
  const [entryPrice, setEntryPrice] = useState("50000");
  const [markPrice, setMarkPrice] = useState("51000");
  const [activation, setActivation] = useState("100");
  const [distance, setDistance] = useState("5");
  const [observedPrice, setObservedPrice] = useState("110");
  const [fundingRate, setFundingRate] = useState("0.0001");
  const [formError, setFormError] = useState("");

  function submitGrid() {
    const intervals = Number(intervalCount.trim());
    if (!Number.isInteger(intervals) || intervals < 1) {
      setFormError("Aralık sayısı pozitif tam sayı olmalı.");
      return;
    }
    setFormError("");
    onGrid({
      direction,
      level_mode: levelMode,
      lower_price: lowerPrice.trim(),
      upper_price: upperPrice.trim(),
      interval_count: intervals,
      price_tick: priceTick.trim(),
      tick_origin: "0",
    });
  }

  function currentPosition(): FuturesPnlPayload {
    return {
      side,
      quantity: quantity.trim(),
      contract_size: contractSize.trim(),
      entry_price: entryPrice.trim(),
      mark_price: markPrice.trim(),
      settlement_asset: "USDT",
    };
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="futures-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">FUTURES LAB</p>
          <h2 id="futures-title">Futures grid ve PnL projeksiyonları</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {formError && (
        <div className="form-error" role="alert">
          {formError}
        </div>
      )}

      <h3 className="paper-subheading">Grid seviyeleri</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Yön</span>
          <span className="input-wrap">
            <input aria-label="Yön" value={direction} onChange={(event) => setDirection(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Alt fiyat</span>
          <span className="input-wrap">
            <input aria-label="Alt fiyat" value={lowerPrice} onChange={(event) => setLowerPrice(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Üst fiyat</span>
          <span className="input-wrap">
            <input aria-label="Üst fiyat" value={upperPrice} onChange={(event) => setUpperPrice(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Aralık sayısı</span>
          <span className="input-wrap">
            <input aria-label="Aralık sayısı" value={intervalCount} onChange={(event) => setIntervalCount(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitGrid}>
        Seviyeleri üret
      </button>
      {grid && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Seviyeler ({grid.level_mode})</td>
                <td>{grid.levels.join(" · ")}</td>
              </tr>
              {grid.arithmetic_step && (
                <tr>
                  <td>Adım</td>
                  <td>{grid.arithmetic_step}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Pozisyon PnL</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Taraf</span>
          <span className="input-wrap">
            <input aria-label="Taraf" value={side} onChange={(event) => setSide(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Miktar</span>
          <span className="input-wrap">
            <input aria-label="Miktar" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Kontrat boyu</span>
          <span className="input-wrap">
            <input aria-label="Kontrat boyu" value={contractSize} onChange={(event) => setContractSize(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Giriş fiyatı</span>
          <span className="input-wrap">
            <input aria-label="Giriş fiyatı" value={entryPrice} onChange={(event) => setEntryPrice(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Mark fiyatı</span>
          <span className="input-wrap">
            <input aria-label="Mark fiyatı" value={markPrice} onChange={(event) => setMarkPrice(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={() => onPnl(currentPosition())}>
        PnL hesapla
      </button>
      {pnl && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Efektif miktar</td>
                <td>{pnl.effective_quantity}</td>
              </tr>
              <tr>
                <td>Pozisyon değeri</td>
                <td>{pnl.position_value}</td>
              </tr>
              <tr>
                <td>Gerçekleşmemiş PnL</td>
                <td>{pnl.unrealized_pnl}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Trailing tetikleyici</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Aktivasyon</span>
          <span className="input-wrap">
            <input aria-label="Aktivasyon" value={activation} onChange={(event) => setActivation(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Mesafe</span>
          <span className="input-wrap">
            <input aria-label="Mesafe" value={distance} onChange={(event) => setDistance(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Gözlenen fiyat</span>
          <span className="input-wrap">
            <input aria-label="Gözlenen fiyat" value={observedPrice} onChange={(event) => setObservedPrice(event.target.value)} />
          </span>
        </label>
      </div>
      <div className="template-list">
        <button
          className="secondary-button"
          type="button"
          disabled={busy}
          onClick={() => onTrailingArm({ side, activation_price: activation.trim(), distance: distance.trim() })}
        >
          Trailing kur
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={busy || !trailing}
          onClick={() =>
            trailing &&
            onTrailingObserve({ side, state: trailing as unknown as Record<string, unknown>, price: observedPrice.trim() })
          }
        >
          Gözlemi işle
        </button>
      </div>
      {trailing && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Durum</td>
                <td>{trailing.status}</td>
              </tr>
              <tr>
                <td>Stop</td>
                <td>{trailing.stop_price ?? "—"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Funding</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Funding oranı</span>
          <span className="input-wrap">
            <input aria-label="Funding oranı" value={fundingRate} onChange={(event) => setFundingRate(event.target.value)} />
          </span>
        </label>
      </div>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => onFunding({ position: currentPosition(), funding_rate: fundingRate.trim(), effective_time_us: Date.now() * 1000 })}
      >
        Funding hesapla
      </button>
      {funding && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Nakit akışı</td>
                <td>{funding.amount}</td>
              </tr>
              <tr>
                <td>Çekirdek gider</td>
                <td>{funding.core_expense}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      <div className="table-note">
        <span className="note-icon">↳</span> Tüm sonuçlar salt okunur projeksiyondur; likidasyon yetkisi yok, emir yetkisi yok.
      </div>
    </section>
  );
}
