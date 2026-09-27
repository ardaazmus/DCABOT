import { useState } from "react";
import { SegmentedControl } from "./forms";
import { useI18n } from "./i18n";

export type FuturesGridView = {
  levels: string[];
  arithmetic_step: string | null;
  level_mode: string;
  gross_spacing_percent?: string | null;
  gross_spacing_percent_exact?: boolean;
};

export type FuturesPlacementView = {
  decision: string;
  candidate_levels: string[];
  order_authority: string;
  reason: string | null;
};

export type FuturesGridPositionView = {
  position_side: string;
  quantity: string;
  average_entry: string | null;
};

export type FuturesGridMarginView = {
  notional: string;
  required_initial_margin: string;
  reserve_asset: string;
  capacity_status: string;
};

export type FuturesGridLifecycleView = {
  status: string;
  fill_ids: string[];
  replacement_admitted: boolean;
  event_count: number;
};

export type FuturesVariantRow = {
  variant: string;
  admission: string;
  reason: string;
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
  if (
    typeof value !== "object" ||
    value === null ||
    !Array.isArray((value as Record<string, unknown>).levels) ||
    !((value as Record<string, unknown>).levels as unknown[]).every((l) => typeof l === "string") ||
    !isStringOrNull((value as Record<string, unknown>).arithmetic_step) ||
    typeof (value as Record<string, unknown>).level_mode !== "string"
  ) {
    return false;
  }
  const body = value as Record<string, unknown>;
  if ("gross_spacing_percent" in body && !isStringOrNull(body.gross_spacing_percent)) return false;
  if ("gross_spacing_percent_exact" in body && typeof body.gross_spacing_percent_exact !== "boolean") return false;
  return true;
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isFuturesPlacementView(value: unknown): value is FuturesPlacementView {
  return (
    isRecord(value) &&
    typeof value.decision === "string" &&
    Array.isArray(value.candidate_levels) &&
    (value.candidate_levels as unknown[]).every((l) => typeof l === "string") &&
    typeof value.order_authority === "string" &&
    isStringOrNull(value.reason)
  );
}

export function isFuturesGridPositionView(value: unknown): value is FuturesGridPositionView {
  return (
    isRecord(value) &&
    typeof value.position_side === "string" &&
    typeof value.quantity === "string" &&
    isStringOrNull(value.average_entry)
  );
}

export function isFuturesGridMarginView(value: unknown): value is FuturesGridMarginView {
  return (
    isRecord(value) &&
    typeof value.notional === "string" &&
    typeof value.required_initial_margin === "string" &&
    typeof value.reserve_asset === "string" &&
    typeof value.capacity_status === "string"
  );
}

export function isFuturesGridLifecycleView(value: unknown): value is FuturesGridLifecycleView {
  return (
    isRecord(value) &&
    typeof value.status === "string" &&
    Array.isArray(value.fill_ids) &&
    (value.fill_ids as unknown[]).every((l) => typeof l === "string") &&
    typeof value.replacement_admitted === "boolean" &&
    typeof value.event_count === "number"
  );
}

export function isFuturesVariantRows(value: unknown): value is FuturesVariantRow[] {
  return (
    Array.isArray(value) &&
    value.every(
      (row: unknown) =>
        isRecord(row) &&
        typeof row.variant === "string" &&
        typeof row.admission === "string" &&
        typeof row.reason === "string",
    )
  );
}

export async function postJson<T>(url: string, body: unknown, guard: (value: unknown) => value is T): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Sunucu ${response.status} döndü.`);
  const parsed = (await response.json()) as { data?: unknown };
  if (!guard(parsed.data)) throw new Error("Sunucu yanıtı doğrulanamadı.");
  return parsed.data;
}

async function getJson<T>(url: string, guard: (value: unknown) => value is T): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Sunucu ${response.status} döndü.`);
  const parsed = (await response.json()) as { data?: unknown };
  if (!guard(parsed.data)) throw new Error("Sunucu yanıtı doğrulanamadı.");
  return parsed.data;
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
  const { t } = useI18n();
  const [direction, setDirection] = useState("LONG");
  const [levelMode, setLevelMode] = useState("ARITHMETIC");
  const [lowerPrice, setLowerPrice] = useState("100");
  const [upperPrice, setUpperPrice] = useState("200");
  const [intervalCount, setIntervalCount] = useState("2");
  const [priceTick, setPriceTick] = useState("1");
  const [placementMode, setPlacementMode] = useState("STATIC");
  const [rangePolicy, setRangePolicy] = useState("FIXED");
  const [placement, setPlacement] = useState<FuturesPlacementView | null>(null);
  const [posDirection, setPosDirection] = useState("LONG");
  const [fillsJson, setFillsJson] = useState('[{"fill_id":"f1","side":"BUY","price":"100","quantity":"1","effective_time_us":1000}]');
  const [position, setPosition] = useState<FuturesGridPositionView | null>(null);
  const [marginRef, setMarginRef] = useState("150");
  const [marginSize, setMarginSize] = useState("1");
  const [marginAvailable, setMarginAvailable] = useState("");
  const [margin, setMargin] = useState<FuturesGridMarginView | null>(null);
  const [eventsJson, setEventsJson] = useState('[{"event_id":"e1","event_type":"CANCEL_REQUESTED","event_sequence":1},{"event_id":"e2","event_type":"CANCEL_CONFIRMED","event_sequence":2}]');
  const [lifecycle, setLifecycle] = useState<FuturesGridLifecycleView | null>(null);
  const [variants, setVariants] = useState<FuturesVariantRow[] | null>(null);
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState("");
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

  function currentLevels() {
    const intervals = Number(intervalCount.trim());
    if (!Number.isInteger(intervals) || intervals < 1) {
      setFormError("Aralık sayısı pozitif tam sayı olmalı.");
      return null;
    }
    return {
      direction,
      level_mode: levelMode,
      lower_price: lowerPrice.trim(),
      upper_price: upperPrice.trim(),
      interval_count: intervals,
      price_tick: priceTick.trim(),
      tick_origin: "0",
    };
  }

  function parseJsonArray(raw: string, label: string): unknown[] | null {
    try {
      const parsed: unknown = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) {
        setLocalError(`${label} JSON dizisi olmalı.`);
        return null;
      }
      return parsed;
    } catch {
      setLocalError(`${label} geçerli JSON değil.`);
      return null;
    }
  }

  async function submitPlacement() {
    const levels = currentLevels();
    if (!levels) return;
    setLocalBusy(true);
    setLocalError("");
    try {
      setPlacement(await postJson("/api/futures/grid/placement", { ...levels, placement_mode: placementMode, range_policy: rangePolicy }, isFuturesPlacementView));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Yerleşim alınamadı.");
    } finally {
      setLocalBusy(false);
    }
  }

  async function submitPosition() {
    const fills = parseJsonArray(fillsJson, "Fill listesi");
    if (!fills) return;
    setLocalBusy(true);
    setLocalError("");
    try {
      setPosition(await postJson("/api/futures/grid/position", { direction: posDirection, fills }, isFuturesGridPositionView));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Pozisyon alınamadı.");
    } finally {
      setLocalBusy(false);
    }
  }

  async function submitMargin() {
    const fills = parseJsonArray(fillsJson, "Fill listesi");
    if (!fills) return;
    const body: Record<string, unknown> = {
      direction: posDirection,
      fills,
      reference_price: marginRef.trim(),
      contract_size: marginSize.trim(),
    };
    if (marginAvailable.trim() !== "") body.available_margin = marginAvailable.trim();
    setLocalBusy(true);
    setLocalError("");
    try {
      setMargin(await postJson("/api/futures/grid/margin", body, isFuturesGridMarginView));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Marjin alınamadı.");
    } finally {
      setLocalBusy(false);
    }
  }

  async function submitLifecycle() {
    const events = parseJsonArray(eventsJson, "Olay listesi");
    if (!events) return;
    setLocalBusy(true);
    setLocalError("");
    try {
      setLifecycle(await postJson("/api/futures/grid/lifecycle", { events }, isFuturesGridLifecycleView));
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Lifecycle alınamadı.");
    } finally {
      setLocalBusy(false);
    }
  }

  async function submitPolicy() {
    setLocalBusy(true);
    setLocalError("");
    try {
      const rows = await getJson<{ variants: unknown }>("/api/futures/grid/variants", (value): value is { variants: unknown } => isRecord(value) && "variants" in value);
      if (!isFuturesVariantRows(rows.variants)) throw new Error("Sunucu yanıtı doğrulanamadı.");
      setVariants(rows.variants);
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Varyantlar alınamadı.");
    } finally {
      setLocalBusy(false);
    }
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
        <SegmentedControl
          label={t("grid.type.label")}
          name="futures_direction"
          value={direction}
          options={[
            { value: "LONG", label: t("grid.type.long") },
            { value: "NEUTRAL", label: t("grid.type.neutral") },
            { value: "SHORT", label: t("grid.type.short") },
            { value: "HEDGE", label: t("grid.type.hedge"), disabled: true },
          ]}
          onChange={setDirection}
        />
        <SegmentedControl
          label={t("grid.size.label")}
          name="futures_grid_size"
          value="INTERVAL"
          options={[
            { value: "INTERVAL", label: t("grid.size.interval") },
            { value: "INFINITE", label: t("grid.size.infinite"), disabled: true },
          ]}
          onChange={() => {}}
        />
        <label className="field">
          <span className="field-label">{t("grid.levels.lower")}</span>
          <span className="input-wrap">
            <input aria-label={t("grid.levels.lower")} value={lowerPrice} onChange={(event) => setLowerPrice(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">{t("grid.levels.upper")}</span>
          <span className="input-wrap">
            <input aria-label={t("grid.levels.upper")} value={upperPrice} onChange={(event) => setUpperPrice(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">{t("grid.levels.intervals")}</span>
          <span className="input-wrap">
            <input aria-label={t("grid.levels.intervals")} value={intervalCount} onChange={(event) => setIntervalCount(event.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitGrid}>
        {t("grid.levels.submit")}
      </button>
      <p className="helper-text">Sonsuz grid varyant kapısıyla kapalı (INFINITY_GRID BLOCKED); hedge one-way profilinde desteklenmez.</p>
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
              {grid.gross_spacing_percent != null && (
                <tr>
                  <td>{t("grid.profitPerGrid.label")}</td>
                  <td>{grid.gross_spacing_percent}{grid.gross_spacing_percent_exact === false ? " (yuvarlandı)" : ""}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {grid?.gross_spacing_percent != null && (
        <p className="helper-text">Brüt aralık yüzdesi; fee/funding hariç, emir yetkisi yok.</p>
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
      <h3 className="paper-subheading">Yerleşim değerlendirmesi</h3>
      {localError && (
        <div className="form-error" role="alert">
          {localError}
        </div>
      )}
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Yerleşim modu</span>
          <span className="input-wrap">
            <select aria-label="Yerleşim modu" value={placementMode} onChange={(event) => setPlacementMode(event.target.value)}>
              <option value="STATIC">STATIC</option>
              <option value="DYNAMIC">DYNAMIC</option>
            </select>
          </span>
        </label>
        <label className="field">
          <span className="field-label">Aralık politikası</span>
          <span className="input-wrap">
            <select aria-label="Aralık politikası" value={rangePolicy} onChange={(event) => setRangePolicy(event.target.value)}>
              <option value="FIXED">FIXED</option>
              <option value="RANGE_REVISION">RANGE_REVISION</option>
            </select>
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy || localBusy} onClick={() => void submitPlacement()}>
        Yerleşimi değerlendir
      </button>
      {placement && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Karar</td>
                <td>{placement.decision}</td>
              </tr>
              <tr>
                <td>Aday seviyeler</td>
                <td>{placement.candidate_levels.join(" · ") || "—"}</td>
              </tr>
              <tr>
                <td>Emir yetkisi</td>
                <td>{placement.order_authority}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Pozisyon ve marjin projeksiyonu</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Pozisyon yönü</span>
          <span className="input-wrap">
            <select aria-label="Pozisyon yönü" value={posDirection} onChange={(event) => setPosDirection(event.target.value)}>
              <option value="LONG">LONG</option>
              <option value="SHORT">SHORT</option>
            </select>
          </span>
        </label>
        <label className="field">
          <span className="field-label">Referans fiyat</span>
          <span className="input-wrap">
            <input aria-label="Referans fiyat" value={marginRef} onChange={(event) => setMarginRef(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Kontrat boyu (marjin)</span>
          <span className="input-wrap">
            <input aria-label="Kontrat boyu (marjin)" value={marginSize} onChange={(event) => setMarginSize(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Kullanılabilir marjin (opsiyonel)</span>
          <span className="input-wrap">
            <input aria-label="Kullanılabilir marjin (opsiyonel)" value={marginAvailable} onChange={(event) => setMarginAvailable(event.target.value)} />
          </span>
        </label>
      </div>
      <label className="field">
        <span className="field-label">Fill listesi (JSON)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Fill listesi (JSON)"
          rows={3}
          value={fillsJson}
          onChange={(event) => setFillsJson(event.target.value)}
        />
      </label>
      <div className="template-list">
        <button className="secondary-button" type="button" disabled={busy || localBusy} onClick={() => void submitPosition()}>
          Pozisyonu projekte et
        </button>
        <button className="secondary-button" type="button" disabled={busy || localBusy} onClick={() => void submitMargin()}>
          Marjini projekte et
        </button>
      </div>
      {position && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Taraf/miktar</td>
                <td>{position.position_side} / {position.quantity}</td>
              </tr>
              <tr>
                <td>Ortalama giriş</td>
                <td>{position.average_entry ?? "—"}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      {margin && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Notional</td>
                <td>{margin.notional}</td>
              </tr>
              <tr>
                <td>Gerekli başlangıç marjini</td>
                <td>{margin.required_initial_margin} {margin.reserve_asset}</td>
              </tr>
              <tr>
                <td>Kapasite</td>
                <td>{margin.capacity_status}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Lifecycle simülasyonu</h3>
      <label className="field">
        <span className="field-label">Olay listesi (JSON)</span>
        <textarea
          className="rebalance-textarea"
          aria-label="Olay listesi (JSON)"
          rows={3}
          value={eventsJson}
          onChange={(event) => setEventsJson(event.target.value)}
        />
      </label>
      <button className="secondary-button" type="button" disabled={busy || localBusy} onClick={() => void submitLifecycle()}>
        Lifecycle simüle et
      </button>
      {lifecycle && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Durum</td>
                <td>{lifecycle.status}</td>
              </tr>
              <tr>
                <td>Fill kimlikleri</td>
                <td>{lifecycle.fill_ids.join(", ") || "—"}</td>
              </tr>
              <tr>
                <td>Olay sayısı</td>
                <td>{lifecycle.event_count}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">İlke ve varyantlar</h3>
      <button className="secondary-button" type="button" disabled={busy || localBusy} onClick={() => void submitPolicy()}>
        İlke ve varyantlar
      </button>
      {variants && (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>Varyant</th>
                <th>Kabul</th>
                <th>Gerekçe</th>
              </tr>
            </thead>
            <tbody>
              {variants.map((row) => (
                <tr key={row.variant}>
                  <td>{row.variant}</td>
                  <td>{row.admission}</td>
                  <td>{row.reason}</td>
                </tr>
              ))}
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
