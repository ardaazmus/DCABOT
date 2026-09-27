import { useState } from "react";
import { shortSha256 } from "./datasetCatalog";
import type { TemplateMeta } from "./TemplatePanel";

/* Faz 17 AA.13a: preset-compare sekmesi (qwen sec-compare dizilimi).
 * `POST /api/presets/compare` — iki şablon AYNI datasette koşar; yanıtın her
 * iki tarafı da kayıtlı-koşu metrik-setinin aynısıdır (tek türetim, dördüncü
 * yeniden-hesap yok). UI YAN-YANA gösterir, fark/oran HESAPLAMAZ.
 * Onay disiplini TemplatePanel-bind emsali: tarafta checkbox → APPROVED,
 * yoksa PENDING (sunucu ikisini de kabul eder, karar onundur). */

export type PresetCompareSideRequest = {
  template_id: string;
  profile_id: string;
  allowed_capabilities: string[];
  approval: string;
};

export type PresetComparePayload = {
  a: PresetCompareSideRequest;
  b: PresetCompareSideRequest;
};

export type PresetCompareSide = {
  binding_id: string;
  profile_id: string;
  config_hash: string;
  execution_status: string;
  position_status: string;
  realized_net_after_all_costs: string;
  peak_equity: string;
  max_drawdown: string;
  deal_count: number;
  completed_deal_count: number;
  deal_pnls: string[];
  win_count: number;
  win_rate: string | null;
  profit_factor: string | null;
  roi: string | null;
  safety_order_fill_count: number;
  safety_order_fill_rate: string | null;
};

export type PresetCompareResult = {
  dataset_id: string;
  a: PresetCompareSide;
  b: PresetCompareSide;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isCount(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value);
}

function isRatio(value: unknown): value is string | null {
  return typeof value === "string" || value === null;
}

function isSide(value: unknown): value is PresetCompareSide {
  if (!isRecord(value)) return false;
  return typeof value.binding_id === "string"
    && typeof value.profile_id === "string"
    && typeof value.config_hash === "string"
    && typeof value.execution_status === "string"
    && typeof value.position_status === "string"
    && typeof value.realized_net_after_all_costs === "string"
    && typeof value.peak_equity === "string"
    && typeof value.max_drawdown === "string"
    && isCount(value.deal_count)
    && isCount(value.completed_deal_count)
    && Array.isArray(value.deal_pnls)
    && value.deal_pnls.every((entry) => typeof entry === "string")
    && isCount(value.win_count)
    && isRatio(value.win_rate)
    && isRatio(value.profit_factor)
    && isRatio(value.roi)
    && isCount(value.safety_order_fill_count)
    && isRatio(value.safety_order_fill_rate);
}

export function isPresetCompareResponse(value: unknown): value is { data: PresetCompareResult } {
  if (!isRecord(value)) return false;
  const data = value.data;
  if (!isRecord(data)) return false;
  return typeof data.dataset_id === "string" && isSide(data.a) && isSide(data.b);
}

const SIDE_ROWS: Array<{ key: keyof PresetCompareSide; label: string }> = [
  { key: "binding_id", label: "Binding" },
  { key: "profile_id", label: "Profil" },
  { key: "execution_status", label: "Durum" },
  { key: "position_status", label: "Pozisyon" },
  { key: "realized_net_after_all_costs", label: "Net" },
  { key: "peak_equity", label: "Tepe equity" },
  { key: "max_drawdown", label: "Maks. düşüş" },
  { key: "deal_count", label: "Deal" },
  { key: "completed_deal_count", label: "Tamamlanan" },
  { key: "win_count", label: "Kazanan" },
  { key: "win_rate", label: "Win rate" },
  { key: "profit_factor", label: "Profit factor" },
  { key: "roi", label: "ROI" },
  { key: "safety_order_fill_count", label: "SO dolum" },
  { key: "safety_order_fill_rate", label: "SO dolum oranı" },
];

function cellText(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" && Number.isInteger(value)) return String(value);
  return "—";
}

const DEAL_PNL_DISPLAY_CAP = 60;

type SideForm = { templateId: string; profileId: string; approved: boolean };

type PresetComparePanelProps = {
  datasetId: string | null;
  artifactSha256: string | null;
  templates: TemplateMeta[];
  busy: boolean;
  error: string;
  result: PresetCompareResult | null;
  onRun: (payload: PresetComparePayload) => void;
};

