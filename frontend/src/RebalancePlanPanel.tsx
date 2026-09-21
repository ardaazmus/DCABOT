import { useState } from "react";

export type RebalancePlanView = {
  plan_id: string;
  status: string;
  gross_buy: string;
  gross_sell: string;
  trigger_policy: string;
  plan_time_us?: number;
  valuation_asset?: string;
  total_equity?: string;
};

export type RebalanceDisclosureLineView = {
  asset: string;
  side: string;
  gross_delta: string;
  fee: string;
  qty: string;
  quantized_qty: string;
  remainder_qty: string;
  status: string;
};

export type RebalanceDisclosureView = {
  status: string;
  total_fee: string;
  lines: RebalanceDisclosureLineView[];
};

export type RebalanceCandidateView = {
  candidate_id: string;
  asset: string;
  side: string;
  qty: string;
  status: string;
};

export type RebalancePlanPayload = {
  trigger:
    | { policy: "threshold"; current_weight: string; target_weight: string; threshold: string }
    | { policy: "time"; last_rebalance_us: number; now_us: number; interval_us: number };
  projection: {
    valuation_asset: string;
    total_equity: string;
    allocations: [string, string, string][];
  };
};

export type RebalanceDisclosePayload = {
  plan: RebalancePlanView;
  projection: RebalancePlanPayload["projection"];
  prices: [string, string][];
  fee_rate: string;
  qty_step: string;
  min_notional: string;
  cash_reserve: string;
};

function parseTripleLines(text: string): { rows: [string, string, string][]; error: string } {
  const rows: [string, string, string][] = [];
  const lines = text.split("\n");
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trim();
    if (!line) continue;
    const parts = line.split(/\s+/);
    if (parts.length !== 3) {
      return { rows: [], error: `Satır ${index + 1}: "ASSET AĞIRLIK DEĞER" biçiminde olmalı.` };
    }
    rows.push([parts[0], parts[1], parts[2]]);
  }
  return { rows, error: "" };
}

