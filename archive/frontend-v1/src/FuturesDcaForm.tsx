import { useState } from "react";

import {
  BudgetSlider,
  LabeledSlider,
  NumericParameter,
  QuickPercentChips,
  SegmentedControl,
  TextParameter,
} from "./forms";
import {
  isFuturesGridMarginView,
  postJson,
  type FuturesGridMarginView,
  type FuturesGridPayload,
  type FuturesGridView,
} from "./FuturesPanel";
import { Badge } from "./Badge";
import { useI18n } from "./i18n";

export type FuturesLadderSummaryView = {
  direction: string;
  leg_count: number;
  total_shares: string;
  weighted_average_entry: string | null;
  weighted_average_exact: boolean;
};

export function isFuturesLadderSummaryView(value: unknown): value is FuturesLadderSummaryView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.direction === "string" &&
    typeof body.leg_count === "number" &&
    typeof body.total_shares === "string" &&
    (body.weighted_average_entry === null || typeof body.weighted_average_entry === "string") &&
    typeof body.weighted_average_exact === "boolean"
  );
}

/* Faz 15.3b: Pionex "Futures DCA Bot" sırası — grid seviyeleri üstte, altta
 * düşen-fiyat merdiveni + paylar, sonra TP, sonra yatırım/kaldıraç. Toplam
 * pay + ort. giriş MEVCUT pozisyon projeksiyonundan gelir (UI'da toplama
 * yok); marjin MEVCUT marjin projeksiyonundan. Likidasyon tahmini YOK:
 * venue risk kademesi gerekir, uydurulmaz. */

const TP_CHIPS = [
  { chip: "0.5%", ratio: "0.005" },
  { chip: "1%", ratio: "0.01" },
  { chip: "2%", ratio: "0.02" },
  { chip: "5%", ratio: "0.05" },
  { chip: "10%", ratio: "0.1" },
];

const LEVERAGE_STOPS = ["1", "2", "3", "5", "10"];
const SHARES_INT = /^(?:0|[1-9]\d*)$/;

