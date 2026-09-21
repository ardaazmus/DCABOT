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
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Paper session</td>
                <td>{dashboard.paper.sessions}</td>
              </tr>
              <tr>
                <td>Toplam paper nakit</td>
                <td>{dashboard.paper.total_cash}</td>
              </tr>
              <tr>
                <td>Pozisyon / açık emir</td>
                <td>
                  {dashboard.paper.positions} / {dashboard.paper.open_orders}
                </td>
              </tr>
              <tr>
                <td>Bot / bağlı session</td>
                <td>
                  {dashboard.bots.bots} / {dashboard.bots.bound_sessions}
                </td>
              </tr>
              <tr>
                <td>Deal</td>
                <td>{dashboard.deals.deals}</td>
              </tr>
              <tr>
                <td>Backup</td>
                <td>{dashboard.backups.backups}</td>
              </tr>
            </tbody>
          </table>
          <p className="paper-note">
            Salt-okunur toplama; değerleme ve venue verisi içermez.
          </p>
        </div>
      )}
    </section>
  );
}
