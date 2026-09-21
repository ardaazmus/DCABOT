import { useState } from "react";

export type SignalReadinessView = { signal_id: string; status: string };

export type SignalCandidateView = {
  candidate_id: string;
  signal_id: string;
  side: string;
  qty: string;
  expires_us: number;
};

export type SignalEventPayload = {
  signal_id: string;
  source: string;
  event_time_us: number;
  schema_version: string;
  payload_hash: string;
};

export type SignalAssessPayload = {
  signal: SignalEventPayload;
  closed_bar_time_us: number;
  warmup_bars_observed: number;
  required_warmup_bars: number;
  max_staleness_us: number;
};

export type SignalBindPayload = SignalAssessPayload & {
  action: string;
  symbol: string;
  action_map: [string, string][];
  qty: string;
  ttl_us: number;
};

const DEFAULT_ACTION_MAP: [string, string][] = [
  ["BUY", "BUY"],
  ["SELL", "SELL"],
];

function toInt(text: string): number | null {
  const value = Number(text.trim());
  return Number.isInteger(value) && value >= 0 ? value : null;
}

export function isSignalReadinessView(value: unknown): value is SignalReadinessView {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).signal_id === "string" &&
    typeof (value as Record<string, unknown>).status === "string"
  );
}

export function isSignalCandidateView(value: unknown): value is SignalCandidateView {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).candidate_id === "string" &&
    typeof (value as Record<string, unknown>).signal_id === "string" &&
    typeof (value as Record<string, unknown>).side === "string" &&
    typeof (value as Record<string, unknown>).qty === "string" &&
    typeof (value as Record<string, unknown>).expires_us === "number"
  );
}