export function FuturesDcaForm({ grid, busy, error, onGrid }: {
  grid: FuturesGridView | null;
  busy: boolean;
  error: string;
  onGrid: (payload: FuturesGridPayload) => void;
}) {
  const { t } = useI18n();
  const [pair, setPair] = useState("BTCUSDT");
  const [direction, setDirection] = useState("LONG");
  const [lowerPrice, setLowerPrice] = useState("100");
  const [upperPrice, setUpperPrice] = useState("200");
  const [intervalCount, setIntervalCount] = useState("2");
  const [shares, setShares] = useState<string[]>([]);
  const [tpRatio, setTpRatio] = useState("0.02");
  const [investment, setInvestment] = useState("");
  const [leverage, setLeverage] = useState("3");
  const [summary, setSummary] = useState<FuturesLadderSummaryView | null>(null);
  const [margin, setMargin] = useState<FuturesGridMarginView | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState("");
  const [formError, setFormError] = useState("");

  const levels = grid?.levels ?? [];
  const sharesFor = (index: number) => shares[index] ?? "1";
  const tpChip = TP_CHIPS.find((chip) => chip.ratio === tpRatio.trim())?.chip;

  function setShare(index: number, next: string) {
    setShares((current) => {
      const copy = current.slice();
      copy[index] = next;
      return copy;
    });
  }

  function submitGrid() {
    const intervals = Number(intervalCount.trim());
    if (!Number.isInteger(intervals) || intervals < 1) {
      setFormError(t("futuresdca.form.intervalsInvalid"));
      return;
    }
    setFormError("");
    onGrid({
      direction,
      level_mode: "ARITHMETIC",
      lower_price: lowerPrice.trim(),
      upper_price: upperPrice.trim(),
      interval_count: intervals,
      price_tick: "1",
      tick_origin: "0",
    });
  }

  function buildLegs(): { price: string; shares: string }[] | null {
    const legs: { price: string; shares: string }[] = [];
    for (let index = 0; index < levels.length; index += 1) {
      const quantity = sharesFor(index).trim();
      if (!SHARES_INT.test(quantity)) {
        setFormError(t("futuresdca.form.sharesInvalid"));
        return null;
      }
      legs.push({ price: levels[index], shares: quantity });
    }
    if (legs.length === 0 || legs.every((leg) => leg.shares === "0")) {
      setFormError(t("futuresdca.form.sharesInvalid"));
      return null;
    }
    return legs;
  }

  function buildMarginFill(): { fill_id: string; side: string; price: string; quantity: string; effective_time_us: number }[] | null {
    // Marjin matematiği state'ten yalnız toplam miktarı tüketir; merdiven
    // satırları özet ortalamada tek konsolide satıra indirgenir (ara-ortalama
    // exactness tuzağına düşmeden, varsayımsal-projeksiyon etiketiyle).
    if (!summary || !summary.weighted_average_exact || summary.weighted_average_entry === null) {
      setFormError(t("futuresdca.form.averageInexact"));
      return null;
    }
    const side = direction === "SHORT" ? "SELL" : "BUY";
    return [{ fill_id: "ladder-consolidated", side, price: summary.weighted_average_entry, quantity: summary.total_shares, effective_time_us: 1 }];
  }

  async function submitSummary() {
    const legs = buildLegs();
    if (!legs) return;
    setFormError("");
    setLocalError("");
    setLocalBusy(true);
    try {
      setSummary(await postJson("/api/futures/ladder/summary", { direction, legs }, isFuturesLadderSummaryView));
    } catch (requestError) {
      setLocalError(requestError instanceof Error ? requestError.message : t("futuresdca.form.summaryFirst"));
    } finally {
      setLocalBusy(false);
    }
  }

  async function submitMargin() {
    if (!summary) {
      setFormError(t("futuresdca.form.summaryFirst"));
      return;
    }
    const fills = buildMarginFill();
    if (!fills) return;
    setFormError("");
    setLocalError("");
    setLocalBusy(true);
    const body: Record<string, unknown> = {
      direction,
      fills,
      reference_price: summary.weighted_average_entry,
      // Pay = baz birim tanımı gereği sözleşme çarpanı 1'dir (çifte sayım yok).
      contract_size: "1",
    };
    if (investment.trim() !== "") body.available_margin = investment.trim();
    try {
      setMargin(await postJson("/api/futures/grid/margin", body, isFuturesGridMarginView));
    } catch (requestError) {
      setLocalError(requestError instanceof Error ? requestError.message : t("futuresdca.form.summaryFirst"));
    } finally {
      setLocalBusy(false);
    }
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="futuresdca-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">FUTURES DCA</p>
          <h2 id="futuresdca-title">{t("futuresdca.title")}</h2>
        </div>
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {formError && <div className="form-error" role="alert">{formError}</div>}
      {localError && <div className="form-error" role="alert">{localError}</div>}

      <div className="paper-order-form">
        <TextParameter label={t("futuresdca.pair.label")} name="futuresdca_pair" value={pair} onChange={setPair} />
        <SegmentedControl
          label={t("grid.type.label")}
          name="futuresdca_direction"
          value={direction}
          options={[
            { value: "LONG", label: t("grid.type.long") },
            { value: "SHORT", label: t("grid.type.short") },
          ]}
          onChange={setDirection}
        />
        <NumericParameter label={t("grid.levels.lower")} name="futuresdca_low" value={lowerPrice} onChange={setLowerPrice} />
        <NumericParameter label={t("grid.levels.upper")} name="futuresdca_high" value={upperPrice} onChange={setUpperPrice} />
        <NumericParameter integer label={t("grid.levels.intervals")} name="futuresdca_count" value={intervalCount} onChange={setIntervalCount} />
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitGrid}>
        {t("grid.levels.submit")}
      </button>

      <h3 className="paper-subheading">{t("futuresdca.ladder.heading")}</h3>
      {levels.length === 0 ? (
        <div className="empty-state">{t("futuresdca.ladder.empty")}</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>{t("futuresdca.ladder.price")}</th>
                <th>{t("futuresdca.ladder.shares")}</th>
              </tr>
            </thead>
            <tbody>
              {levels.map((level, index) => (
                <tr key={`${level}-${index}`}>
                  <td>{String(index + 1).padStart(2, "0")}</td>
                  <td>{level}</td>
                  <td>
                    <input
                      className="ladder-shares-input"
                      aria-label={`${index + 1}. ${t("futuresdca.ladder.rowShares")}`}
                      value={sharesFor(index)}
                      inputMode="numeric"
                      onChange={(event) => setShare(index, event.target.value)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <button className="secondary-button" type="button" disabled={localBusy || levels.length === 0} onClick={() => void submitSummary()}>
        {t("futuresdca.ladder.compute")}
      </button>
      <p className="helper-text">{t("futuresdca.ladder.note")}</p>

      <h3 className="paper-subheading">{t("futuresdca.tp.heading")}</h3>
      <NumericParameter label={t("futuresdca.tp.label")} name="futuresdca_tp" value={tpRatio} suffix="oran" onChange={setTpRatio} />
      <QuickPercentChips label={t("chips.percent.label")} options={TP_CHIPS} onSelect={setTpRatio} />

      <h3 className="paper-subheading">{t("futuresdca.investment.heading")}</h3>
      <BudgetSlider label={t("setup.investment.label")} name="futuresdca_investment" value={investment} max="10000" step="10" onChange={setInvestment} />
      <LabeledSlider label={t("futuresdca.leverage.label")} name="futuresdca_leverage" value={leverage} stops={LEVERAGE_STOPS} minLabel="1x" maxLabel="10x" onChange={setLeverage} />
      <button className="secondary-button" type="button" disabled={localBusy} onClick={() => void submitMargin()}>
        {t("futuresdca.margin.submit")}
      </button>
      <p className="helper-text">{t("futuresdca.margin.note")}</p>

      <h3 className="paper-subheading">
        {t("futuresdca.summary.label")} · {pair.trim() === "" ? "—" : pair.trim()}{" "}
        <Badge tone="neutral" label={t("badge.exact.label")} title={t("badge.exact.tooltip")} />
      </h3>
      <dl className="summary-list">
        <div>
          <dt>{t("futuresdca.ladder.totalShares")}</dt>
          <dd>{summary?.total_shares ?? "—"}</dd>
        </div>
        <div>
          <dt>{t("futuresdca.ladder.avgEntry")}</dt>
          <dd>
            {summary === null ? "—" : summary.weighted_average_exact && summary.weighted_average_entry !== null ? summary.weighted_average_entry : <span className="state-label">{t("futuresdca.ladder.inexact")}</span>}
          </dd>
        </div>
        <div>
          <dt>{t("futuresdca.tp.label")}</dt>
          <dd>{tpChip ? `${tpChip} (${tpRatio.trim()})` : tpRatio.trim() === "" ? "—" : tpRatio.trim()}</dd>
        </div>
        <div>
          <dt>{t("futuresdca.leverage.label")}</dt>
          <dd>{leverage.trim() === "" ? "—" : `${leverage.trim()}x`}</dd>
        </div>
        <div>
          <dt>{t("futuresdca.margin.required")}</dt>
          <dd>{margin?.required_initial_margin ?? "—"}</dd>
        </div>
        <div>
          <dt>{t("futuresdca.margin.capacity")}</dt>
          <dd>{margin?.capacity_status ?? "—"}</dd>
        </div>
      </dl>
      <p className="helper-text">{t("futuresdca.liq.note")}</p>
    </section>
  );
}