function parsePairLines(text: string): { rows: [string, string][]; error: string } {
  const rows: [string, string][] = [];
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isRebalancePlanView(value: unknown): value is RebalancePlanView {
  return (
    isRecord(value) &&
    typeof value.plan_id === "string" &&
    typeof value.status === "string" &&
    typeof value.gross_buy === "string" &&
    typeof value.gross_sell === "string" &&
    typeof value.trigger_policy === "string"
  );
}

export function isRebalanceDisclosureView(value: unknown): value is { disclosure: RebalanceDisclosureView; candidates: RebalanceCandidateView[] } {
  if (!isRecord(value)) return false;
  const disclosure = value.disclosure as Record<string, unknown>;
  if (!isRecord(disclosure) || typeof disclosure.status !== "string" || typeof disclosure.total_fee !== "string") return false;
  if (!Array.isArray(disclosure.lines)) return false;
  const linesOk = (disclosure.lines as unknown[]).every(
    (line: unknown) =>
      isRecord(line) &&
      typeof line.asset === "string" &&
      typeof line.side === "string" &&
      typeof line.gross_delta === "string" &&
      typeof line.fee === "string" &&
      typeof line.qty === "string" &&
      typeof line.quantized_qty === "string" &&
      typeof line.remainder_qty === "string" &&
      typeof line.status === "string",
  );
  const candidatesOk =
    Array.isArray(value.candidates) &&
    (value.candidates as unknown[]).every(
      (candidate: unknown) =>
        isRecord(candidate) &&
        typeof candidate.candidate_id === "string" &&
        typeof candidate.asset === "string" &&
        typeof candidate.side === "string" &&
        typeof candidate.qty === "string" &&
        typeof candidate.status === "string",
    );
  return linesOk && candidatesOk;
}

export function RebalancePlanPanel({
  plan,
  disclosure,
  candidates,
  busy,
  error,
  onPlan,
  onDisclose,
}: {
  plan: RebalancePlanView | null;
  disclosure: RebalanceDisclosureView | null;
  candidates: RebalanceCandidateView[];
  busy: boolean;
  error: string;
  onPlan: (payload: RebalancePlanPayload) => void;
  onDisclose: (payload: RebalanceDisclosePayload) => void;
}) {
  const [policy, setPolicy] = useState<"threshold" | "time">("threshold");
  const [currentWeight, setCurrentWeight] = useState("0.5");
  const [targetWeight, setTargetWeight] = useState("0.6");
  const [threshold, setThreshold] = useState("0.05");
  const [lastRebalanceUs, setLastRebalanceUs] = useState("");
  const [nowUs, setNowUs] = useState("");
  const [intervalUs, setIntervalUs] = useState("");
  const [equity, setEquity] = useState("1000");
  const [allocations, setAllocations] = useState("BTC 0.6 500\nETH 0.4 500");
  const [prices, setPrices] = useState("BTC 50000\nETH 1600");
  const [feeRate, setFeeRate] = useState("0.001");
  const [qtyStep, setQtyStep] = useState("0.001");
  const [minNotional, setMinNotional] = useState("10");
  const [cashReserve, setCashReserve] = useState("1000");
  const [formError, setFormError] = useState("");

  function currentProjection(): RebalancePlanPayload["projection"] | null {
    const parsed = parseTripleLines(allocations);
    if (parsed.error) {
      setFormError(`Dağılım: ${parsed.error}`);
      return null;
    }
    if (parsed.rows.length === 0) {
      setFormError("Dağılım: en az bir satır gerekli.");
      return null;
    }
    return { valuation_asset: "USDT", total_equity: equity.trim(), allocations: parsed.rows };
  }

  function submitPlan() {
    const projection = currentProjection();
    if (!projection) return;
    if (policy === "threshold") {
      setFormError("");
      onPlan({
        trigger: {
          policy: "threshold",
          current_weight: currentWeight.trim(),
          target_weight: targetWeight.trim(),
          threshold: threshold.trim(),
        },
        projection,
      });
      return;
    }
    const last = Number(lastRebalanceUs.trim());
    const now = Number(nowUs.trim());
    const interval = Number(intervalUs.trim());
    if (![last, now, interval].every((v) => Number.isInteger(v) && v >= 0)) {
      setFormError("Zaman alanları negatif-olmayan tam sayı olmalıdır.");
      return;
    }
    setFormError("");
    onPlan({
      trigger: { policy: "time", last_rebalance_us: last, now_us: now, interval_us: interval },
      projection,
    });
  }

  function submitDisclose() {
    if (!plan) return;
    const projection = currentProjection();
    if (!projection) return;
    const parsed = parsePairLines(prices);
    if (parsed.error) {
      setFormError(`Fiyatlar: ${parsed.error}`);
      return;
    }
    setFormError("");
    onDisclose({
      plan,
      projection,
      prices: parsed.rows,
      fee_rate: feeRate.trim(),
      qty_step: qtyStep.trim(),
      min_notional: minNotional.trim(),
      cash_reserve: cashReserve.trim(),
    });
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="rebalance-plan-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">REBALANCE PLAN</p>
          <h2 id="rebalance-plan-title">Rebalancing planı ve disclosure</h2>
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

      <h3 className="paper-subheading">Tetikleyici</h3>
      <div className="mapping-row">
        <label className="field">
          <span className="field-label">Politika</span>
          <select aria-label="Politika" value={policy} onChange={(event) => setPolicy(event.target.value as "threshold" | "time")}>
            <option value="threshold">Eşik (threshold)</option>
            <option value="time">Zaman (time)</option>
          </select>
        </label>
        {policy === "threshold" ? (
          <>
            <label className="field">
              <span className="field-label">Mevcut ağırlık</span>
              <span className="input-wrap">
                <input aria-label="Mevcut ağırlık" value={currentWeight} onChange={(event) => setCurrentWeight(event.target.value)} />
              </span>
            </label>
            <label className="field">
              <span className="field-label">Hedef ağırlık</span>
              <span className="input-wrap">
                <input aria-label="Hedef ağırlık" value={targetWeight} onChange={(event) => setTargetWeight(event.target.value)} />
              </span>
            </label>
            <label className="field">
              <span className="field-label">Eşik</span>
              <span className="input-wrap">
                <input aria-label="Eşik" value={threshold} onChange={(event) => setThreshold(event.target.value)} />
              </span>
            </label>
          </>
        ) : (
          <>
            <label className="field">
              <span className="field-label">Son dengeleme (µs)</span>
              <span className="input-wrap">
                <input aria-label="Son dengeleme" value={lastRebalanceUs} onChange={(event) => setLastRebalanceUs(event.target.value)} />
              </span>
            </label>
            <label className="field">
              <span className="field-label">Şimdi (µs)</span>
              <span className="input-wrap">
                <input aria-label="Şimdi" value={nowUs} onChange={(event) => setNowUs(event.target.value)} />
              </span>
            </label>
            <label className="field">
              <span className="field-label">Aralık (µs)</span>
              <span className="input-wrap">
                <input aria-label="Aralık" value={intervalUs} onChange={(event) => setIntervalUs(event.target.value)} />
              </span>
            </label>
          </>
        )}
      </div>

      <h3 className="paper-subheading">Projeksiyon girdisi</h3>
      <label className="field">
        <span className="field-label">Özsermaye (değerleme paneli çıktısından kopyalayın)</span>
        <span className="input-wrap">
          <input aria-label="Özsermaye" value={equity} onChange={(event) => setEquity(event.target.value)} />
        </span>
      </label>
      <label className="field">
        <span className="field-label">Dağılım (satır başına: ASSET AĞIRLIK MEVCUT-DEĞER)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Dağılım"
          rows={3}
          value={allocations}
          onChange={(event) => setAllocations(event.target.value)}
        />
      </label>
      <button className="primary-button" type="button" disabled={busy} onClick={submitPlan}>
        {busy ? "Üretiliyor…" : "Planı üret"}
      </button>

      {plan && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Plan ID</td>
                <td>{plan.plan_id}</td>
              </tr>
              <tr>
                <td>Brüt al/sat</td>
                <td>
                  {plan.gross_buy} / {plan.gross_sell}
                </td>
              </tr>
              <tr>
                <td>Tetikleyici</td>
                <td>{plan.trigger_policy}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Fee/rounding disclosure</h3>
      <label className="field">
        <span className="field-label">Fiyatlar (satır başına: ASSET FİYAT)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Fiyatlar"
          rows={2}
          value={prices}
          onChange={(event) => setPrices(event.target.value)}
        />
      </label>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Fee oranı</span>
          <span className="input-wrap">
            <input aria-label="Fee oranı" value={feeRate} onChange={(event) => setFeeRate(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Miktar adımı</span>
          <span className="input-wrap">
            <input aria-label="Miktar adımı" value={qtyStep} onChange={(event) => setQtyStep(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Min notional</span>
          <span className="input-wrap">
            <input aria-label="Min notional" value={minNotional} onChange={(event) => setMinNotional(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Nakit rezervi</span>
          <span className="input-wrap">
            <input aria-label="Nakit rezervi" value={cashReserve} onChange={(event) => setCashReserve(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy || !plan} onClick={submitDisclose}>
        Disclosure hesapla
      </button>

      {disclosure && (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>Varlık</th>
                <th>Yön</th>
                <th>Brüt</th>
                <th>Fee</th>
                <th>Miktar</th>
                <th>Yuvarlanmış</th>
                <th>Kalan</th>
                <th>Durum</th>
              </tr>
            </thead>
            <tbody>
              {disclosure.lines.map((line) => (
                <tr key={line.asset}>
                  <td>{line.asset}</td>
                  <td>{line.side}</td>
                  <td>{line.gross_delta}</td>
                  <td>{line.fee}</td>
                  <td>{line.qty}</td>
                  <td>{line.quantized_qty}</td>
                  <td>{line.remainder_qty}</td>
                  <td>{line.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {candidates.length > 0 && (
        <>
          <h3 className="paper-subheading">Emir adayları</h3>
          <div className="table-wrap paper-result">
            <table>
              <thead>
                <tr>
                  <th>Aday ID</th>
                  <th>Varlık</th>
                  <th>Yön</th>
                  <th>Miktar</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((candidate) => (
                  <tr key={candidate.candidate_id}>
                    <td>{candidate.candidate_id}</td>
                    <td>{candidate.asset}</td>
                    <td>{candidate.side}</td>
                    <td>{candidate.qty}</td>
                    <td>{candidate.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      <div className="table-note">
        <span className="note-icon">↳</span> Plan ve adaylar salt okunur kayıtlardır; emir yetkisi yok.
      </div>
    </section>
  );
}
