import { useState } from "react";

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

export function RiskPanel({
  explanation,
  busy,
  error,
  onExplain,
}: {
  explanation: RiskExplainView | null;
  busy: boolean;
  error: string;
  onExplain: (payload: RiskExplainPayload) => void;
}) {
  const [sessionId, setSessionId] = useState("");
  const [botId, setBotId] = useState("");
  const [symbol, setSymbol] = useState("");
  const [dealId, setDealId] = useState("");

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
    </section>
  );
}
