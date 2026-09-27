import { useState } from "react";

export type RecurringSlotView = {
  index: number;
  slot_us: number;
};

export type RecurringScheduleView = {
  symbol: string;
  quote_amount: string;
  start_us: number;
  interval_us: number;
  count: number;
  slots: RecurringSlotView[];
  total_quote: string;
  order_authority: string;
};

export type RecurringSchedulePayload = {
  symbol: string;
  quote_amount: string;
  start_us: number;
  interval_us: number;
  count: number;
};

export function isRecurringScheduleView(value: unknown): value is RecurringScheduleView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.symbol === "string" &&
    typeof body.quote_amount === "string" &&
    typeof body.start_us === "number" &&
    typeof body.interval_us === "number" &&
    typeof body.count === "number" &&
    Array.isArray(body.slots) &&
    typeof body.total_quote === "string" &&
    typeof body.order_authority === "string"
  );
}

export function RecurringPanel({
  schedule,
  busy,
  error,
  onProject,
}: {
  schedule: RecurringScheduleView | null;
  busy: boolean;
  error: string;
  onProject: (payload: RecurringSchedulePayload) => void;
}) {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [amount, setAmount] = useState("100");
  const [startUs, setStartUs] = useState("1000000");
  const [intervalUs, setIntervalUs] = useState("500000");
  const [count, setCount] = useState("3");
  const [formError, setFormError] = useState("");

  function submit() {
    const start = Number(startUs.trim());
    const interval = Number(intervalUs.trim());
    const slots = Number(count.trim());
    if (!symbol.trim() || !amount.trim()) {
      setFormError("Sembol ve tutar boş olamaz.");
      return;
    }
    if (!Number.isInteger(start) || start < 0 || !Number.isInteger(interval) || interval <= 0) {
      setFormError("Zamanlar integer, aralık pozitif olmalı.");
      return;
    }
    if (!Number.isInteger(slots) || slots < 1 || slots > 365) {
      setFormError("Slot sayısı 1-365 arası olmalı.");
      return;
    }
    setFormError("");
    onProject({
      symbol: symbol.trim(),
      quote_amount: amount.trim(),
      start_us: start,
      interval_us: interval,
      count: slots,
    });
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="recurring-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">SCHEDULER</p>
          <h2 id="recurring-title">Dönemsel alım takvimi</h2>
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
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Sembol</span>
          <span className="input-wrap">
            <input aria-label="Sembol" value={symbol} onChange={(e) => setSymbol(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Slot tutarı</span>
          <span className="input-wrap">
            <input aria-label="Slot tutarı" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Başlangıç (µs)</span>
          <span className="input-wrap">
            <input aria-label="Başlangıç (µs)" value={startUs} onChange={(e) => setStartUs(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Aralık (µs)</span>
          <span className="input-wrap">
            <input aria-label="Aralık (µs)" value={intervalUs} onChange={(e) => setIntervalUs(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Slot sayısı</span>
          <span className="input-wrap">
            <input aria-label="Slot sayısı" value={count} onChange={(e) => setCount(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submit}>
        Takvimi projekte et
      </button>
      {schedule && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Slot</td>
                <td>{schedule.count}</td>
              </tr>
              <tr>
                <td>Toplam tutar</td>
                <td>{schedule.total_quote}</td>
              </tr>
              <tr>
                <td>İlk / son slot</td>
                <td>
                  {schedule.slots[0]?.slot_us} / {schedule.slots[schedule.slots.length - 1]?.slot_us}
                </td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Plan projeksiyonudur; emir yetkisi yok, safety/DCA stratejisi değil.
          </p>
        </div>
      )}
    </section>
  );
}
