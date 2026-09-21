import { useState } from "react";
import {
  SavedRunDetail,
  SavedRunListItem,
  SavedRunRecordHealth,
} from "./savedRuns";

type SavedRunsPanelProps = {
  view: "list" | "detail" | "compare";
  runs: SavedRunListItem[];
  listStatus: "idle" | "loading" | "ready" | "error";
  listError: string;
  detail: SavedRunDetail | null;
  detailStatus: "idle" | "loading" | "ready" | "error";
  detailError: string;
  onOpenDetail: (runId: string) => void;
  onBackToList: () => void;
  compareSelection: string[];
  onToggleCompareSelection: (runId: string) => void;
  onOpenCompare: () => void;
  compareDetails: [SavedRunDetail, SavedRunDetail] | null;
  compareStatus: "idle" | "loading" | "ready" | "error";
  compareError: string;
  onExportRun: (runId: string, format: "json" | "csv") => void;
  exportStatus: "idle" | "loading" | "ready" | "error";
  exportError: string;
};

const COMPARE_SUMMARY_ROWS: Array<{ key: string; label: string }> = [
  { key: "position_status", label: "Pozisyon durumu" },
  { key: "realized_gross", label: "Brüt gerçekleşen sonuç" },
  { key: "fees", label: "Toplam ücret" },
  { key: "realized_net_after_all_costs", label: "Net PnL" },
  { key: "equity", label: "Equity" },
  { key: "peak_equity", label: "Tepe equity" },
  { key: "max_drawdown", label: "Max drawdown" },
  { key: "action_count", label: "İşlem sayısı" },
  { key: "deal_count", label: "Deal sayısı" },
  { key: "completed_deal_count", label: "Tamamlanan deal" },
  { key: "average_entry_price", label: "Ortalama giriş" },
  { key: "time_in_position_us", label: "Pozisyonda kalma (µs)" },
];

function compareCellValue(detail: SavedRunDetail, key: string): string {
  const summary = detail.result_snapshot?.["summary"] as Record<string, unknown> | undefined;
  const value = summary?.[key];
  if (value === null || value === undefined) return "—";
  return String(value);
}

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

function SavedRunList({ runs, listStatus, listError, onOpenDetail, compareSelection, onToggleCompareSelection, onOpenCompare }: Pick<SavedRunsPanelProps, "runs" | "listStatus" | "listError" | "onOpenDetail" | "compareSelection" | "onToggleCompareSelection" | "onOpenCompare">) {
  const status = listStatus;
  const error = listError;
  return <section className="panel saved-runs-panel" aria-labelledby="saved-runs-title">
    <div className="panel-heading"><div><p className="eyebrow">SAVED RUNS</p><h2 id="saved-runs-title">Kaydedilmiş koşular</h2></div><span className={`catalog-state ${status}`}>{status === "loading" ? "Yükleniyor" : status === "error" ? "Hata" : `${runs.length} kayıt`}</span></div>
    <p className="catalog-intro">Yerel immutable historical run kayıtları salt okunur olarak açılır. Bu görünüm yeniden çalıştırma, düzenleme veya silme işlemi başlatmaz. Karşılaştırmak için iki koşu seçin.</p>
    {status === "loading" && <div className="catalog-empty" role="status">Kaydedilmiş koşular okunuyor…</div>}
    {status === "error" && <div className="form-error" role="alert">{error}</div>}
    {status === "ready" && runs.length === 0 && <div className="saved-runs-empty"><strong>Henüz kaydedilmiş koşu yok.</strong><p>Bir tarihsel koşu tamamlandığında veya belirsiz olarak durduğunda, sonuç kartındaki “Koşuyu kaydet” eylemiyle burada açabilirsiniz.</p></div>}
    {status === "ready" && runs.length > 0 && <div className="saved-runs-table-wrap"><table className="saved-runs-table"><caption className="sr-only">Kaydedilmiş tarihsel koşular</caption><thead><tr><th scope="col"><span className="sr-only">Karşılaştırma seçimi</span></th><th scope="col">Dataset / dönem</th><th scope="col">Durum</th><th scope="col">Kayıt sağlığı</th><th scope="col">İşlenen bar</th><th scope="col">Oluşturulma</th><th scope="col"><span className="sr-only">İşlem</span></th></tr></thead><tbody>{runs.map((run) => {
      const checked = compareSelection.includes(run.run_id);
      const disabled = run.record_health === "CORRUPT" || (!checked && compareSelection.length >= 2);
      return <tr key={run.run_id} className={checked ? "saved-run-row-selected" : undefined}>
      <td data-label="Karşılaştır"><label className="saved-run-compare-checkbox"><input type="checkbox" checked={checked} disabled={disabled} onChange={() => onToggleCompareSelection(run.run_id)} aria-label={`${run.symbol} ${run.created_at} koşusunu karşılaştırmak için seç`} /></label></td>
      <td data-label="Dataset / dönem"><div className="saved-run-primary"><strong>{run.symbol} · {run.interval}</strong><span>{run.period_start} → {run.period_end}</span><ShortId value={run.run_id} /><details className="saved-run-mobile-extra"><summary>Koşu ek bilgileri</summary><span>Pozisyon: {run.position_status === "OPEN_AT_END" ? "Dönem sonunda açık" : "Kapalı"}</span></details></div></td>
      <td data-label="Durum"><RunStatus status={run.execution_status} /></td>
      <td data-label="Kayıt sağlığı"><RecordHealth health={run.record_health} /></td>
      <td data-label="İşlenen bar"><code>{run.processed_bar_count.toLocaleString("tr-TR")}</code></td>
      <td data-label="Oluşturulma"><time dateTime={run.created_at}>{formatCreatedAt(run.created_at)}</time></td>
      <td data-label="İşlem"><button className="catalog-secondary-button saved-run-open-button" type="button" disabled={run.record_health === "CORRUPT"} onClick={() => onOpenDetail(run.run_id)}>{run.record_health === "CORRUPT" ? "Detail kapalı" : "Ayrıntıyı aç"}</button></td>
    </tr>;
    })}</tbody></table></div>}
    {status === "ready" && runs.length > 0 && <div className="saved-runs-compare-bar"><span>{compareSelection.length}/2 koşu seçildi</span><button className="catalog-secondary-button" type="button" disabled={compareSelection.length !== 2} onClick={onOpenCompare}>Karşılaştır</button></div>}
  </section>;
}

