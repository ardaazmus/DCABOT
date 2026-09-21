import { useState } from "react";

export type TwoLegIdentityView = {
  account_id: string;
  venue_profile: string;
  product_id: string;
  symbol: string;
  position_mode: string;
  hedge_side: string | null;
};

export type TwoLegFillView = {
  fill_id: string;
  leg_id: string;
  quantity: string;
  fill_status: string;
  event_time_us: number;
};

export type TwoLegProjectionView = {
  state: string;
  leg_a_identity: TwoLegIdentityView | null;
  leg_b_identity: TwoLegIdentityView | null;
  leg_a_quantity: string;
  leg_b_quantity: string;
  leg_a_status: string;
  leg_b_status: string;
  fills: TwoLegFillView[];
};

export type TwoLegFillPayload = {
  fill_id: string;
  leg_id: string;
  account_id: string;
  venue_profile: string;
  product_id: string;
  symbol: string;
  hedge_side: string;
  quantity: string;
  fill_status: string;
  event_time_us: number;
};

function isIdentityOrNull(value: unknown): value is TwoLegIdentityView | null {
  if (value === null) return true;
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.account_id === "string" &&
    typeof body.venue_profile === "string" &&
    typeof body.product_id === "string" &&
    typeof body.symbol === "string" &&
    typeof body.position_mode === "string" &&
    (body.hedge_side === null || typeof body.hedge_side === "string")
  );
}

function isFillView(value: unknown): value is TwoLegFillView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.fill_id === "string" &&
    typeof body.leg_id === "string" &&
    typeof body.quantity === "string" &&
    typeof body.fill_status === "string" &&
    typeof body.event_time_us === "number"
  );
}

export function isTwoLegProjectionView(value: unknown): value is TwoLegProjectionView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.state === "string" &&
    isIdentityOrNull(body.leg_a_identity) &&
    isIdentityOrNull(body.leg_b_identity) &&
    typeof body.leg_a_quantity === "string" &&
    typeof body.leg_b_quantity === "string" &&
    typeof body.leg_a_status === "string" &&
    typeof body.leg_b_status === "string" &&
    Array.isArray(body.fills) &&
    (body.fills as unknown[]).every(isFillView)
  );
}

export function TwoLegPanel({
  sessionId,
  projection,
  busy,
  error,
  onStart,
  onFill,
  onRecovery,
  onTimeout,
  onReplay,
}: {
  sessionId: string;
  projection: TwoLegProjectionView | null;
  busy: boolean;
  error: string;
  onStart: (sessionId: string) => void;
  onFill: (payload: TwoLegFillPayload) => void;
  onRecovery: () => void;
  onTimeout: () => void;
  onReplay: () => void;
}) {
  const [session, setSession] = useState(sessionId);
  const [fillId, setFillId] = useState("f-a1");
  const [legId, setLegId] = useState("A");
  const [hedgeSide, setHedgeSide] = useState("LONG");
  const [quantity, setQuantity] = useState("0.5");
  const [fillStatus, setFillStatus] = useState("FULL");
  const [eventTime, setEventTime] = useState("1000");
  const [formError, setFormError] = useState("");

  function submitStart() {
    if (!session.trim()) {
      setFormError("Session kimliği boş olamaz.");
      return;
    }
    setFormError("");
    onStart(session.trim());
  }

  function submitFill() {
    const eventTimeUs = Number(eventTime.trim());
    if (!Number.isInteger(eventTimeUs) || eventTimeUs < 0) {
      setFormError("Event time negatif olmayan tam sayı olmalı.");
      return;
    }
    if (!fillId.trim() || !quantity.trim()) {
      setFormError("Fill kimliği ve miktar boş olamaz.");
      return;
    }
    setFormError("");
    onFill({
      fill_id: fillId.trim(),
      leg_id: legId,
      account_id: "acct-1",
      venue_profile: "BINANCE-SPOT",
      product_id: "BTCUSDT",
      symbol: "BTCUSDT",
      hedge_side: hedgeSide,
      quantity: quantity.trim(),
      fill_status: fillStatus,
      event_time_us: eventTimeUs,
    });
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="twoleg-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">HEDGE LAB</p>
          <h2 id="twoleg-title">Two-leg session ve replay</h2>
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

      <h3 className="paper-subheading">Session</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Session kimliği</span>
          <span className="input-wrap">
            <input aria-label="Session kimliği" value={session} onChange={(event) => setSession(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitStart}>
        Session başlat
      </button>
      <button className="secondary-button" type="button" disabled={busy} onClick={onReplay}>
        Replay
      </button>

      <h3 className="paper-subheading">Accepted fill</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Fill kimliği</span>
          <span className="input-wrap">
            <input aria-label="Fill kimliği" value={fillId} onChange={(event) => setFillId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Bacak</span>
          <span className="input-wrap">
            <input aria-label="Bacak" value={legId} onChange={(event) => setLegId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Hedge yönü</span>
          <span className="input-wrap">
            <input aria-label="Hedge yönü" value={hedgeSide} onChange={(event) => setHedgeSide(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Miktar</span>
          <span className="input-wrap">
            <input aria-label="Miktar" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Fill durumu</span>
          <span className="input-wrap">
            <input aria-label="Fill durumu" value={fillStatus} onChange={(event) => setFillStatus(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Event time (µs)</span>
          <span className="input-wrap">
            <input aria-label="Event time (µs)" value={eventTime} onChange={(event) => setEventTime(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitFill}>
        Fill kabul et
      </button>

      <h3 className="paper-subheading">Terminal işaretleri</h3>
      <button className="secondary-button" type="button" disabled={busy} onClick={onRecovery}>
        Recovery işaretle
      </button>
      <button className="secondary-button" type="button" disabled={busy} onClick={onTimeout}>
        Timeout işaretle
      </button>

      {projection && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Durum</td>
                <td>{projection.state}</td>
              </tr>
              <tr>
                <td>Bacak A</td>
                <td>
                  {projection.leg_a_status} · {projection.leg_a_quantity}
                </td>
              </tr>
              <tr>
                <td>Bacak B</td>
                <td>
                  {projection.leg_b_status} · {projection.leg_b_quantity}
                </td>
              </tr>
              <tr>
                <td>Fill sayısı</td>
                <td>{projection.fills.length}</td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Yalnız gözlenen fill&apos;ler kaydedilir; sentetik bacak üretilmez, timeout saatten tahmin edilmez.
          </p>
        </div>
      )}
    </section>
  );
}