export function PresetComparePanel({
  datasetId,
  artifactSha256,
  templates,
  busy,
  error,
  result,
  onRun,
}: PresetComparePanelProps) {
  const [sideA, setSideA] = useState<SideForm>({ templateId: "", profileId: "paper", approved: false });
  const [sideB, setSideB] = useState<SideForm>({ templateId: "", profileId: "paper", approved: false });
  const [formError, setFormError] = useState("");
  const ready = datasetId !== null && artifactSha256 !== null && templates.length > 0 && !busy;

  function capsOf(templateId: string): string[] {
    return templates.find((meta) => meta.template_id === templateId)?.declared_capabilities ?? [];
  }

  function submit() {
    if (sideA.templateId === "" || sideB.templateId === "") {
      setFormError("İki taraf için de şablon seçin.");
      return;
    }
    if (sideA.templateId === sideB.templateId && sideA.profileId.trim() === sideB.profileId.trim()) {
      setFormError("A ve B aynı şablon+profil — karşılaştırma anlamsız (farklı taraf seçin).");
      return;
    }
    if (sideA.profileId.trim() === "" || sideB.profileId.trim() === "") {
      setFormError("Profil kimliği boş olamaz.");
      return;
    }
    setFormError("");
    const side = (form: SideForm): PresetCompareSideRequest => ({
      template_id: form.templateId,
      profile_id: form.profileId.trim(),
      allowed_capabilities: [...capsOf(form.templateId)],
      approval: form.approved ? "APPROVED" : "PENDING",
    });
    onRun({ a: side(sideA), b: side(sideB) });
  }

  function renderSideForm(legend: string, form: SideForm, setForm: (next: SideForm) => void) {
    const caps = form.templateId === "" ? [] : capsOf(form.templateId);
    return (
      <fieldset className="compare-side-form">
        <legend>{legend}</legend>
        <label className="field">
          <span className="field-label">Şablon</span>
          <span className="input-wrap">
            <select
              aria-label={`${legend} şablon`}
              value={form.templateId}
              onChange={(event) => setForm({ ...form, templateId: event.target.value })}
            >
              <option value="">Seçin…</option>
              {templates.map((meta) => <option key={meta.template_id} value={meta.template_id}>{meta.template_id}</option>)}
            </select>
          </span>
        </label>
        <label className="field">
          <span className="field-label">Profil</span>
          <span className="input-wrap">
            <input aria-label={`${legend} profil`} value={form.profileId} onChange={(event) => setForm({ ...form, profileId: event.target.value })} />
          </span>
        </label>
        <p className="helper-text">Kapabilite: {caps.length === 0 ? "—" : caps.join(", ")} (şablon-bildirimi, otomatik)</p>
        <label className="template-approval">
          <input
            type="checkbox"
            aria-label={`${legend} bağlamayı onaylıyorum`}
            checked={form.approved}
            onChange={(event) => setForm({ ...form, approved: event.target.checked })}
          />
          Bağlamayı onaylıyorum (APPROVED) — yoksa PENDING gönderilir
        </label>
      </fieldset>
    );
  }

  function renderDealPnls(side: PresetCompareSide, label: string) {
    const rows = side.deal_pnls;
    const shown = rows.slice(-DEAL_PNL_DISPLAY_CAP);
    const hidden = rows.length - shown.length;
    const firstNo = hidden + 1;
    if (rows.length === 0) {
      return <div className="empty-state" role="status">{label}: tamamlanan deal yok.</div>;
    }
    return (
      <>
        {hidden > 0 && <p className="helper-text" role="status">{label}: önceki {hidden} deal gizli — son {shown.length} gösteriliyor.</p>}
        <div className="table-wrap">
          <table>
            <caption className="sr-only">{label} kapanan deal net sonuçları</caption>
            <thead><tr><th scope="col">Deal</th><th scope="col">Net</th></tr></thead>
            <tbody>
              {shown.map((net, index) => <tr key={firstNo + index}><td><code>{firstNo + index}</code></td><td><code>{net}</code></td></tr>)}
            </tbody>
          </table>
        </div>
      </>
    );
  }

  return <section className="panel preset-compare-panel" aria-labelledby="preset-compare-title">
    <div className="panel-heading">
      <div>
        <p className="eyebrow">LAB · STRATEJİ KARŞILAŞTIRMA · AYNI VERİ</p>
        <h2 id="preset-compare-title">Preset compare</h2>
      </div>
      <span className="revision">{result === null ? "koşulmadı" : result.dataset_id}</span>
    </div>
    {(datasetId === null || artifactSha256 === null) && (
      <div className="empty-state" role="status">Dataset seçilmeden karşılaştırma koşulamaz — katalogdan seçin.</div>
    )}
    {datasetId !== null && artifactSha256 !== null && templates.length === 0 && (
      <div className="empty-state" role="status">Şablon listesi boş — önce şablon içe aktarın.</div>
    )}
    {datasetId !== null && artifactSha256 !== null && (
      <p className="helper-text">Dataset: {datasetId} · artifact: <code title={artifactSha256}>{shortSha256(artifactSha256)}</code></p>
    )}
    {renderSideForm("A tarafı", sideA, setSideA)}
    {renderSideForm("B tarafı", sideB, setSideB)}
    {formError && <div className="form-error" role="alert">{formError}</div>}
    {error && <div className="form-error" role="alert">{error}</div>}
    <button className="primary-button" type="button" disabled={!ready} onClick={submit}>
      {busy ? "Karşılaştırılıyor…" : "Karşılaştır"}
    </button>
    <p className="helper-text">İki taraf aynı datasette koşar; sonuçlar yan-yana dizilir, fark/oran hesaplanmaz.</p>
    {result !== null && (
      <>
        <p className="eyebrow">SONUÇLAR (A — B)</p>
        <div className="table-wrap">
          <table>
            <thead><tr><th scope="col">Metrik</th><th scope="col">A</th><th scope="col">B</th></tr></thead>
            <tbody>
              {SIDE_ROWS.map(({ key, label }) => (
                <tr key={key}>
                  <td>{label}</td>
                  <td><code>{cellText(result.a[key])}</code></td>
                  <td><code>{cellText(result.b[key])}</code></td>
                </tr>
              ))}
              <tr>
                <td>Config</td>
                <td title={result.a.config_hash}><code>{shortSha256(result.a.config_hash)}</code></td>
                <td title={result.b.config_hash}><code>{shortSha256(result.b.config_hash)}</code></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="eyebrow">DEAL PNL’LERİ (KAPANIŞ SIRASI)</p>
        {renderDealPnls(result.a, "A")}
        {renderDealPnls(result.b, "B")}
      </>
    )}
    <p className="paper-note">Onay PENDING de olabilir (sunucu kabul eder, bağlama kararını o verir). Kapabilite listesi şablon-bildiriminden otomatik alınır, elle yazılmaz.</p>
  </section>;
}
