import { useState } from "react";

export type DealLifecycleView = {
  deal_id: string;
  config_revision_id: string;
  status: string;
  event_sequence: number;
};

export type DealEventView = {
  event_id: string;
  deal_id: string;
  config_revision_id: string;
  event: string;
  event_sequence: number;
};

export type DealCreatePayload = {
  deal_id: string;
  config_revision_id: string;
};

export type DealAppendPayload = {
  event_id: string;
  config_revision_id: string;
  event: string;
  event_sequence: number;
};

export type DealBulkAction = DealAppendPayload & {
  deal_id: string;
};

function isLifecycleOrNull(value: unknown): value is DealLifecycleView | null {
  if (value === null) return true;
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.deal_id === "string" &&
    typeof body.config_revision_id === "string" &&
    typeof body.status === "string" &&
    typeof body.event_sequence === "number"
  );
}

function isEventView(value: unknown): value is DealEventView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.event_id === "string" &&
    typeof body.deal_id === "string" &&
    typeof body.config_revision_id === "string" &&
    typeof body.event === "string" &&
    typeof body.event_sequence === "number"
  );
}

export function isDealReplayView(value: unknown): value is {
  deal_id: string;
  lifecycle: DealLifecycleView | null;
  history: DealEventView[];
} {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.deal_id === "string" &&
    isLifecycleOrNull(body.lifecycle) &&
    Array.isArray(body.history) &&
    (body.history as unknown[]).every(isEventView)
  );
}

export function DealPanel({
  dealId,
  lifecycle,
  history,
  bulkResults,
  busy,
  error,
  onCreate,
  onAppend,
  onReplay,
  onBulk,
}: {
  dealId: string;
  lifecycle: DealLifecycleView | null;
  history: DealEventView[];
  bulkResults: { deal_id: string; event_id: string; result?: string; error?: string }[];
  busy: boolean;
  error: string;
  onCreate: (payload: DealCreatePayload) => void;
  onAppend: (payload: DealAppendPayload) => void;
  onReplay: () => void;
  onBulk: (actions: DealBulkAction[]) => void;
}) {
  const [deal, setDeal] = useState(dealId);
  const [revision, setRevision] = useState("rev-1");
  const [eventId, setEventId] = useState("event-1");
  const [event, setEvent] = useState("START");
  const [sequence, setSequence] = useState("1");
  const [bulkDeals, setBulkDeals] = useState("deal-1, deal-2");
  const [formError, setFormError] = useState("");

  function submitCreate() {
    if (!deal.trim() || !revision.trim()) {
      setFormError("Deal ve revision kimliği boş olamaz.");
      return;
    }
    setFormError("");
    onCreate({ deal_id: deal.trim(), config_revision_id: revision.trim() });
  }

  function submitAppend() {
    const eventSequence = Number(sequence.trim());
    if (!eventId.trim() || !revision.trim()) {
      setFormError("Event ve revision kimliği boş olamaz.");
      return;
    }
    if (!Number.isInteger(eventSequence) || eventSequence < 1) {
      setFormError("Event sırası pozitif tam sayı olmalı.");
      return;
    }
    setFormError("");
    onAppend({
      event_id: eventId.trim(),
      config_revision_id: revision.trim(),
      event,
      event_sequence: eventSequence,
    });
  }

  function submitBulk() {
    const deals = bulkDeals
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    if (deals.length === 0 || !revision.trim()) {
      setFormError("En az bir deal ve revision kimliği gerekli.");
      return;
    }
    setFormError("");
    onBulk(
      deals.map((deal_id, index) => ({
        deal_id,
        event_id: `bulk-${index + 1}`,
        config_revision_id: revision.trim(),
        event,
        event_sequence: 1,
      })),
    );
  }

  return (
    <section className="panel rebalance-panel" aria-labelledby="deals-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">DEAL DESK</p>
          <h2 id="deals-title">Deal lifecycle ve toplu işlem</h2>
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

      <h3 className="paper-subheading">Deal</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Deal kimliği</span>
          <span className="input-wrap">
            <input aria-label="Deal kimliği" value={deal} onChange={(e) => setDeal(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Revision kimliği</span>
          <span className="input-wrap">
            <input aria-label="Revision kimliği" value={revision} onChange={(e) => setRevision(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitCreate}>
        Deal aç
      </button>
      <button className="secondary-button" type="button" disabled={busy} onClick={onReplay}>
        Replay
      </button>

      <h3 className="paper-subheading">Lifecycle olayı</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Event kimliği</span>
          <span className="input-wrap">
            <input aria-label="Event kimliği" value={eventId} onChange={(e) => setEventId(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Olay</span>
          <span className="input-wrap">
            <input aria-label="Olay" value={event} onChange={(e) => setEvent(e.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Sıra</span>
          <span className="input-wrap">
            <input aria-label="Sıra" value={sequence} onChange={(e) => setSequence(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitAppend}>
        Olay ekle
      </button>

      <h3 className="paper-subheading">Toplu işlem</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Deal listesi</span>
          <span className="input-wrap">
            <input aria-label="Deal listesi" value={bulkDeals} onChange={(e) => setBulkDeals(e.target.value)} />
          </span>
        </label>
      </div>
      <button className="secondary-button" type="button" disabled={busy} onClick={submitBulk}>
        Toplu gönder
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
                <td>Olay sayısı</td>
                <td>{history.length}</td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Config snapshot sunucu config&apos;inden alınır; toplu işlem atomik değildir, her deal sonucu ayrıdır.
          </p>
        </div>
      )}
      {bulkResults.length > 0 && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              {bulkResults.map((row) => (
                <tr key={`${row.deal_id}-${row.event_id}`}>
                  <td>{row.deal_id}</td>
                  <td>{row.result ?? row.error ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
