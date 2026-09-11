import { useState } from "react";
import {
  SavedRunDetail,
  SavedRunListItem,
  SavedRunRecordHealth,
} from "./savedRuns";

type SavedRunsPanelProps = {
  view: "list" | "detail";
  runs: SavedRunListItem[];
  listStatus: "idle" | "loading" | "ready" | "error";
  listError: string;
  detail: SavedRunDetail | null;
  detailStatus: "idle" | "loading" | "ready" | "error";
  detailError: string;
  onOpenDetail: (runId: string) => void;
  onBackToList: () => void;
};

function statusMeta(status: SavedRunListItem["execution_status"]): { icon: string; label: string; className: string } {
  return status === "COMPLETED"
    ? { icon: "·", label: "Tamamlandı", className: "completed" }
    : { icon: "!", label: "Belirsiz", className: "indeterminate" };
}

function healthMeta(health: SavedRunRecordHealth): { icon: string; label: string; className: string } {
  return health === "OK"
    ? { icon: "✓", label: "Kayıt doğrulandı", className: "ok" }
    : { icon: "!", label: "Bozuk kayıt", className: "corrupt" };
}

function formatCreatedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("tr-TR", { dateStyle: "short", timeStyle: "short" });
}

function ShortId({ value }: { value: string }) {
  return <code className="saved-run-short-id" title={value}>{value.slice(0, 8)}…</code>;
}

