import { useEffect, useRef, useState } from "react";

export type TimelineFrameView = {
  deal_id: string;
  step: number;
  of: number;
  lifecycle: {
    deal_id: string;
    config_revision_id: string;
    status: string;
    event_sequence: number;
  } | null;
  event: {
    event_id: string;
    deal_id: string;
    config_revision_id: string;
    event: string;
    event_sequence: number;
  } | null;
};

export function isTimelineFrameView(value: unknown): value is TimelineFrameView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  const lifecycle = body.lifecycle as Record<string, unknown> | null;
  const event = body.event as Record<string, unknown> | null;
  return (
    typeof body.deal_id === "string" &&
    typeof body.step === "number" &&
    typeof body.of === "number" &&
    (lifecycle === null ||
      (typeof lifecycle === "object" &&
        lifecycle !== null &&
        typeof lifecycle.status === "string")) &&
    (event === null ||
      (typeof event === "object" && event !== null && typeof event.event === "string"))
  );
}

export function TimelinePanel({
  frame,
  busy,
  error,
  onSeek,
}: {
  frame: TimelineFrameView | null;
  busy: boolean;
  error: string;
  onSeek: (step: number) => void;
}) {
  const [speed, setSpeed] = useState("0");
  const [playing, setPlaying] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (timer.current !== null) {
      window.clearInterval(timer.current);
      timer.current = null;
    }
    if (!playing || frame === null) return;
    const intervalMs = Number(speed);
    if (!Number.isFinite(intervalMs) || intervalMs <= 0) {
      setPlaying(false);
      return;
    }
    if (frame.step >= frame.of) {
      setPlaying(false);
      return;
    }
    timer.current = window.setInterval(() => onSeek(frame.step + 1), intervalMs);
    return () => {
      if (timer.current !== null) {
        window.clearInterval(timer.current);
        timer.current = null;
      }
    };
  }, [playing, speed, frame, onSeek]);

  const step = frame?.step ?? 0;
  const of = frame?.of ?? 0;

  return (
    <section className="panel rebalance-panel" aria-labelledby="timeline-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">TIME MACHINE</p>
          <h2 id="timeline-title">Deal zaman çizgisi</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      <div className="paper-order-form">
        {frame === null && (
          <button
            className="secondary-button"
            type="button"
            disabled={busy}
            onClick={() => onSeek(0)}
          >
            Çizgiyi yükle
          </button>
        )}
        <button
          className="secondary-button"
          type="button"
          disabled={busy || frame === null || step <= 0}
          onClick={() => onSeek(step - 1)}
        >
          Geri
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={busy || frame === null || step >= of}
          onClick={() => onSeek(step + 1)}
        >
          İleri
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={busy || frame === null || of <= 0}
          onClick={() => onSeek(0)}
        >
          Başa sar
        </button>
        <label className="field">
          <span className="field-label">Hız (ms/adım, 0=kapalı)</span>
          <span className="input-wrap">
            <input aria-label="Hız (ms/adım, 0=kapalı)" value={speed} onChange={(e) => setSpeed(e.target.value)} />
          </span>
        </label>
        <button
          className="secondary-button"
          type="button"
          disabled={busy || frame === null || playing}
          onClick={() => setPlaying(true)}
        >
          Oynat
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!playing}
          onClick={() => setPlaying(false)}
        >
          Durdur
        </button>
      </div>
      {frame && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Adım</td>
                <td>
                  {frame.step} / {frame.of}
                </td>
              </tr>
              <tr>
                <td>Durum</td>
                <td>{frame.lifecycle?.status ?? "—"}</td>
              </tr>
              <tr>
                <td>Olay</td>
                <td>{frame.event?.event ?? "—"}</td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Geçmiş ledger değişmez; geri sarma yalnızca görünümü kaydırır.
          </p>
        </div>
      )}
    </section>
  );
}
