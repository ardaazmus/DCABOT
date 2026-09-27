import { useState } from "react";

import { Banner } from "./notifications";

export type RiskReasonView = {
  code: string;
  severity: string;
  message: string;
};

export type RiskExplainView = {
  blocked: boolean;
  reasons: RiskReasonView[];
};

export type RiskExplainPayload = {
  session_id?: string;
  bot_id?: string;
  symbol?: string;
  deal_id?: string;
};

export type CanaryStatusView = {
  verdict: string;
  reasons: string[];
  kill_switch_engaged: boolean;
  approval_present: boolean;
  spec_status: string;
  paper_fill_count: number;
  observed_at: string;
};

export function isCanaryStatusView(value: unknown): value is CanaryStatusView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.verdict === "string" &&
    Array.isArray(body.reasons) &&
    (body.reasons as unknown[]).every((reason) => typeof reason === "string") &&
    typeof body.kill_switch_engaged === "boolean" &&
    typeof body.approval_present === "boolean" &&
    typeof body.spec_status === "string" &&
    typeof body.paper_fill_count === "number" &&
    typeof body.observed_at === "string"
  );
}

export function isRiskExplainView(value: unknown): value is RiskExplainView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.blocked === "boolean" &&
    Array.isArray(body.reasons) &&
    (body.reasons as unknown[]).every((reason) => {
      if (typeof reason !== "object" || reason === null) return false;
      const item = reason as Record<string, unknown>;
      return (
        typeof item.code === "string" &&
        typeof item.severity === "string" &&
        typeof item.message === "string"
      );
    })
  );
}

/**
 * Faz 17 AA.10a: global kill-switch bandı — tüm bölümlerde görünür (App
 * shell'inde Banner-precedentinin yanında). Yalnız engaged=true iken çıkar;
 * okunmamış (null) durumda da gizlenir — okunmamışlık "kapalı" demek
 * değildir, RiskPanel'deki "henüz okunmadı" notu o durumu taşır.
 */
export function KillSwitchBanner({
  canary,
  busy,
  onRefresh,
}: {
  canary: CanaryStatusView | null;
  busy: boolean;
  onRefresh: () => void;
}) {
  if (canary === null || !canary.kill_switch_engaged) return null;
  return (
    <Banner tone="critical">
      ⛔ KILL-SWITCH DEVREDE — yeni riskli işlemler engelleniyor ({canary.verdict}).
      {" "}
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        {busy ? "Okunuyor…" : "Durumu yenile"}
      </button>
    </Banner>
  );
}

export function RiskPanel({
  explanation,
  busy,
  error,
  onExplain,
  canary,
  canaryBusy,
  canaryError,
  onRefreshCanary,
  onSetKillSwitch,
}: {
  explanation: RiskExplainView | null;
  busy: boolean;
  error: string;
  onExplain: (payload: RiskExplainPayload) => void;
  canary: CanaryStatusView | null;
  canaryBusy: boolean;
  canaryError: string;
  onRefreshCanary: () => void;
  onSetKillSwitch: (engaged: boolean, reason: string) => void;
}) {
  const [sessionId, setSessionId] = useState("");
  const [botId, setBotId] = useState("");
  const [symbol, setSymbol] = useState("");
  const [dealId, setDealId] = useState("");
  const [killReason, setKillReason] = useState("");

  function submit() {
    const payload: RiskExplainPayload = {};
    if (sessionId.trim()) payload.session_id = sessionId.trim();
    if (botId.trim()) payload.bot_id = botId.trim();
    if (symbol.trim()) payload.symbol = symbol.trim();
    if (dealId.trim()) payload.deal_id = dealId.trim();
    onExplain(payload);
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="risk-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">RISK DESK</p>
          <h2 id="risk-title">Neden işlem açılmıyor</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Session (opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="Session (opsiyonel)" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Bot (opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="Bot (opsiyonel)" value={botId} onChange={(e) => setBotId(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Sembol (opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="Sembol (opsiyonel)" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Deal (opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="Deal (opsiyonel)" value={dealId} onChange={(e) => setDealId(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submit}>
        Açıkla
      </button>
      {explanation && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Engel</td>
                <td>{explanation.blocked ? "VAR" : "YOK"}</td>
              </tr>
              {explanation.reasons.map((reason) => (
                <tr key={reason.code}>
                  <td>{reason.code}</td>
                  <td>{reason.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="paper-note">
            Salt-okunur açıklama; hiçbir kararı değiştirmez.
          </p>
        </div>
      )}
      <p className="eyebrow">CIRCUIT BREAKER · CANARY</p>
      {canaryError && <div className="form-error" role="alert">{canaryError}</div>}
      {canary ? (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Karar</td>
                <td>
                  <span className={canary.verdict === "CANARY_GO" ? "state-label ready" : "state-label"}>
                    {canary.verdict}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Kill-switch</td>
                <td>
                  <span className={canary.kill_switch_engaged ? "state-label error" : "state-label"}>
                    {canary.kill_switch_engaged ? "AÇIK (devrede)" : "kapalı"}
                  </span>
                </td>
              </tr>
              <tr><td>Onay belgesi</td><td>{canary.approval_present ? "VAR" : "YOK"}</td></tr>
              <tr><td>Spec</td><td>{canary.spec_status}</td></tr>
              <tr><td>Paper dolum</td><td>{canary.paper_fill_count}</td></tr>
              {canary.reasons.map((reason) => (
                <tr key={reason}>
                  <td>Neden</td>
                  <td>{reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="paper-note">
            Spec yokken karar her zaman NOGO&apos;dur (Arda değerleri bekleniyor). Anahtar yalnızca yerel
            işaret dosyasıdır; canlı emir yolu zaten kapalı.
          </p>
        </div>
      ) : (
        <p className="helper-text">Durum henüz okunmadı — Yenile ile sorgulayın.</p>
      )}
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Gerekçe (açma için zorunlu)</span>
          <span className="input-wrap">
            <input aria-label="Gerekçe (açma için zorunlu)" value={killReason} onChange={(e) => setKillReason(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={canaryBusy} onClick={onRefreshCanary}>
        Yenile
      </button>
      <button className="secondary-button" type="button" disabled={canaryBusy} onClick={() => onSetKillSwitch(true, killReason)}>
        Anahtarı aç
      </button>
      <button className="secondary-button" type="button" disabled={canaryBusy} onClick={() => onSetKillSwitch(false, "")}>
        Anahtarı kapat
      </button>
    </section>
  );
}
