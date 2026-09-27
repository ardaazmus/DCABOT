import { Badge } from "./Badge";
import type { DealEventView, DealLifecycleView } from "./DealPanel";

/**
 * Faz 17 A.4: tam sayfa deal detay (qwen `sec-dealdetail`) — popup YOK.
 * Lifecycle + olay geçmişi backend replay'inden gelir. Bilinçli eksikler
 * (backend karşılığı yok, uydurulmadı): fiyat grafiği (deal olaylarında
 * fiyat/zaman yok), Fon Ekle/Panic Sell (emir yetkisi gerektirir), hızlı
 * geçiş şeridi (deal listesi endpoint'i yok), bağlı bot (deal↔bot bağı yok).
 */
export function DealDetailView({
  dealId,
  lifecycle,
  history,
  replayVerified,
  busy,
  error,
  onBack,
  onReplay,
}: {
  dealId: string;
  lifecycle: DealLifecycleView | null;
  history: DealEventView[];
  replayVerified: boolean;
  busy: boolean;
  error: string;
  onBack: () => void;
  onReplay: () => void;
}) {
  const loaded = lifecycle !== null && lifecycle.deal_id === dealId;
  return (
    <section className="bot-create-view" aria-labelledby="deal-detail-title">
      <div className="bot-create-head">
        <button className="secondary-button" type="button" onClick={onBack}>
          ← Deal Desk
        </button>
        <h2 id="deal-detail-title">{dealId}</h2>
        {loaded && (lifecycle.status === "UNKNOWN" ? (
          <Badge tone="warn" label="UNKNOWN — inceleniyor" />
        ) : (
          <span className="state-label">{lifecycle.status}</span>
        ))}
        {replayVerified && <Badge tone="ok" label="Replay Doğrulandı ✓" />}
        <span className="state-label">{history.length} olay</span>
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {loaded ? (
        <dl className="binance-snapshot-facts">
          <div><dt>Deal</dt><dd>{lifecycle.deal_id}</dd></div>
          <div><dt>Revision</dt><dd>{lifecycle.config_revision_id}</dd></div>
          <div><dt>Durum</dt><dd>{lifecycle.status}</dd></div>
          <div><dt>Sıra</dt><dd>{lifecycle.event_sequence}</dd></div>
        </dl>
      ) : (
        <p className="helper-text" role="status">{busy ? "Deal yükleniyor…" : "Deal lifecycle alınamadı."}</p>
      )}
      <section className="panel" aria-labelledby="deal-detail-history-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">GEÇMİŞ</p>
            <h2 id="deal-detail-history-title">Olay geçmişi</h2>
          </div>
          <button className="secondary-button" type="button" disabled={busy} onClick={onReplay}>
            Replay
          </button>
        </div>
        {history.length === 0 ? (
          <p className="helper-text">Olay yok — Replay ile yükleyin.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Sıra</th><th>Olay</th><th>Event</th><th>Revision</th></tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.event_id}>
                    <td>{entry.event_sequence}</td>
                    <td>{entry.event}</td>
                    <td>{entry.event_id}</td>
                    <td>{entry.config_revision_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}
