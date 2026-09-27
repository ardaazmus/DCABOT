export type DashboardView = {
  paper: {
    sessions: number;
    total_cash: string;
    positions: number;
    open_orders: number;
  };
  bots: {
    bots: number;
    bound_sessions: number;
  };
  deals: {
    deals: number;
    by_status: Record<string, number>;
  };
  backups: {
    backups: number;
  };
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isDashboardView(value: unknown): value is DashboardView {
  if (!isRecord(value)) return false;
  const paper = value.paper;
  const bots = value.bots;
  const deals = value.deals;
  const backups = value.backups;
  return (
    isRecord(paper) &&
    typeof paper.sessions === "number" &&
    typeof paper.total_cash === "string" &&
    typeof paper.positions === "number" &&
    typeof paper.open_orders === "number" &&
    isRecord(bots) &&
    typeof bots.bots === "number" &&
    typeof bots.bound_sessions === "number" &&
    isRecord(deals) &&
    typeof deals.deals === "number" &&
    isRecord(deals.by_status) &&
    isRecord(backups) &&
    typeof backups.backups === "number"
  );
}

/* AA.2a: durum-dağılımı salt-metin birleştirme (hesap yok). */
function formatByStatus(byStatus: Record<string, number>): string {
  const entries = Object.entries(byStatus);
  if (entries.length === 0) return "durum dağılımı yok";
  return entries.map(([status, count]) => `${status}: ${count}`).join(" · ");
}

export function DashboardPanel({
  dashboard,
  busy,
  error,
  onRefresh,
}: {
  dashboard: DashboardView | null;
  busy: boolean;
  error: string;
  onRefresh: () => void;
}) {
  return (
    <section className="panel rebalance-panel" aria-labelledby="dashboard-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">OVERVIEW</p>
          <h2 id="dashboard-title">Portföy özeti</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        Özeti yenile
      </button>
      {dashboard && (
        <>
          <div className="quality-summary" role="list" aria-label="Portföy özeti kartları">
            <div className="metric" role="listitem">
              <span className="metric-label">Paper Nakit</span>
              <strong>{dashboard.paper.total_cash}</strong>
              <span className="metric-unit">{dashboard.paper.sessions} session · salt-okunur</span>
            </div>
            <div className="metric" role="listitem">
              <span className="metric-label">Pozisyon / Açık Emir</span>
              <strong>{dashboard.paper.positions} / {dashboard.paper.open_orders}</strong>
              <span className="metric-unit">paper</span>
            </div>
            <div className="metric" role="listitem">
              <span className="metric-label">Bot / Bağlı Session</span>
              <strong>{dashboard.bots.bots} / {dashboard.bots.bound_sessions}</strong>
              <span className="metric-unit">kayıtlı</span>
            </div>
            <div className="metric" role="listitem">
              <span className="metric-label">Deal</span>
              <strong>{dashboard.deals.deals}</strong>
              <span className="metric-unit">{formatByStatus(dashboard.deals.by_status)}</span>
            </div>
          </div>
          <p className="paper-note" role="status">
            Değerleme kartları (yatırılan · uPnL · bugünkü kâr): portföy-özet
            ucu bekleniyor (AA.-1). Salt-okunur toplama; değerleme ve venue
            verisi içermez.
          </p>
        </>
      )}
    </section>
  );
}
