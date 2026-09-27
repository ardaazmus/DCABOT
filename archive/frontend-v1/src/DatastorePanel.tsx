import { useState } from "react";
import {
  formatDatasetBytes,
  shortSha256,
  type DatasetCatalogStatus,
  type DatasetDownloadJob,
  type DatasetSummary,
} from "./datasetCatalog";

/* Faz 17 AA.6: veri-deposu manifestosu (qwen sec-datastore "Manifesto"
 * düğmesinin GERÇEK karşılığı). Parquet-script ÜRETİLMEZ (plan kapsam-
 * dışı); bunun yerine DCABOT'un artifact+hash manifestosu dizilir:
 * dataset kimliği + sha256 + bayt + doğrulama-durumu + aktif indirme-
 * işi. Tüm alanlar katalog/iş yanıtlarından aynen; kopyalama salt
 * metin-birleştirmedir (hesap yok). Sıfır-backend: yeni fetch YOK. */

export function manifestText(dataset: DatasetSummary): string {
  return [
    `dataset_id: ${dataset.dataset_id}`,
    `instrument: ${dataset.instrument}`,
    `interval: ${dataset.interval}`,
    `period: ${dataset.period_start} → ${dataset.period_end}`,
    `status: ${dataset.status}`,
    `artifact_sha256: ${dataset.artifact?.sha256 ?? "—"}`,
    `byte_size: ${dataset.artifact ? String(dataset.artifact.byte_size) : "—"}`,
  ].join("\n");
}

function ManifestRow({ dataset }: { dataset: DatasetSummary }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    if (!navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(manifestText(dataset));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <tr>
      <td data-label="Dataset"><code title={dataset.dataset_id}>{dataset.dataset_id}</code><br />{dataset.instrument} {dataset.interval}</td>
      <td data-label="Dönem">{dataset.period_start} → {dataset.period_end}</td>
      <td data-label="Durum">{dataset.status}</td>
      <td data-label="Artifact">{dataset.artifact ? <code title={dataset.artifact.sha256}>{shortSha256(dataset.artifact.sha256)} · {formatDatasetBytes(dataset.artifact.byte_size)}</code> : "—"}</td>
      <td data-label="Manifesto">
        <button className="catalog-secondary-button" type="button" onClick={() => void copy()} disabled={!navigator.clipboard}>
          {copied ? "Kopyalandı" : "Manifesto"}
        </button>
      </td>
    </tr>
  );
}

type DatastorePanelProps = {
  datasets: DatasetSummary[];
  status: DatasetCatalogStatus;
  error: string;
  activeJob: DatasetDownloadJob | null;
};

export function DatastorePanel({ datasets, status, error, activeJob }: DatastorePanelProps) {
  return <section className="panel datastore-panel" aria-labelledby="datastore-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">VERİ DEPOSU · ARTIFACT+MANIFESTO</p>
        <h2 id="datastore-title">Datastore manifestosu</h2>
      </div>
      <span className={`catalog-state ${status}`}>{status === "pending" ? "Yükleniyor" : status === "error" ? "Hata" : `${datasets.length} tanım`}</span>
    </div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {activeJob !== null && (
      <p className="helper-text" role="status">Aktif indirme-işi: <code>{activeJob.job_id}</code> · {activeJob.dataset_id} · {activeJob.status} · deneme {activeJob.attempt}/{activeJob.max_attempts}</p>
    )}
    {status !== "ready" && error === "" && <div className="empty-state" role="status">Katalog bekleniyor.</div>}
    {status === "ready" && datasets.length === 0 && <div className="empty-state" role="status">Kayıtlı dataset tanımı yok.</div>}
    {status === "ready" && datasets.length > 0 && (
      <div className="table-wrap">
        <table>
          <caption className="sr-only">Dataset artifact manifestosu</caption>
          <thead>
            <tr>
              <th scope="col">Dataset</th>
              <th scope="col">Dönem</th>
              <th scope="col">Durum</th>
              <th scope="col">Artifact</th>
              <th scope="col">Manifesto</th>
            </tr>
          </thead>
          <tbody>
            {datasets.map((dataset) => <ManifestRow key={dataset.dataset_id} dataset={dataset} />)}
          </tbody>
        </table>
      </div>
    )}
    <p className="paper-note">Parquet indirme-scripti bu ekranda YOK (bilinçli kapsam-dışı); indirme yalnız katalogdaki gerçek iş-akışıyla yapılır.</p>
  </section>;
}
