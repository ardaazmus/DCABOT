import { useState } from "react";
import { useI18n } from "./i18n";
import { SegmentedControl, TextParameter } from "./forms";

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

function LegCard({
  legId,
  status,
  quantity,
  eventTimeUs,
  busy,
  onFill,
  onError,
}: {
  legId: "A" | "B";
  status: string;
  quantity: string;
  eventTimeUs: string;
  busy: boolean;
  onFill: (payload: TwoLegFillPayload) => void;
  onError: (message: string) => void;
}) {
  const { t } = useI18n();
  const [fillId, setFillId] = useState("");
  const [qty, setQty] = useState("");
  const [side, setSide] = useState("LONG");
  const [fillStatus, setFillStatus] = useState("FULL");
  const heading = t(legId === "A" ? "twoleg.result.legA" : "twoleg.result.legB");

  function submit() {
    if (!fillId.trim() || !qty.trim()) {
      onError(t("twoleg.form.fillRequired"));
      return;
    }
    const eventTime = Number(eventTimeUs.trim());
    if (!Number.isInteger(eventTime) || eventTime < 0) {
      onError(t("twoleg.form.eventTimeInvalid"));
      return;
    }
    onError("");
    onFill({
      fill_id: fillId.trim(),
      leg_id: legId,
      account_id: "acct-1",
      venue_profile: "BINANCE-SPOT",
      product_id: "BTCUSDT",
      symbol: "BTCUSDT",
      hedge_side: side,
      quantity: qty.trim(),
      fill_status: fillStatus,
      event_time_us: eventTime,
    });
  }

  return (
    <section className="hedge-leg" role="group" aria-label={`${heading} ${t("twoleg.leg.card")}`}>
      <h3>{heading}</h3>
      <p className="hedge-leg-state">{`${t(`twoleg.legState.${status}`)} · ${quantity}`}</p>
      <div className="hedge-leg-form">
        <TextParameter label={t("twoleg.fill.id")} name={`hedge-fill-${legId}`} value={fillId} onChange={setFillId} />
        <TextParameter label={t("twoleg.qty.label")} name={`hedge-qty-${legId}`} value={qty} onChange={setQty} />
        <SegmentedControl
          label={t("twoleg.hedgeSide.label")}
          name={`hedge-side-${legId}`}
          value={side}
          options={[
            { value: "LONG", label: t("twoleg.hedgeSide.long") },
            { value: "SHORT", label: t("twoleg.hedgeSide.short") },
          ]}
          onChange={setSide}
        />
        <SegmentedControl
          label={t("twoleg.fillStatus.label")}
          name={`hedge-fillstatus-${legId}`}
          value={fillStatus}
          options={[
            { value: "FULL", label: t("twoleg.fillStatus.full") },
            { value: "PARTIAL", label: t("twoleg.fillStatus.partial") },
          ]}
          onChange={setFillStatus}
        />
        <button className="secondary-button" type="button" disabled={busy} onClick={submit}>
          {t("twoleg.fill.accept")}
        </button>
      </div>
    </section>
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
  const [eventTime, setEventTime] = useState("1000");
  const [formError, setFormError] = useState("");
  const { t } = useI18n();

  function submitStart() {
    if (!session.trim()) {
      setFormError(t("twoleg.form.sessionRequired"));
      return;
    }
    setFormError("");
    onStart(session.trim());
  }

  return (
    <section className="panel" aria-labelledby="twoleg-title">
      <div className="panel-heading">
        <div>
          <h2 id="twoleg-title">{t("twoleg.panel.title")}</h2>
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

      <div className="hedge-status-strip" data-testid="hedge-status-strip">
        <div>
          <span className="hedge-strip-label">{t("twoleg.result.state")}</span>
          <span className="hedge-strip-value">{projection?.state ?? ""}</span>
        </div>
        <div>
          <span className="hedge-strip-label">{t("twoleg.session.id")}</span>
          <span className="hedge-strip-value">{sessionId}</span>
        </div>
        <div>
          <span className="hedge-strip-label">{t("twoleg.result.fillCount")}</span>
          <span className="hedge-strip-value">{projection?.fills.length ?? 0}</span>
        </div>
      </div>

      <div className="hedge-levels">
        <span>{t("twoleg.sr.label")}</span>
        <span className="badge badge-closed">{t("badge.closed.label")}</span>
      </div>

      <div className="hedge-legs">
        <LegCard
          legId="A"
          status={projection?.leg_a_status ?? "NONE"}
          quantity={projection?.leg_a_quantity ?? "0"}
          eventTimeUs={eventTime}
          busy={busy}
          onFill={onFill}
          onError={setFormError}
        />
        <LegCard
          legId="B"
          status={projection?.leg_b_status ?? "NONE"}
          quantity={projection?.leg_b_quantity ?? "0"}
          eventTimeUs={eventTime}
          busy={busy}
          onFill={onFill}
          onError={setFormError}
        />
      </div>

      <div className="hedge-actions">
        <TextParameter label={t("twoleg.session.id")} name="hedge-session" value={session} onChange={setSession} />
        <TextParameter label={t("twoleg.eventTime.label")} name="hedge-event-time" value={eventTime} onChange={setEventTime} />
        <div className="hedge-buttons">
          <button className="secondary-button" type="button" disabled={busy} onClick={submitStart}>
            {t("twoleg.session.start")}
          </button>
          <button className="secondary-button" type="button" disabled={busy} onClick={onReplay}>
            {t("twoleg.session.replay")}
          </button>
          <button className="secondary-button" type="button" disabled={busy} onClick={onRecovery}>
            {t("twoleg.terminal.recovery")}
          </button>
          <button className="secondary-button" type="button" disabled={busy} onClick={onTimeout}>
            {t("twoleg.terminal.timeout")}
          </button>
        </div>
      </div>

      <p className="paper-note">{t("twoleg.integrity.note")}</p>
    </section>
  );
}
