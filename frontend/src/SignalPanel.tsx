import { useState } from "react";
import { AdvancedDetails } from "./forms";
import { useI18n } from "./i18n";

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

export type WebhookIntakeView = {
  signal_id: string;
  symbol: string;
  action: string;
  event_time_us: number;
  status: string;
};

const DEFAULT_ACTION_MAP: [string, string][] = [
  ["BUY", "BUY"],
  ["SELL", "SELL"],
];

export const SIGNAL_WEBHOOK_PATH = "/api/signals/webhook/tradingview";

const WEBHOOK_PATH = SIGNAL_WEBHOOK_PATH;

const ALERT_TEMPLATE = `{
  "secret": "…",
  "symbol": "{{ticker}}",
  "action": "{{strategy.order.comment}}",
  "event_time_us": "{{time}}",
  "price": "{{close}}",
  "strategy_order_id": "{{strategy.order.id}}"
}`;

function toInt(text: string): number | null {
  const value = Number(text.trim());
  return Number.isInteger(value) && value >= 0 ? value : null;
}

const EXACT_DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;

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

export function isWebhookIntakeList(value: unknown): value is WebhookIntakeView[] {
  return (
    Array.isArray(value) &&
    value.every(
      (row: unknown) =>
        typeof row === "object" &&
        row !== null &&
        typeof (row as Record<string, unknown>).signal_id === "string" &&
        typeof (row as Record<string, unknown>).symbol === "string" &&
        typeof (row as Record<string, unknown>).action === "string" &&
        typeof (row as Record<string, unknown>).event_time_us === "number" &&
        typeof (row as Record<string, unknown>).status === "string",
    )
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
  const { t } = useI18n();
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

  const [configured, setConfigured] = useState<boolean | null>(null);
  const [intakes, setIntakes] = useState<WebhookIntakeView[] | null>(null);
  const [webhookSignalId, setWebhookSignalId] = useState("");
  const [maxCapital, setMaxCapital] = useState("");
  const [webhookCandidate, setWebhookCandidate] = useState<SignalCandidateView | null>(null);
  const [whBusy, setWhBusy] = useState(false);
  const [whError, setWhError] = useState("");

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

  async function checkStatus() {
    setWhBusy(true);
    setWhError("");
    try {
      const response = await fetch("/api/signals/webhook/status");
      if (!response.ok) throw new Error(`Sunucu ${response.status} döndü.`);
      const parsed = (await response.json()) as { data?: { configured?: unknown } };
      if (typeof parsed.data?.configured !== "boolean") throw new Error("Sunucu yanıtı doğrulanamadı.");
      setConfigured(parsed.data.configured);
    } catch (err) {
      setWhError(err instanceof Error ? err.message : "Durum alınamadı.");
    } finally {
      setWhBusy(false);
    }
  }

  async function refreshIntakes() {
    setWhBusy(true);
    setWhError("");
    try {
      const response = await fetch("/api/signals/webhook/intakes?limit=50");
      if (!response.ok) throw new Error(`Sunucu ${response.status} döndü.`);
      const parsed = (await response.json()) as { data?: { intakes?: unknown } };
      if (!isWebhookIntakeList(parsed.data?.intakes)) throw new Error("Sunucu yanıtı doğrulanamadı.");
      setIntakes(parsed.data.intakes);
    } catch (err) {
      setWhError(err instanceof Error ? err.message : "Alertler alınamadı.");
    } finally {
      setWhBusy(false);
    }
  }

  async function submitWebhookBind() {
    const closedBar = toInt(closedBarUs);
    const observed = toInt(warmupObserved);
    const required = toInt(warmupRequired);
    const staleness = toInt(stalenessUs);
    const ttl = toInt(ttlUs);
    if (
      webhookSignalId.trim() === "" ||
      closedBar === null ||
      observed === null ||
      required === null ||
      staleness === null ||
      ttl === null ||
      ttl === 0
    ) {
      setWhError("Sinyal ID ve zaman/sayı alanları eksiksiz olmalı; TTL pozitif tam sayı olmalı.");
      return;
    }
    if (maxCapital.trim() !== "" && !EXACT_DECIMAL.test(maxCapital.trim())) {
      setWhError(t("signal.maxCapital.invalid"));
      return;
    }
    setWhBusy(true);
    setWhError("");
    try {
      const response = await fetch(`/api/signals/webhook/${encodeURIComponent(webhookSignalId.trim())}/bind`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          closed_bar_time_us: closedBar,
          warmup_bars_observed: observed,
          required_warmup_bars: required,
          max_staleness_us: staleness,
          action_map: DEFAULT_ACTION_MAP,
          qty: qty.trim(),
          ttl_us: ttl,
        }),
      });
      if (!response.ok) throw new Error(`Sunucu ${response.status} döndü.`);
      const parsed = (await response.json()) as { data?: unknown };
      if (!isSignalCandidateView(parsed.data)) throw new Error("Sunucu yanıtı doğrulanamadı.");
      setWebhookCandidate(parsed.data);
    } catch (err) {
      setWhError(err instanceof Error ? err.message : "Aday bağlanamadı.");
    } finally {
      setWhBusy(false);
    }
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="signal-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">SIGNAL BOT · TRADINGVIEW</p>
          <h2 id="signal-title">Sinyal botu: indikatör başlatma</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {whError && (
        <div className="form-error" role="alert">
          {whError}
        </div>
      )}

      <h3 className="paper-subheading">1. {t("signal.step.settings")}</h3>
      <p className="helper-text">
        TradingView alert webhook adresi: <code>{WEBHOOK_PATH}</code>
      </p>
      <pre className="template-payload" aria-label="TradingView alert şablonu">{ALERT_TEMPLATE}</pre>
      <p className="helper-text">
        Sembol/aksiyon A-Z/0-9:_- (en fazla 32); zaman UTC ISO-8601 (…Z) ya da µs tam sayı; fiyat exact decimal.
        Secret sunucudaki DCABOT_TRADINGVIEW_WEBHOOK_TOKEN değeridir; hiçbir ekranda gösterilmez, repoya girmez.
      </p>
      <button className="secondary-button" type="button" disabled={busy || whBusy} onClick={() => void checkStatus()}>
        {t("signal.status.check")}
      </button>
      {configured !== null && (
        <p className="helper-text" role="status">{configured ? "Yapılandırıldı" : "Yapılandırılmadı"}</p>
      )}

      <h3 className="paper-subheading">2. {t("signal.step.alerts")}</h3>
      <button className="secondary-button" type="button" disabled={busy || whBusy} onClick={() => void refreshIntakes()}>
        {t("signal.alerts.refresh")}
      </button>
      {intakes && (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>Sinyal</th>
                <th>Sembol/aksiyon</th>
                <th>Durum</th>
                <th>Seç</th>
              </tr>
            </thead>
            <tbody>
              {intakes.map((row) => (
                <tr key={row.signal_id}>
                  <td>{row.signal_id}</td>
                  <td>{row.symbol}/{row.action}</td>
                  <td>{row.status}</td>
                  <td>
                    <button
                      className="secondary-button paper-fill-button"
                      type="button"
                      onClick={() => setWebhookSignalId(row.signal_id)}
                    >
                      Seç {row.signal_id}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">3. {t("signal.step.launch")}</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Webhook sinyal ID</span>
          <span className="input-wrap">
            <input aria-label="Webhook sinyal ID" value={webhookSignalId} onChange={(event) => setWebhookSignalId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Bağlanacak miktar</span>
          <span className="input-wrap">
            <input aria-label="Webhook miktar" value={qty} onChange={(event) => setQty(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Bağlanacak TTL (µs)</span>
          <span className="input-wrap">
            <input aria-label="Webhook TTL" value={ttlUs} onChange={(event) => setTtlUs(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">{t("signal.maxCapital.label")}</span>
          <span className="input-wrap">
            <input aria-label={t("signal.maxCapital.label")} value={maxCapital} onChange={(event) => setMaxCapital(event.target.value)} />
          </span>
        </label>
      </div>
      <p className="helper-text">Readiness girdileri (kapalı bar, warmup, bayatlık) manuel akışla aynı alanlardan alınır; yön eşlemesi sabit: BUY→BUY, SELL→SELL.</p>
      <button className="primary-button" type="button" disabled={busy || whBusy} onClick={() => void submitWebhookBind()}>
        {t("signal.bind.launch")}
      </button>
      {webhookCandidate && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Aday ID</td>
                <td>{webhookCandidate.candidate_id}</td>
              </tr>
              <tr>
                <td>Yön/miktar</td>
                <td>
                  {webhookCandidate.side} / {webhookCandidate.qty}
                </td>
              </tr>
              <tr>
                <td>Bitiş (µs)</td>
                <td>{webhookCandidate.expires_us}</td>
              </tr>
              {maxCapital.trim() !== "" && (
                <tr>
                  <td>{t("signal.maxCapital.echo")}</td>
                  <td>{maxCapital.trim()}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <AdvancedDetails title="Manuel akış (offline fixture)">
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
      </AdvancedDetails>
      <div className="table-note">
        <span className="note-icon">↳</span> Adaylar salt okunur niyet kayıtlarıdır; emir yetkisi yok.
      </div>
    </section>
  );
}