function CopyValue({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return <div className="saved-run-copy-row"><code>{value}</code><button className="saved-run-copy-button" type="button" onClick={() => void copy()} disabled={!navigator.clipboard}>{copied ? "Kopyalandı" : label}</button></div>;
}

function JsonEvidence({ label, value }: { label: string; value: Record<string, unknown> }) {
  return <details className="saved-run-evidence-section"><summary>{label}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}

function RunStatus({ status }: { status: SavedRunListItem["execution_status"] }) {
  const meta = statusMeta(status);
  return <span className={`saved-run-status ${meta.className}`}><span aria-hidden="true">{meta.icon}</span>{meta.label}</span>;
}

function RecordHealth({ health }: { health: SavedRunRecordHealth }) {
  const meta = healthMeta(health);
  return <span className={`saved-run-health ${meta.className}`}><span aria-hidden="true">{meta.icon}</span>{meta.label}</span>;
}

function SavedRunList({ runs, listStatus, listError, onOpenDetail }: Pick<SavedRunsPanelProps, "runs" | "listStatus" | "listError" | "onOpenDetail">) {
  const status = listStatus;
  const error = listError;
  return <section className="panel saved-runs-panel" aria-labelledby="saved-runs-title">
    <div className="panel-heading"><div><p className="eyebrow">SAVED RUNS</p><h2 id="saved-runs-title">Kaydedilmiş koşular</h2></div><span className={`catalog-state ${status}`}>{status === "loading" ? "Yükleniyor" : status === "error" ? "Hata" : `${runs.length} kayıt`}</span></div>
    <p className="catalog-intro">Yerel immutable historical run kayıtları salt okunur olarak açılır. Bu görünüm yeniden çalıştırma, düzenleme veya silme işlemi başlatmaz.</p>
    {status === "loading" && <div className="catalog-empty" role="status">Kaydedilmiş koşular okunuyor…</div>}
    {status === "error" && <div className="form-error" role="alert">{error}</div>}
    {status === "ready" && runs.length === 0 && <div className="saved-runs-empty"><strong>Henüz kaydedilmiş koşu yok.</strong><p>Bir tarihsel koşu tamamlandığında veya belirsiz olarak durduğunda, sonuç kartındaki “Koşuyu kaydet” eylemiyle burada açabilirsiniz.</p></div>}
    {status === "ready" && runs.length > 0 && <div className="saved-runs-table-wrap"><table className="saved-runs-table"><caption className="sr-only">Kaydedilmiş tarihsel koşular</caption><thead><tr><th scope="col">Dataset / dönem</th><th scope="col">Durum</th><th scope="col">Kayıt sağlığı</th><th scope="col">İşlenen bar</th><th scope="col">Oluşturulma</th><th scope="col"><span className="sr-only">İşlem</span></th></tr></thead><tbody>{runs.map((run) => <tr key={run.run_id}>
      <td data-label="Dataset / dönem"><div className="saved-run-primary"><strong>{run.symbol} · {run.interval}</strong><span>{run.period_start} → {run.period_end}</span><ShortId value={run.run_id} /><details className="saved-run-mobile-extra"><summary>Koşu ek bilgileri</summary><span>Pozisyon: {run.position_status === "OPEN_AT_END" ? "Dönem sonunda açık" : "Kapalı"}</span></details></div></td>
      <td data-label="Durum"><RunStatus status={run.execution_status} /></td>
      <td data-label="Kayıt sağlığı"><RecordHealth health={run.record_health} /></td>
      <td data-label="İşlenen bar"><code>{run.processed_bar_count.toLocaleString("tr-TR")}</code></td>
      <td data-label="Oluşturulma"><time dateTime={run.created_at}>{formatCreatedAt(run.created_at)}</time></td>
      <td data-label="İşlem"><button className="catalog-secondary-button saved-run-open-button" type="button" disabled={run.record_health === "CORRUPT"} onClick={() => onOpenDetail(run.run_id)}>{run.record_health === "CORRUPT" ? "Detail kapalı" : "Ayrıntıyı aç"}</button></td>
    </tr>)}</tbody></table></div>}
  </section>;
}

function SavedRunDetailPanel({ detail, detailStatus, detailError, onBackToList }: Pick<SavedRunsPanelProps, "detail" | "detailStatus" | "detailError" | "onBackToList">) {
  if (detailStatus === "loading") return <section className="panel saved-runs-panel" aria-labelledby="saved-run-detail-title"><button className="saved-run-back-button" type="button" onClick={onBackToList}>← Saved Runs’a dön</button><div className="catalog-empty" role="status">Koşu ayrıntısı okunuyor…</div></section>;
  if (detailStatus === "error" || !detail) return <section className="panel saved-runs-panel" aria-labelledby="saved-run-detail-title"><button className="saved-run-back-button" type="button" onClick={onBackToList}>← Saved Runs’a dön</button><div className="form-error" role="alert">{detailError || "Koşu ayrıntısı gösterilemedi."}</div></section>;

  const status = statusMeta(detail.execution_status);
  return <section className="panel saved-runs-panel saved-run-detail-panel" aria-labelledby="saved-run-detail-title">
    <button className="saved-run-back-button" type="button" onClick={onBackToList}>← Saved Runs’a dön</button>
    <div className="saved-run-detail-heading"><div><p className="eyebrow">READ-ONLY HISTORICAL RUN</p><h2 id="saved-run-detail-title">Koşu ayrıntısı</h2><p className="saved-run-created">{formatCreatedAt(detail.created_at)} · <code>{detail.run_id}</code></p></div><div className="saved-run-detail-status"><span className={`saved-run-status ${status.className}`}><span aria-hidden="true">{status.icon}</span>{status.label}</span><span className="saved-run-storage"><span aria-hidden="true">✓</span> Yerel kayıt saklandı</span></div></div>
    {detail.execution_status === "INDETERMINATE" && <div className="saved-run-warning" role="note"><strong>! Belirsiz sonuç</strong><p>Bu kayıt kesin ekonomik sonuç olarak yorumlanmamalıdır. Belirsizlik kanıtları ve snapshot’lar değişmeden saklanır.</p></div>}
    <div className="saved-run-detail-grid">
      <div className="saved-run-detail-card"><p className="preflight-section-label">DATASET EVIDENCE</p><dl className="saved-run-facts">{Object.entries(detail.dataset).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl></div>
      <div className="saved-run-detail-card"><p className="preflight-section-label">EXECUTION IDENTITY</p><dl className="saved-run-facts">{Object.entries(detail.execution).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl></div>
    </div>
    <div className="saved-run-detail-sections">
      <JsonEvidence label="Girdi snapshot’ı" value={detail.input_snapshot} />
      <JsonEvidence label="Config snapshot’ı" value={detail.config} />
      <JsonEvidence label="Enstrüman ve risk snapshot’ı" value={detail.instrument_risk} />
      <JsonEvidence label="Sonuç ve belirsizlik snapshot’ı" value={detail.result_snapshot} />
      <details className="saved-run-evidence-section"><summary>Bütünlük hash’leri</summary><div className="saved-run-integrity"><div><span>Result SHA-256</span><CopyValue label="Kopyala" value={detail.result_sha256} /></div><div><span>Record SHA-256</span><CopyValue label="Kopyala" value={detail.record_sha256} /></div></div></details>
    </div>
    <div className="saved-run-detail-boundary" role="note"><strong>Salt okunur kayıt</strong><p>Bu ekranda finansal değerler yeniden hesaplanmaz; koşu düzenlenemez, yeniden çalıştırılamaz, silinemez veya dışa aktarılamaz.</p></div>
  </section>;
}

export function SavedRunsPanel(props: SavedRunsPanelProps) {
  return props.view === "list"
    ? <SavedRunList {...props} />
    : <SavedRunDetailPanel detail={props.detail} detailStatus={props.detailStatus} detailError={props.detailError} onBackToList={props.onBackToList} />;
}
