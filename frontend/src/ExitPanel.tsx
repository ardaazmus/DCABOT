import { useState } from "react";

export type TrailingBindView = {
  trigger_price: string;
  requested_qty: string;
  remaining_capacity: string;
  order_authority: string;
};

export type PercentStateView = {
  status: string;
  activation_price: string;
  rate: string;
  high_water?: string | null;
  low_water?: string | null;
  stop_price: string | null;
};

export type BreakevenView = {
  status: string;
  gross_breakeven_price: string;
  fee_aware_breakeven_price: string | null;
  reason: string;
  profile_revision: string | null;
  order_authority: string;
};

export type TrailingBindPayload = {
  side: string;
  kind: string;
  state: Record<string, unknown>;
  open_qty: string;
  accepted_exit_fills: string[];
  committed_exit_qty: string[];
  requested_qty: string;
};

function isStringOrNull(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

export function isTrailingBindView(value: unknown): value is TrailingBindView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.trigger_price === "string" &&
    typeof body.requested_qty === "string" &&
    typeof body.remaining_capacity === "string" &&
    typeof body.order_authority === "string"
  );
}

export function isPercentStateView(value: unknown): value is PercentStateView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.status === "string" &&
    typeof body.activation_price === "string" &&
    typeof body.rate === "string" &&
    isStringOrNull(body.stop_price)
  );
}

export function isBreakevenView(value: unknown): value is BreakevenView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.status === "string" &&
    typeof body.gross_breakeven_price === "string" &&
    isStringOrNull(body.fee_aware_breakeven_price) &&
    typeof body.reason === "string" &&
    isStringOrNull(body.profile_revision) &&
    typeof body.order_authority === "string"
  );
}

export function ExitPanel({
  binding,
  percent,
  breakeven,
  busy,
  error,
  onBind,
  onPercentArm,
  onPercentObserve,
  onBreakeven,
}: {
  binding: TrailingBindView | null;
  percent: PercentStateView | null;
  breakeven: BreakevenView | null;
  busy: boolean;
  error: string;
  onBind: (payload: TrailingBindPayload) => void;
  onPercentArm: (payload: { side: string; activation_price: string; rate: string }) => void;
  onPercentObserve: (payload: { side: string; state: Record<string, unknown>; price: string }) => void;
  onBreakeven: () => void;
}) {
  const [side, setSide] = useState("LONG");
  const [stopPrice, setStopPrice] = useState("105");
  const [highWater, setHighWater] = useState("110");
  const [openQty, setOpenQty] = useState("2");
  const [requestedQty, setRequestedQty] = useState("1");
  const [activation, setActivation] = useState("100");
  const [rate, setRate] = useState("0.05");
  const [observedPrice, setObservedPrice] = useState("110");
  const [formError, setFormError] = useState("");

  function submitBind() {
    if (!stopPrice.trim() || !openQty.trim() || !requestedQty.trim()) {
      setFormError("Stop fiyatı ve miktarlar boş olamaz.");
      return;
    }
    setFormError("");
    onBind({
      side,
      kind: "FIXED",
      state: {
        status: "TRIGGERED",
        activation_price: activation.trim(),
        distance: "5",
        high_water: side === "LONG" ? highWater.trim() : null,
        low_water: side === "SHORT" ? highWater.trim() : null,
        stop_price: stopPrice.trim(),
      },
      open_qty: openQty.trim(),
      accepted_exit_fills: [],
      committed_exit_qty: [],
      requested_qty: requestedQty.trim(),
    });
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="exits-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">EXIT DESK</p>
          <h2 id="exits-title">Trailing çıkış ve breakeven projeksiyonları</h2>
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

      <h3 className="paper-subheading">Trailing çıkış adayı</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Yön</span>
          <span className="input-wrap">
            <input aria-label="Yön" value={side} onChange={(e) => setSide(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Stop fiyatı</span>
          <span className="input-wrap">
            <input aria-label="Stop fiyatı" value={stopPrice} onChange={(e) => setStopPrice(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Açık miktar</span>
          <span className="input-wrap">
            <input aria-label="Açık miktar" value={openQty} onChange={(e) => setOpenQty(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">İstenen çıkış</span>
          <span className="input-wrap">
            <input aria-label="İstenen çıkış" value={requestedQty} onChange={(e) => setRequestedQty(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitBind}>
        Çıkış adayı üret
      </button>
      {binding && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Tetik fiyatı</td>
                <td>{binding.trigger_price}</td>
              </tr>
              <tr>
                <td>Kalan kapasite</td>
                <td>{binding.remaining_capacity}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Yüzde trailing</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Aktivasyon</span>
          <span className="input-wrap">
            <input aria-label="Aktivasyon" value={activation} onChange={(e) => setActivation(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Oran</span>
          <span className="input-wrap">
            <input aria-label="Oran" value={rate} onChange={(e) => setRate(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Gözlenen fiyat</span>
          <span className="input-wrap">
            <input aria-label="Gözlenen fiyat" value={observedPrice} onChange={(e) => setObservedPrice(e.target.value)} />
          </span>
        </label>
      </div>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => {
          setFormError("");
          onPercentArm({ side, activation_price: activation.trim(), rate: rate.trim() });
        }}
      >
        Yüzde trailing kur
      </button>
      <button
        className="secondary-button"
        type="button"
        disabled={busy || percent === null}
        onClick={() => {
          if (percent === null) return;
          setFormError("");
          onPercentObserve({ side, state: percent as unknown as Record<string, unknown>, price: observedPrice.trim() });
        }}
      >
        Yüzde gözlemi işle
      </button>
      {percent && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Durum</td>
                <td>{percent.status}</td>
              </tr>
              <tr>
                <td>Stop</td>
                <td>{percent.stop_price ?? "—"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Breakeven (örnek plan)</h3>
      <button className="secondary-button" type="button" disabled={busy} onClick={onBreakeven}>
        Breakeven hesapla
      </button>
      {breakeven && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Brüt breakeven</td>
                <td>{breakeven.gross_breakeven_price}</td>
              </tr>
              <tr>
                <td>Fee-aware</td>
                <td>{breakeven.fee_aware_breakeven_price ?? breakeven.reason}</td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Emir yetkisi yok (NONE); OCO/cancel-replace ve gerçek execution kapsam dışı.
          </p>
        </div>
      )}
    </section>
  );
}
