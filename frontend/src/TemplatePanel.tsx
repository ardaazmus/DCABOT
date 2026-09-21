import { useState } from "react";

export type TemplateMeta = {
  template_id: string;
  payload_sha256: string;
  declared_capabilities: string[];
};

export type TemplateDetail = TemplateMeta & {
  payload: Record<string, unknown>;
};

export type TemplateBindResult = {
  binding_id: string;
  status: string;
  profile_id: string;
  params: [string, unknown][];
  config_hash: string;
};

export type TemplateDiffRow = { key: string; before: unknown; after: unknown };

export type TemplateImportPayload = {
  template_id: string;
  schema_version: string;
  payload: Record<string, unknown>;
  declared_capabilities: string[];
};

export type TemplateBindPayload = {
  profile_id: string;
  allowed_capabilities: string[];
  approval: string;
};

function isStringList(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

export function isTemplateDetail(value: unknown): value is TemplateDetail {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.template_id === "string" &&
    typeof body.payload_sha256 === "string" &&
    isStringList(body.declared_capabilities) &&
    typeof body.payload === "object" &&
    body.payload !== null &&
    !Array.isArray(body.payload)
  );
}

export function isTemplateMetaList(value: unknown): value is TemplateMeta[] {
  return (
    Array.isArray(value) &&
    value.every(
      (item: unknown) =>
        typeof item === "object" &&
        item !== null &&
        typeof (item as Record<string, unknown>).template_id === "string" &&
        typeof (item as Record<string, unknown>).payload_sha256 === "string" &&
        isStringList((item as Record<string, unknown>).declared_capabilities),
    )
  );
}

function isTemplateBinding(value: unknown): value is Omit<TemplateBindResult, "config_hash"> {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.binding_id === "string" &&
    typeof body.status === "string" &&
    typeof body.profile_id === "string" &&
    Array.isArray(body.params) &&
    body.params.every(
      (row: unknown) =>
        Array.isArray(row) && row.length === 2 && typeof row[0] === "string",
    )
  );
}

// The backend response splits the bind result across two keys: `binding`
// (identity/status/params) and `materialized` (the materialized config and
// its hash) -- see POST /api/templates/{id}/bind. This validates that shape
// and merges it into the flat TemplateBindResult the UI renders.
export function isTemplateBindResponse(
  value: unknown,
): value is { binding: Omit<TemplateBindResult, "config_hash">; materialized: { config_hash: string } } {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  const materialized = body.materialized;
  return (
    isTemplateBinding(body.binding) &&
    typeof materialized === "object" &&
    materialized !== null &&
    typeof (materialized as Record<string, unknown>).config_hash === "string"
  );
}

export function isTemplateDiffRows(value: unknown): value is TemplateDiffRow[] {
  return (
    Array.isArray(value) &&
    value.every(
      (row: unknown) =>
        typeof row === "object" &&
        row !== null &&
        typeof (row as Record<string, unknown>).key === "string" &&
        "before" in (row as Record<string, unknown>) &&
        "after" in (row as Record<string, unknown>),
    )
  );
}

