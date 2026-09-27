/* Faz 17 AA.12: Sistem & Yedekler sekmesi sağlık-yoklaması (qwen
 * sec-deploy'un GERÇEK karşılığı — `GET /api/system/status`). Yalnız tek
 * yerel sürecin kendisi hakkında gözlemleyebildikleri: veri-dizini, disk,
 * yedek-sayacı. Yüzde/oran hesabı YOK (görüntü-disiplini); bayt ve zaman
 * damgası aynen gösterilir. */

export type SystemStatusView = {
  status: string;
  data_dir: { path: string; exists: boolean };
  disk: { free_bytes: number; total_bytes: number };
  backups: { count: number; latest_created_us: number | null };
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isDataDir(value: unknown): value is SystemStatusView["data_dir"] {
  return isRecord(value) && typeof value.path === "string" && typeof value.exists === "boolean";
}

function isDisk(value: unknown): value is SystemStatusView["disk"] {
  return isRecord(value) && typeof value.free_bytes === "number" && typeof value.total_bytes === "number";
}

function isBackups(value: unknown): value is SystemStatusView["backups"] {
  return isRecord(value) && typeof value.count === "number"
    && (typeof value.latest_created_us === "number" || value.latest_created_us === null);
}

export function isSystemStatusResponse(value: unknown): value is { data: SystemStatusView } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.status === "string"
    && isDataDir(data.data_dir)
    && isDisk(data.disk)
    && isBackups(data.backups);
}

function formatInstant(us: number): string {
  return new Date(us / 1000).toLocaleString("tr-TR");
}

type SystemStatusPanelProps = {
  status: SystemStatusView | null;
  busy: boolean;
  error: string;
  onRefresh: () => void;
};

export function SystemStatusPanel({ status, busy, error, onRefresh }: SystemStatusPanelProps) {
  return <section className="panel system-panel" aria-labelledby="system-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">SİSTEM · SAĞLIK</p>
        <h2 id="system-title">Sistem &amp; Yedekler</h2>
      </div>
      <span className="revision">{status === null ? (busy ? "okunuyor" : "bilinmiyor") : status.status}</span>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {status === null && !busy && error === "" && <div className="empty-state">Sağlık-yoklaması henüz yapılmadı.</div>}
    {status !== null && (
      <dl className="preflight-facts">
        <div><dt>Veri dizini</dt><dd><code>{status.data_dir.path}</code> {status.data_dir.exists ? "(var)" : "(YOK)"}</dd></div>
        <div><dt>Disk boş / toplam</dt><dd>{status.disk.free_bytes.toLocaleString("tr-TR")} / {status.disk.total_bytes.toLocaleString("tr-TR")} bayt</dd></div>
        <div><dt>Yedek sayısı</dt><dd>{status.backups.count}</dd></div>
        <div><dt>Son yedek</dt><dd>{status.backups.latest_created_us === null ? "yedek yok" : formatInstant(status.backups.latest_created_us)}</dd></div>
      </dl>
    )}
    <button className="primary-button" type="button" disabled={busy} onClick={onRefresh}>
      {busy ? "Okunuyor…" : "Yenile"}
    </button>
    <p className="paper-note">Bu yanıtın kendisi backend-up kanıtıdır. Yalnız yerel-gözlem; docker/servis-kartı/CPU-RAM bu ekranda bilinçli YOK.</p>
  </section>;
}