function SavedRunComparePanel({ compareDetails, compareStatus, compareError, onBackToList }: Pick<SavedRunsPanelProps, "compareDetails" | "compareStatus" | "compareError" | "onBackToList">) {
  if (compareStatus === "loading" || !compareDetails) return <section className="panel saved-runs-panel" aria-labelledby="saved-run-compare-title"><button className="saved-run-back-button" type="button" onClick={onBackToList}>← Saved Runs’a dön</button><div className="catalog-empty" role="status">{compareStatus === "error" ? <span className="form-error" role="alert">{compareError || "Karşılaştırma gösterilemedi."}</span> : "Karşılaştırılacak koşular okunuyor…"}</div></section>;

  const [first, second] = compareDetails;
  const resultMatches = first.result_sha256 === second.result_sha256;
  return <section className="panel saved-runs-panel saved-run-detail-panel" aria-labelledby="saved-run-compare-title">
    <button className="saved-run-back-button" type="button" onClick={onBackToList}>← Saved Runs’a dön</button>
    <div className="saved-run-detail-heading"><div><p className="eyebrow">READ-ONLY COMPARE</p><h2 id="saved-run-compare-title">İki koşuyu karşılaştır</h2><p className="saved-run-created">Değerler kayıtlı snapshot’lardan okunur; yeniden hesaplanmaz.</p></div></div>
    {resultMatches && <div className="saved-run-warning" role="note"><strong>✓ Aynı sonuç</strong><p>İki koşunun result hash’i birebir aynı — aynı hesaplamanın tekrar kaydıdır.</p></div>}
    <div className="saved-runs-table-wrap"><table className="saved-runs-table saved-runs-compare-table"><caption className="sr-only">Koşu karşılaştırma tablosu</caption>
      <thead><tr><th scope="col">Alan</th><th scope="col"><ShortId value={first.run_id} /><br /><time dateTime={first.created_at}>{formatCreatedAt(first.created_at)}</time></th><th scope="col"><ShortId value={second.run_id} /><br /><time dateTime={second.created_at}>{formatCreatedAt(second.created_at)}</time></th></tr></thead>
      <tbody>
        {COMPARE_SUMMARY_ROWS.map(({ key, label }) => {
          const a = compareCellValue(first, key);
          const b = compareCellValue(second, key);
          return <tr key={key} className={a !== b ? "saved-run-compare-diff" : undefined}><td data-label="Alan">{label}</td><td data-label="Koşu 1"><code>{a}</code></td><td data-label="Koşu 2"><code>{b}</code></td></tr>;
        })}
        <tr><td data-label="Alan">Result SHA-256</td><td data-label="Koşu 1"><ShortId value={first.result_sha256} /></td><td data-label="Koşu 2"><ShortId value={second.result_sha256} /></td></tr>
      </tbody>
    </table></div>
    <div className="saved-run-detail-boundary" role="note"><strong>Salt okunur karşılaştırma</strong><p>Bu ekran iki kayıtlı snapshot’ı yan yana gösterir; yeniden hesaplama, düzenleme veya birleştirme yapmaz.</p></div>
  </section>;
}

function SavedRunDetailPanel({ detail, detailStatus, detailError, onBackToList, onExportRun, exportStatus, exportError }: Pick<SavedRunsPanelProps, "detail" | "detailStatus" | "detailError" | "onBackToList" | "onExportRun" | "exportStatus" | "exportError">) {
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
    <div className="saved-run-export-bar"><span>Dışa aktar (salt-okunur kopya):</span><button className="catalog-secondary-button" type="button" disabled={exportStatus === "loading"} onClick={() => onExportRun(detail.run_id, "json")}>JSON indir</button><button className="catalog-secondary-button" type="button" disabled={exportStatus === "loading"} onClick={() => onExportRun(detail.run_id, "csv")}>CSV indir</button>{exportStatus === "loading" && <span role="status">Hazırlanıyor…</span>}{exportStatus === "error" && <span className="form-error" role="alert">{exportError || "Export hazırlanamadı."}</span>}</div>
    <div className="saved-run-detail-boundary" role="note"><strong>Salt okunur kayıt</strong><p>Bu ekranda finansal değerler yeniden hesaplanmaz; koşu düzenlenemez, yeniden çalıştırılamaz veya silinemez. Export, kaydın birebir kopyasıdır.</p></div>
  </section>;
}

export function SavedRunsPanel(props: SavedRunsPanelProps) {
  if (props.view === "list") return <SavedRunList {...props} />;
  if (props.view === "compare") return <SavedRunComparePanel compareDetails={props.compareDetails} compareStatus={props.compareStatus} compareError={props.compareError} onBackToList={props.onBackToList} />;
  return <SavedRunDetailPanel detail={props.detail} detailStatus={props.detailStatus} detailError={props.detailError} onBackToList={props.onBackToList} onExportRun={props.onExportRun} exportStatus={props.exportStatus} exportError={props.exportError} />;
}