export function TemplatePanel({
  templates,
  detail,
  bindResult,
  diffRows,
  busy,
  error,
  onImport,
  onSelect,
  onBind,
  onDiff,
}: {
  templates: TemplateMeta[];
  detail: TemplateDetail | null;
  bindResult: TemplateBindResult | null;
  diffRows: TemplateDiffRow[];
  busy: boolean;
  error: string;
  onImport: (payload: TemplateImportPayload) => void;
  onSelect: (templateId: string) => void;
  onBind: (templateId: string, payload: TemplateBindPayload) => void;
  onDiff: (firstId: string, secondId: string) => void;
}) {
  const [importId, setImportId] = useState("");
  const [importJson, setImportJson] = useState("");
  const [importCaps, setImportCaps] = useState("");
  const [importError, setImportError] = useState("");
  const [profileId, setProfileId] = useState("paper");
  const [approved, setApproved] = useState(false);
  const [diffSecond, setDiffSecond] = useState("");

  function submitImport() {
    let payload: unknown;
    try {
      payload = JSON.parse(importJson) as unknown;
    } catch {
      setImportError("Yük geçerli JSON değil.");
      return;
    }
    if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
      setImportError("Yük geçerli JSON değil.");
      return;
    }
    setImportError("");
    onImport({
      template_id: importId.trim(),
      schema_version: "strategy-template-v1",
      payload: payload as Record<string, unknown>,
      declared_capabilities: importCaps.split(/[,\s]+/).filter(Boolean),
    });
  }

  return (
    <section className="panel template-panel" aria-labelledby="template-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">STRATEGY TEMPLATES</p>
          <h2 id="template-title">Strateji şablonları</h2>
        </div>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}

      <h3 className="paper-subheading">Kayıtlı şablonlar</h3>
      {templates.length === 0 ? (
        <div className="empty-state">Henüz şablon yok; aşağıdan içe aktarın.</div>
      ) : (
        <div className="template-list">
          {templates.map((item) => (
            <button
              key={item.template_id}
              type="button"
              className={`catalog-secondary-button template-item${detail?.template_id === item.template_id ? " active" : ""}`}
              disabled={busy}
              onClick={() => onSelect(item.template_id)}
            >
              {item.template_id} · {item.declared_capabilities.join(",") || "—"}
            </button>
          ))}
        </div>
      )}

      {detail && (
        <>
          <h3 className="paper-subheading">Şablon detayı</h3>
          <pre className="template-payload">{JSON.stringify(detail.payload, null, 2)}</pre>
          <p className="helper-text">SHA-256: {detail.payload_sha256}</p>
        </>
      )}

      <h3 className="paper-subheading">İçe aktar</h3>
      <div className="template-form">
        <label className="field">
          <span className="field-label">Şablon ID</span>
          <span className="input-wrap">
            <input aria-label="Şablon ID" value={importId} onChange={(event) => setImportId(event.target.value)} />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Yük (JSON)</span>
          <textarea
            className="rebalance-textarea"
            aria-label="Yük (JSON)"
            rows={3}
            value={importJson}
            onChange={(event) => setImportJson(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="field-label">Kapabilite (virgülle)</span>
          <span className="input-wrap">
            <input aria-label="Kapabilite" value={importCaps} onChange={(event) => setImportCaps(event.target.value)} />
          </span>
        </label>
      </div>
      {importError && (
        <div className="form-error" role="alert">
          {importError}
        </div>
      )}
      <button className="secondary-button" type="button" disabled={busy} onClick={submitImport}>
        İçe aktar
      </button>

      <h3 className="paper-subheading">Profile bağla</h3>
      <div className="template-form">
        <label className="field">
          <span className="field-label">Profil</span>
          <span className="input-wrap">
            <input aria-label="Profil" value={profileId} onChange={(event) => setProfileId(event.target.value)} />
          </span>
        </label>
        <label className="template-approval">
          <input
            type="checkbox"
            aria-label="Bağlamayı onaylıyorum"
            checked={approved}
            onChange={(event) => setApproved(event.target.checked)}
          />
          Bağlamayı onaylıyorum — şablon yalnız strateji parametrelerini geçersiz kılar
        </label>
      </div>
      <button
        className="primary-button"
        type="button"
        disabled={busy || !detail || !approved}
        onClick={() =>
          detail &&
          onBind(detail.template_id, {
            profile_id: profileId.trim(),
            allowed_capabilities: detail.declared_capabilities,
            approval: "APPROVED",
          })
        }
      >
        Profile bağla
      </button>
      {bindResult && (
        <div className="table-wrap paper-result">
          <table>
            <tbody>
              <tr>
                <td>Durum</td>
                <td>{bindResult.status}</td>
              </tr>
              <tr>
                <td>Bağlama ID</td>
                <td>{bindResult.binding_id}</td>
              </tr>
              <tr>
                <td>Config hash</td>
                <td>{bindResult.config_hash}</td>
              </tr>
              {bindResult.params.map(([key, value]) => (
                <tr key={key}>
                  <td>{key}</td>
                  <td>{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Karşılaştır</h3>
      <div className="template-form">
        <label className="field">
          <span className="field-label">İkinci şablon</span>
          <span className="input-wrap">
            <input aria-label="İkinci şablon" value={diffSecond} onChange={(event) => setDiffSecond(event.target.value)} />
          </span>
        </label>
      </div>
      <button
        className="secondary-button"
        type="button"
        disabled={busy || !detail || !diffSecond.trim()}
        onClick={() => detail && onDiff(detail.template_id, diffSecond.trim())}
      >
        Karşılaştır
      </button>
      {diffRows.length > 0 && (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>Anahtar</th>
                <th>Önce</th>
                <th>Sonra</th>
              </tr>
            </thead>
            <tbody>
              {diffRows.map((row) => (
                <tr key={row.key}>
                  <td>{row.key}</td>
                  <td>{row.before === null || row.before === undefined ? "—" : String(row.before)}</td>
                  <td>{row.after === null || row.after === undefined ? "—" : String(row.after)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="table-note">
        <span className="note-icon">↳</span> Şablon içe aktarma tek başına yetkisiz aktivasyon yapmaz; bağlama açık onay ve kapabilite kontrolü ister.
      </div>
    </section>
  );
}
