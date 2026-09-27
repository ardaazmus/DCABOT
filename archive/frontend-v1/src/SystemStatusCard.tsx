import type { DatasetSummary } from "./datasetCatalog";
import type { DashboardView } from "./DashboardPanel";
import type { CanaryStatusView } from "./RiskPanel";

// AA.1 (=sec-status): Genel Bakış'taki "Durum & Veri Kaynağı" kartı.
// Qwen'in Sistem Özeti panel-dilini (başlık + mini-kartlar) DCABOT'un GERÇEK
// durumuyla doldurur: yerel API bağlantısı, dataset kataloğu sayımı, güvenlik
// (canary/kill-switch), bot/deal sayaçları (dashboard), bağlantı modu
// (capabilities). Yeni endpoint yok (3 uç da mevcut); sayı uydurulmaz,
// hesap yok. Halka GÖRSEL durum rozetidir (kesikli-eşik yok, oran YOK);
// sayaçlar statiktir (animasyonsuz), yükleniyor-halkası `prefers-reduced-
// motion` saygılıdır (styles.css). Roadmap-kartları bilinçli YOK.

export type SystemApiStatus = "unknown" | "loading" | "ready" | "error";

export type CapabilitiesView = {
  mode: string;
  data_mode: string;
  execution_mode: string;
  trading_enabled: boolean;
  features: {
    preview: boolean;
    historical_import: boolean;
    testnet: boolean;
  };
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isCapabilitiesView(value: unknown): value is CapabilitiesView {
  if (!isRecord(value)) return false;
  const features = value.features;
  if (!isRecord(features)) return false;
  return typeof value.mode === "string"
    && typeof value.data_mode === "string"
    && typeof value.execution_mode === "string"
    && typeof value.trading_enabled === "boolean"
    && typeof features.preview === "boolean"
    && typeof features.historical_import === "boolean"
    && typeof features.testnet === "boolean";
}

type RingState = "ok" | "pending" | "error" | "idle";

function StatusRing({ state, label }: { state: RingState; label: string }) {
  return (
    <svg className={`sysstatus-ring sysstatus-ring-${state}`} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <title>{label}</title>
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="3" />
      {state === "ok" && <circle cx="12" cy="12" r="3.5" fill="currentColor" />}
    </svg>
  );
}

export function SystemStatusCard({
  apiStatus,
  apiError,
  datasets,
  datasetCatalogReady,
  selectedDatasetId,
  canary,
  canaryBusy,
  canaryError,
  onRefreshCanary,
  dashboard,
  dashboardBusy,
  dashboardError,
  capabilities,
  capabilitiesBusy,
  capabilitiesError,
}: {
  apiStatus: SystemApiStatus;
  apiError: string;
  datasets: DatasetSummary[];
  datasetCatalogReady: boolean;
  selectedDatasetId: string | null;
  canary: CanaryStatusView | null;
  canaryBusy: boolean;
  canaryError: string;
  onRefreshCanary: () => void;
  dashboard: DashboardView | null;
  dashboardBusy: boolean;
  dashboardError: string;
  capabilities: CapabilitiesView | null;
  capabilitiesBusy: boolean;
  capabilitiesError: string;
}) {
  const verifiedCount = datasets.filter((dataset) => dataset.status === "VERIFIED").length;
  const apiRing: RingState = apiStatus === "ready" ? "ok" : apiStatus === "loading" ? "pending" : apiStatus === "error" ? "error" : "idle";
  const dataRing: RingState = datasetCatalogReady ? "ok" : "idle";
  const securityRing: RingState = canary ? (canary.kill_switch_engaged ? "error" : "ok") : canaryBusy ? "pending" : canaryError ? "error" : "idle";
  const botsRing: RingState = dashboard ? "ok" : dashboardBusy ? "pending" : dashboardError ? "error" : "idle";
  const modeRing: RingState = capabilities ? "ok" : capabilitiesBusy ? "pending" : capabilitiesError ? "error" : "idle";
  return (
    <section className="panel sysstatus-panel" aria-labelledby="sysstatus-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">SİSTEM DURUMU</p>
          <h2 id="sysstatus-title">Durum &amp; Veri Kaynağı</h2>
        </div>
      </div>
      <div className="sysstatus-grid">
        <div className="sysstatus-card">
          <div className="sysstatus-card-title"><StatusRing state={apiRing} label="API durumu" />YEREL API</div>
          {apiStatus === "ready" && <p className="sysstatus-ok">✓ Bağlı</p>}
          {apiStatus === "loading" && <p className="sysstatus-pending">… Bağlanıyor</p>}
          {apiStatus === "error" && <p className="sysstatus-error">! Bağlantı yok</p>}
          {apiStatus === "unknown" && <p className="sysstatus-idle">○ Henüz okunmadı</p>}
          <p className="sysstatus-note">{apiStatus === "error" ? apiError || "Özet alınamadı." : apiStatus === "ready" ? "Özet okundu." : apiStatus === "loading" ? "Özet isteniyor…" : "Genel Bakış açılınca otomatik okunur."}</p>
        </div>
        <div className="sysstatus-card">
          <div className="sysstatus-card-title"><StatusRing state={dataRing} label="Katalog durumu" />VERİ KAYNAĞI</div>
          {datasetCatalogReady ? (
            <>
              <p className="sysstatus-ok">{datasets.length} dataset · {verifiedCount} doğrulandı</p>
              <p className="sysstatus-note">{selectedDatasetId ? `Seçili: ${selectedDatasetId}` : "Seçili dataset yok."}</p>
            </>
          ) : (
            <>
              <p className="sysstatus-idle">○ Katalog bekleniyor</p>
              <p className="sysstatus-note">Dataset kataloğu henüz yüklenmedi.</p>
            </>
          )}
        </div>
        <div className="sysstatus-card">
          <div className="sysstatus-card-title"><StatusRing state={securityRing} label="Güvenlik durumu" />GÜVENLİK</div>
          {canary ? (
            <>
              <p className={canary.kill_switch_engaged ? "sysstatus-error" : "sysstatus-ok"}>Kill-switch: {canary.kill_switch_engaged ? "AÇIK (devrede)" : "kapalı"}</p>
              <p className="sysstatus-note">Canary: <code>{canary.verdict}</code></p>
            </>
          ) : canaryBusy ? (
            <>
              <p className="sysstatus-pending">… Okunuyor</p>
              <p className="sysstatus-note">Güvenlik durumu isteniyor…</p>
            </>
          ) : canaryError ? (
            <>
              <p className="sysstatus-error">! Okunamadı</p>
              <p className="sysstatus-note">{canaryError}</p>
            </>
          ) : (
            <>
              <p className="sysstatus-idle">○ Durum henüz okunmadı</p>
              <p className="sysstatus-note">Risk bölümündekiyle aynı salt-okunur durumdur.</p>
            </>
          )}
          {!canary && !canaryBusy && <button className="secondary-button sysstatus-refresh" type="button" onClick={onRefreshCanary}>Yenile</button>}
        </div>
        <div className="sysstatus-card">
          <div className="sysstatus-card-title"><StatusRing state={botsRing} label="Bot sayacı durumu" />BOTLAR &amp; DEAL&apos;LER</div>
          {dashboard ? (
            <>
              <p className="sysstatus-ok">{dashboard.bots.bots} bot · {dashboard.bots.bound_sessions} bağlı oturum</p>
              <p className="sysstatus-note">{dashboard.deals.deals} deal · {dashboard.paper.sessions} paper-oturum · {dashboard.backups.backups} yedek</p>
            </>
          ) : dashboardBusy ? (
            <>
              <p className="sysstatus-pending">… Okunuyor</p>
              <p className="sysstatus-note">Sayaçlar isteniyor…</p>
            </>
          ) : dashboardError ? (
            <>
              <p className="sysstatus-error">! Okunamadı</p>
              <p className="sysstatus-note">{dashboardError}</p>
            </>
          ) : (
            <>
              <p className="sysstatus-idle">○ Sayaçlar henüz okunmadı</p>
              <p className="sysstatus-note">Genel Bakış özeti bekleniyor.</p>
            </>
          )}
        </div>
        <div className="sysstatus-card">
          <div className="sysstatus-card-title"><StatusRing state={modeRing} label="Bağlantı modu durumu" />BAĞLANTI MODU</div>
          {capabilities ? (
            <>
              <p className="sysstatus-ok">{capabilities.mode} · {capabilities.trading_enabled ? "trade açık" : "trade kapalı"}</p>
              <p className="sysstatus-note">Veri: <code>{capabilities.data_mode}</code> · Çalışma: <code>{capabilities.execution_mode}</code></p>
            </>
          ) : capabilitiesBusy ? (
            <>
              <p className="sysstatus-pending">… Okunuyor</p>
              <p className="sysstatus-note">Yetenekler isteniyor…</p>
            </>
          ) : capabilitiesError ? (
            <>
              <p className="sysstatus-error">! Okunamadı</p>
              <p className="sysstatus-note">{capabilitiesError}</p>
            </>
          ) : (
            <>
              <p className="sysstatus-idle">○ Mod henüz okunmadı</p>
              <p className="sysstatus-note">Açılışta otomatik okunur.</p>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
