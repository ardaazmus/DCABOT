import { useState } from "react";

export type BackupManifestView = {
  store: string;
  backup_file: string;
  manifest_file: string;
  bytes: number;
  sha256: string;
  created_us: number;
};

export type BackupVerdictView = {
  backup_file: string;
  verdict: string;
  reason?: string;
  application_id?: number;
  user_version?: number;
};

export function isBackupManifestList(value: unknown): value is BackupManifestView[] {
  if (!Array.isArray(value)) return false;
  return (value as unknown[]).every((entry) => {
    if (typeof entry !== "object" || entry === null) return false;
    const body = entry as Record<string, unknown>;
    return (
      typeof body.store === "string" &&
      typeof body.backup_file === "string" &&
      typeof body.manifest_file === "string" &&
      typeof body.bytes === "number" &&
      typeof body.sha256 === "string" &&
      typeof body.created_us === "number"
    );
  });
}

export function isBackupVerdictView(value: unknown): value is BackupVerdictView {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return typeof body.backup_file === "string" && typeof body.verdict === "string";
}

export function BackupPanel({
  backups,
  verdict,
  busy,
  error,
  onTake,
  onVerify,
  onRefresh,
}: {
  backups: BackupManifestView[];
  verdict: BackupVerdictView | null;
  busy: boolean;
  error: string;
  onTake: (store: string) => void;
  onVerify: (backupFile: string) => void;
  onRefresh: () => void;
}) {
  const [store, setStore] = useState("historical_runs");
  const [backupFile, setBackupFile] = useState("");
  const [formError, setFormError] = useState("");

  return (
    <section className="panel rebalance-panel" aria-labelledby="backup-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">ADMIN</p>
          <h2 id="backup-title">Backup ve doğrulama</h2>
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

      <h3 className="paper-subheading">Backup al</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Store</span>
          <span className="input-wrap">
            <input aria-label="Store" value={store} onChange={(e) => setStore(e.target.value)} />
          </span>
        </label>
      </div>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => {
          if (!store.trim()) {
            setFormError("Store adı boş olamaz.");
            return;
          }
          setFormError("");
          onTake(store.trim());
        }}
      >
        Backup al
      </button>
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        Listeyi yenile
      </button>

      <h3 className="paper-subheading">Doğrula (geri yüklemez)</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Backup dosyası</span>
          <span className="input-wrap">
            <input aria-label="Backup dosyası" value={backupFile} onChange={(e) => setBackupFile(e.target.value)} />
          </span>
        </label>
      </div>
      <button
        className="secondary-button"
        type="button"
        disabled={busy}
        onClick={() => {
          if (!backupFile.trim()) {
            setFormError("Backup dosyası boş olamaz.");
            return;
          }
          setFormError("");
          onVerify(backupFile.trim());
        }}
      >
        Doğrula
      </button>

      {backups.length > 0 && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              {backups.map((entry) => (
                <tr key={entry.manifest_file}>
                  <td>{entry.backup_file}</td>
                  <td>{entry.bytes} B</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="paper-note">
            Restore otomatik değildir: VERIFIED dosya, sunucu kapalıyken operatör tarafından kopyalanır.
          </p>
        </div>
      )}
      {verdict && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Karar</td>
                <td>
                  {verdict.backup_file}: {verdict.verdict}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