export function SignalPanel({
  payloadHash,
  readiness,
  candidate,
  busy,
  error,
  onHash,
  onAssess,
  onBind,
}: {
  payloadHash: string | null;
  readiness: SignalReadinessView | null;
  candidate: SignalCandidateView | null;
  busy: boolean;
  error: string;
  onHash: (payload: Record<string, unknown>) => void;
  onAssess: (payload: SignalAssessPayload) => void;
  onBind: (payload: SignalBindPayload) => void;
}) {
  const [payloadJson, setPayloadJson] = useState('{"action":"BUY","symbol":"BTCUSDT"}');
  const [signalId, setSignalId] = useState("s1");
  const [source, setSource] = useState("offline-fixture");
  const [eventTimeUs, setEventTimeUs] = useState("1700000000000000");
  const [closedBarUs, setClosedBarUs] = useState("1700000000000000");
  const [warmupObserved, setWarmupObserved] = useState("10");
  const [warmupRequired, setWarmupRequired] = useState("5");
  const [stalenessUs, setStalenessUs] = useState("5000000");
  const [action, setAction] = useState("BUY");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [qty, setQty] = useState("0.01");
  const [ttlUs, setTtlUs] = useState("60000000");
  const [formError, setFormError] = useState("");

  function submitHash() {
    let parsed: unknown;
    try {
      parsed = JSON.parse(payloadJson) as unknown;
    } catch {
      setFormError("Yük geçerli JSON değil.");
      return;
    }
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      setFormError("Yük geçerli JSON değil.");
      return;
    }
    setFormError("");
    onHash(parsed as Record<string, unknown>);
  }

  function currentAssess(): SignalAssessPayload | null {
    const eventTime = toInt(eventTimeUs);
    const closedBar = toInt(closedBarUs);
    const observed = toInt(warmupObserved);
    const required = toInt(warmupRequired);
    const staleness = toInt(stalenessUs);
    if (
      eventTime === null ||
      closedBar === null ||
      observed === null ||
      required === null ||
      staleness === null ||
      !payloadHash
    ) {
      setFormError("Önce hash üretin; zaman/sayı alanları tam sayı olmalı.");
      return null;
    }
    return {
      signal: {
        signal_id: signalId.trim(),
        source: source.trim(),
        event_time_us: eventTime,
        schema_version: "signal-v1",
        payload_hash: payloadHash,
      },
      closed_bar_time_us: closedBar,
      warmup_bars_observed: observed,
      required_warmup_bars: required,
      max_staleness_us: staleness,
    };
  }

  function submitAssess() {
    const payload = currentAssess();
    if (!payload) return;
    setFormError("");
    onAssess(payload);
  }

  function submitBind() {
    const base = currentAssess();
    if (!base) return;
    const ttl = toInt(ttlUs);
    if (ttl === null || ttl === 0) {
      setFormError("TTL pozitif tam sayı olmalı.");
      return;
    }
    setFormError("");
    onBind({
      ...base,
      action: action.trim(),
      symbol: symbol.trim(),
      action_map: DEFAULT_ACTION_MAP,
      qty: qty.trim(),
      ttl_us: ttl,
    });
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="signal-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">SIGNAL BOT</p>
          <h2 id="signal-title">Sinyal alımı ve aday bağlama</h2>
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

      <h3 className="paper-subheading">1. Yük hash’i</h3>
      <label className="field">
        <span className="field-label">Yük (JSON)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Yük (JSON)"
          rows={2}
          value={payloadJson}
          onChange={(event) => setPayloadJson(event.target.value)}
        />
      </label>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitHash}>
        Hash üret
      </button>
      {payloadHash && <p className="helper-text">SHA-256: {payloadHash}</p>}

      <h3 className="paper-subheading">2. Sinyal ve readiness</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Signal ID</span>
          <span className="input-wrap">
            <input aria-label="Signal ID" value={signalId} onChange={(event) => setSignalId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Kaynak</span>
          <span className="input-wrap">
            <input aria-label="Kaynak" value={source} onChange={(event) => setSource(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Olay zamanı (µs)</span>
          <span className="input-wrap">
            <input aria-label="Olay zamanı" value={eventTimeUs} onChange={(event) => setEventTimeUs(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Kapalı bar (µs)</span>
          <span className="input-wrap">
            <input aria-label="Kapalı bar" value={closedBarUs} onChange={(event) => setClosedBarUs(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Gözlenen warmup</span>
          <span className="input-wrap">
            <input aria-label="Gözlenen warmup" value={warmupObserved} onChange={(event) => setWarmupObserved(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Gerekli warmup</span>
          <span className="input-wrap">
            <input aria-label="Gerekli warmup" value={warmupRequired} onChange={(event) => setWarmupRequired(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Bayatlık (µs)</span>
          <span className="input-wrap">
            <input aria-label="Bayatlık" value={stalenessUs} onChange={(event) => setStalenessUs(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy || !payloadHash} onClick={submitAssess}>
        Readiness ölç
      </button>
      {readiness && (
        <p className="helper-text">
          {readiness.signal_id}: <strong>{readiness.status}</strong>
        </p>
      )}

      <h3 className="paper-subheading">3. Aday bağlama</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Aksiyon</span>
          <span className="input-wrap">
            <input aria-label="Aksiyon" value={action} onChange={(event) => setAction(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Sembol</span>
          <span className="input-wrap">
            <input aria-label="Sembol" value={symbol} onChange={(event) => setSymbol(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Miktar</span>
          <span className="input-wrap">
            <input aria-label="Miktar" value={qty} onChange={(event) => setQty(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">TTL (µs)</span>
          <span className="input-wrap">
            <input aria-label="TTL" value={ttlUs} onChange={(event) => setTtlUs(event.target.value)} />
          </span>
        </label>
      </div>
      <p className="helper-text">Yön eşlemesi sabit: BUY→BUY, SELL→SELL.</p>
      <button className="primary-button" type="button" disabled={busy || !payloadHash} onClick={submitBind}>
        Aday bağla
      </button>
      {candidate && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Aday ID</td>
                <td>{candidate.candidate_id}</td>
              </tr>
              <tr>
                <td>Yön/miktar</td>
                <td>
                  {candidate.side} / {candidate.qty}
                </td>
              </tr>
              <tr>
                <td>Bitiş (µs)</td>
                <td>{candidate.expires_us}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      <div className="table-note">
        <span className="note-icon">↳</span> Adaylar salt okunur niyet kayıtlarıdır; emir yetkisi yok.
      </div>
    </section>
  );
}
