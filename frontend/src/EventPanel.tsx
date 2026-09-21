export type CenterEventView = {
  seq: number;
  kind: string;
  ref: string;
  summary: string;
  time_us: number;
};

export function isCenterEventList(value: unknown): value is CenterEventView[] {
  if (!Array.isArray(value)) return false;
  return (value as unknown[]).every((entry) => {
    if (typeof entry !== "object" || entry === null) return false;
    const body = entry as Record<string, unknown>;
    return (
      typeof body.seq === "number" &&
      typeof body.kind === "string" &&
      typeof body.ref === "string" &&
      typeof body.summary === "string" &&
      typeof body.time_us === "number"
    );
  });
}

export function EventPanel({
  events,
  busy,
  error,
  onRefresh,
}: {
  events: CenterEventView[];
  busy: boolean;
  error: string;
  onRefresh: () => void;
}) {
  return (
    <section className="panel rebalance-panel" aria-labelledby="events-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">EVENT CENTER</p>
          <h2 id="events-title">Olay merkezi</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        Olayları yenile
      </button>
      {events.length > 0 && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              {events.map((event) => (
                <tr key={event.seq}>
                  <td>
                    #{event.seq} {event.kind}
                  </td>
                  <td>
                    {event.ref}: {event.summary}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="paper-note">
            Yerel kanal; dış bildirim adaptörleri kapsam dışı.
          </p>
        </div>
      )}
    </section>
  );
}
