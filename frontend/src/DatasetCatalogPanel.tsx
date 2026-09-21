import { type HTMLAttributes, type KeyboardEvent, type MouseEvent, useEffect, useRef, useState } from "react";
import { HistoricalChart } from "./HistoricalChart";
import { ExplanationSection } from "./ExplanationSection";
import { WindowExpander, useWindowedList } from "./renderWindow";
import { HistoricalProfileSelector, HistoricalProfileStatus } from "./HistoricalProfileSelector";
import {
  DATASET_STATUS_META,
  DATASET_STATUS_ORDER,
  DatasetCatalogStatus,
  DatasetDownloadJob,
  DatasetFilter,
  HistoricalChartData,
  DatasetPreflight,
  DatasetRunPlan,
  DownloadJobUiStatus,
  DatasetSelectionStatus,
  DatasetStatus,
  DatasetSummary,
  formatDatasetBytes,
  HistoricalSimulationResult,
  HistoricalProfile,
  isActiveDownloadJob,
  shortSha256,
} from "./datasetCatalog";

type DatasetCatalogPanelProps = {
  datasets: DatasetSummary[];
  status: DatasetCatalogStatus;
  error: string;
  filter: DatasetFilter;
  activeDatasetId: string | null;
  selectedDatasetId: string | null;
  selectionStatus: DatasetSelectionStatus;
  selectionError: string;
  downloadJob: DatasetDownloadJob | null;
  downloadUiStatus: DownloadJobUiStatus;
  downloadError: string;
  preflight: DatasetPreflight | null;
  preflightStatus: "idle" | "pending" | "ready" | "error";
  preflightError: string;
  historicalProfiles: HistoricalProfile[];
  historicalProfilesStatus: HistoricalProfileStatus;
  historicalProfilesError: string;
  selectedHistoricalProfileId: string | null;
  onHistoricalProfileChange: (profileId: string) => void;
  onRetryHistoricalProfiles: () => void;
  runPlan: DatasetRunPlan | null;
  runPlanStatus: "idle" | "pending" | "ready" | "error";
  runPlanError: string;
  simulation: HistoricalSimulationResult | null;
  simulationStatus: "idle" | "starting" | "completed" | "indeterminate" | "error";
  simulationError: string;
  chartData: HistoricalChartData | null;
  chartStatus: "idle" | "loading" | "ready" | "error";
  chartError: string;
  onFilterChange: (filter: DatasetFilter) => void;
  onDatasetFocus: (datasetId: string) => void;
  onSelect: (dataset: DatasetSummary) => void;
  onStartDownload: (dataset: DatasetSummary) => void;
  onCancelDownload: () => void;
  onRetryDownload: (dataset: DatasetSummary) => void;
  onStartHistoricalSimulation: () => void;
  historicalSaveStatus: "idle" | "saving" | "saved" | "already_saved" | "error";
  historicalSaveError: string;
  onSaveHistoricalRun: () => void;
  onOpenSavedRuns: () => void;
};

function statusClass(status: DatasetStatus): string {
  return status.toLowerCase();
}

function parserState(dataset: DatasetSummary, selectedDatasetId: string | null): { label: string; className: string } {
  if (dataset.status === "MISSING") return { label: "Bloklu · yerel cache yok", className: "blocked" };
  if (dataset.status === "CORRUPT") return { label: "Bloklu · bütünlük hatası", className: "blocked" };
  if (dataset.dataset_id === selectedDatasetId) return { label: "Seçildi · parser aktarımı bekliyor", className: "selected" };
  return { label: "Seçilebilir · aktarım bu fazda başlatılmaz", className: "available" };
}

function StatusBadge({ status }: { status: DatasetStatus }) {
  const meta = DATASET_STATUS_META[status];
  return <span className={`dataset-status ${statusClass(status)}`}><span aria-hidden="true">{meta.icon}</span>{status} — {meta.label}</span>;
}

function downloadJobLabel(status: DatasetDownloadJob["status"]): string {
  if (status === "QUEUED") return "Kuyrukta";
  if (status === "RUNNING") return "İndiriliyor";
  if (status === "RETRYING") return "Otomatik yeniden deneniyor";
  if (status === "SUCCEEDED") return "Doğrulandı · yerel cache hazır";
  if (status === "FAILED") return "İndirme başarısız";
  return "İptal edildi";
}

function ResultValue({ label, value, note }: { label: string; value: string; note?: string }) {
  return <div className="historical-result-value"><span>{label}</span><strong><code>{value}</code></strong>{note && <small>{note}</small>}</div>;
}

function CopyValue({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false);

  async function copyValue() {
    if (!navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return <div className="historical-copy-row"><span>{label}</span><code>{value}</code><button className="historical-copy-button" type="button" onClick={() => void copyValue()}>{copied ? "Kopyalandı" : "Kopyala"}</button></div>;
}

function fixedActionStatus(action: HistoricalSimulationResult["actions"][number]): string {
  if (action.action_type === "PARTIAL_FILL") return "Kısmi dolum";
  if (action.action_type === "FULL_FILL") return "Tam dolum";
  return action.order_status_after ?? "—";
}

export function ActionTable({ actions, fixedSlice, title = "AKSİYON GEÇMİŞİ", intro = "Backend’in kaydettiği simülasyon aksiyonları; finansal hesap yapılmadan, oluşma sırasıyla gösterilir.", selectedBarIndex = null, onSelectBarIndex }: { actions: HistoricalSimulationResult["actions"]; fixedSlice: boolean; title?: string; intro?: string; selectedBarIndex?: number | null; onSelectBarIndex?: (barIndex: number) => void }) {
  const interactive = typeof onSelectBarIndex === "function";
  const windowed = useWindowedList(actions, 100);
  const selectedBeyondWindow = selectedBarIndex !== null && selectedBarIndex !== undefined
    && actions.findIndex((action) => action.bar_index === selectedBarIndex) >= windowed.shown;
  const rows = selectedBeyondWindow ? actions : windowed.visible;

  useEffect(() => {
    if (selectedBarIndex === null || selectedBarIndex === undefined) return;
    const row = document.getElementById(`historical-action-row-${selectedBarIndex}`);
    if (row && typeof row.scrollIntoView === "function") {
      try {
        row.scrollIntoView({ block: "nearest", behavior: "smooth" });
      } catch {
        /* scroll desteklenmiyorsa seçim vurgusu yine de korunur */
      }
    }
  }, [selectedBarIndex]);

  function onRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, barIndex: number) {
    if (event.target !== event.currentTarget) return; // satır içindeki Kopyala/detay gibi öğelerin tuşlarını satır seçimine sızdırma
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onSelectBarIndex?.(barIndex);
  }

  function onRowClick(event: MouseEvent<HTMLTableRowElement>, barIndex: number) {
    if (event.target !== event.currentTarget) return; // satır içindeki Kopyala/detay gibi öğelerin tıklamasını satır seçimine sızdırma
    onSelectBarIndex?.(barIndex);
  }

  function rowProps(barIndex: number): HTMLAttributes<HTMLTableRowElement> {
    const selected = selectedBarIndex === barIndex;
    return {
      id: `historical-action-row-${barIndex}`,
      className: selected ? "historical-action-row-selected" : interactive ? "historical-action-row-interactive" : undefined,
      role: interactive ? "button" : undefined,
      tabIndex: interactive ? 0 : undefined,
      "aria-label": interactive ? `Bar ${barIndex} aksiyonunu seç` : undefined,
      "aria-pressed": interactive ? selected : undefined,
      onClick: interactive ? (event) => onRowClick(event, barIndex) : undefined,
      onKeyDown: interactive ? (event) => onRowKeyDown(event, barIndex) : undefined,
    };
  }

  return <section className="historical-action-history" aria-labelledby="historical-action-history-title">
    <div className="historical-action-heading"><div><p className="preflight-section-label" id="historical-action-history-title">{title}</p><p className="historical-action-intro">{intro}</p></div><span className="historical-action-count">{actions.length.toLocaleString("tr-TR")} aksiyon</span></div>
    {actions.length === 0 ? <p className="catalog-empty historical-action-empty">Bu koşuda aksiyon üretilmedi.</p> : <div className="historical-action-table-wrap">
      <table className="historical-action-table">
        <caption className="sr-only">Simülasyonda oluşan aksiyon geçmişi</caption>
        {fixedSlice ? <>
          <thead><tr><th scope="col">Bar</th><th scope="col">Aksiyon</th><th scope="col">Rol</th><th scope="col">Order</th><th scope="col">Orijinal</th><th scope="col">Dolan · kümülatif</th><th scope="col">Kalan</th><th scope="col">Durum</th></tr></thead>
          <tbody>{rows.map((action) => <tr key={`${action.event_sequence ?? action.bar_index}-${action.action_type ?? action.role}`} {...rowProps(action.bar_index)}>
            <td data-label="Bar"><code>{action.bar_index.toLocaleString("tr-TR")}</code></td>
            <td data-label="Aksiyon"><span className="historical-action-role">{action.action_type ?? "—"}</span></td>
            <td data-label="Rol">{action.role}</td>
            <td data-label="Order"><code>{action.order_id ? `${action.order_id.slice(0, 7)}…${action.order_id.slice(-5)}` : "—"}</code><details className="historical-action-details"><summary>Teknik ayrıntılar</summary><div className="historical-action-technical"><CopyValue label="Order ID" value={action.order_id ?? "—"} />{action.execution_id && <CopyValue label="Execution ID" value={action.execution_id} />}<div><span>Event sırası</span><code>{action.event_sequence ?? "—"}</code></div><div><span>Ham referans</span><code>{action.raw_reference}</code></div><div><span>Bar zamanı · UTC µs</span><code>{action.open_time_us}</code></div><div><span>Fill fiyatı / miktarı</span><code>{action.fill_price} / {action.quantity}</code></div><div><span>Fee</span><code>{action.fee} {action.fee_asset ?? ""}</code></div><div><span>Fill provenance</span><code>{action.fill_provenance ?? "—"}</code></div></div></details></td>
            <td data-label="Orijinal"><code>{action.original_qty ?? "—"}</code></td>
            <td data-label="Dolan · kümülatif"><code>{action.cumulative_filled_qty ?? "—"}</code></td>
            <td data-label="Kalan"><code>{action.leaves_qty ?? "—"}</code></td>
            <td data-label="Durum"><span className="historical-action-status">{fixedActionStatus(action)}</span><small className="historical-action-status-detail">Order: {action.order_status_after ?? "—"} · İptal: {action.canceled_qty ?? "0"}</small></td>
          </tr>)}</tbody>
        </> : <>
          <thead><tr><th scope="col">Bar</th><th scope="col">Rol</th><th scope="col">Zaman · UTC µs</th><th scope="col">Gerçekleşen fiyat</th><th scope="col">Miktar</th><th scope="col">Fee</th></tr></thead>
          <tbody>{rows.map((action) => <tr key={`${action.event_sequence ?? action.bar_index}-${action.role}`} {...rowProps(action.bar_index)}>
            <td data-label="Bar"><code>{action.bar_index.toLocaleString("tr-TR")}</code></td>
            <td data-label="Rol"><span className="historical-action-role">{action.role}</span></td>
            <td data-label="Zaman · UTC µs"><code>{action.open_time_us}</code></td>
            <td data-label="Gerçekleşen fiyat"><code>{action.fill_price}</code></td>
            <td data-label="Miktar"><code>{action.quantity}</code></td>
            <td data-label="Fee"><code>{action.fee}</code></td>
          </tr>)}</tbody>
        </>}
      </table>
      {!selectedBeyondWindow && windowed.hasMore && <WindowExpander shown={windowed.shown} total={windowed.total} onMore={windowed.showMore} />}
    </div>}
  </section>;
}

function PreflightCard({
  preflight,
  status,
  error,
  historicalProfiles,
  historicalProfilesStatus,
  historicalProfilesError,
  selectedHistoricalProfileId,
  onHistoricalProfileChange,
  onRetryHistoricalProfiles,
  runPlan,
  runPlanStatus,
  runPlanError,
  simulation,
  simulationStatus,
  simulationError,
  chartData,
  chartStatus,
  chartError,
  onStartHistoricalSimulation,
  historicalSaveStatus,
  historicalSaveError,
  onSaveHistoricalRun,
  onOpenSavedRuns,
}: {
  preflight: DatasetPreflight | null;
  status: "idle" | "pending" | "ready" | "error";
  error: string;
  historicalProfiles: HistoricalProfile[];
  historicalProfilesStatus: HistoricalProfileStatus;
  historicalProfilesError: string;
  selectedHistoricalProfileId: string | null;
  onHistoricalProfileChange: (profileId: string) => void;
  onRetryHistoricalProfiles: () => void;
  runPlan: DatasetRunPlan | null;
  runPlanStatus: "idle" | "pending" | "ready" | "error";
  runPlanError: string;
  simulation: HistoricalSimulationResult | null;
  simulationStatus: "idle" | "starting" | "completed" | "indeterminate" | "error";
  simulationError: string;
  chartData: HistoricalChartData | null;
  chartStatus: "idle" | "loading" | "ready" | "error";
  chartError: string;
  onStartHistoricalSimulation: () => void;
  historicalSaveStatus: "idle" | "saving" | "saved" | "already_saved" | "error";
  historicalSaveError: string;
  onSaveHistoricalRun: () => void;
  onOpenSavedRuns: () => void;
}) {
  const statusLabel = status === "pending" ? "Doğrulanıyor" : status === "error" ? "Gösterilemedi" : status === "ready" ? "Hazır" : "Bekliyor";
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [fixedSliceAcknowledged, setFixedSliceAcknowledged] = useState(false);
  const [fixedSliceError, setFixedSliceError] = useState("");
  const [profileResetNotice, setProfileResetNotice] = useState("");
  const confirmationRef = useRef<HTMLButtonElement | null>(null);
  const launchRef = useRef<HTMLButtonElement | null>(null);
  const fixedSliceCheckboxRef = useRef<HTMLInputElement | null>(null);
  const simulationScopeExceeded = preflight?.bar_count !== undefined && preflight.bar_count > 1000;
  const quoteAsset = runPlan?.config.quote_asset ?? "quote asset";
  const fixedSliceSelected = runPlan?.profile.simulation_model === "historical_ohlcv_partial_fixed_v1";
  const fixedSliceSimulation = simulation?.assumptions.model === "historical_ohlcv_partial_fixed_v1";
  const isFixedSliceUi = fixedSliceSelected || fixedSliceSimulation;
  const economicSummary = simulation?.final_economic_summary ?? simulation?.summary ?? null;
  const previousProfileRef = useRef<string | null>(selectedHistoricalProfileId);
  const [selectedBarIndex, setSelectedBarIndex] = useState<number | null>(null);
  const [draftPrice, setDraftPrice] = useState<string | null>(null);
  const [draftVerdict, setDraftVerdict] = useState("");
  const simulationExecutionId = simulation?.execution_id ?? null;

  useEffect(() => {
    if (confirmationOpen) confirmationRef.current?.focus();
  }, [confirmationOpen]);

  useEffect(() => {
    setSelectedBarIndex(null);
    setDraftPrice(null);
    setDraftVerdict("");
  }, [simulationExecutionId]);

  async function onDraftPrice(price: string) {
    if (chartStatus !== "ready" || !chartData) {
      setDraftPrice(null);
      setDraftVerdict("Taslak değerlendirilemedi: grafik kapsamı hazır değil.");
      return;
    }
    if (!price) {
      setDraftPrice(null);
      setDraftVerdict("");
      return;
    }
    try {
      const response = await fetch(`/api/datasets/${encodeURIComponent(chartData.dataset_id)}/draft-level`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ artifact_sha256: chartData.artifact_sha256, draft_price: price }),
      });
      const body = (await response.json()) as { verdict?: string; draft_price?: string; reason?: string; code?: string; detail?: string };
      if (!response.ok || (body.verdict !== "ACCEPTED" && body.verdict !== "REJECTED") || typeof body.draft_price !== "string" || typeof body.reason !== "string") {
        setDraftPrice(null);
        setDraftVerdict(body.detail ? `Taslak reddedildi: ${body.detail}` : "Taslak fiyat geçersiz; seviye çizilmedi.");
        return;
      }
      setDraftPrice(body.draft_price);
      setDraftVerdict(`${body.verdict}: ${body.reason}`);
    } catch {
      setDraftPrice(null);
      setDraftVerdict("Taslak API'sine bağlanılamadı.");
    }
  }

  useEffect(() => {
    setFixedSliceAcknowledged(false);
    setFixedSliceError("");
    if (previousProfileRef.current !== null && previousProfileRef.current !== selectedHistoricalProfileId) {
      setProfileResetNotice("Profil değişti; önceki koşu sonucu ve aksiyon görünümü temizlendi.");
    }
    previousProfileRef.current = selectedHistoricalProfileId;
  }, [selectedHistoricalProfileId]);

  function closeConfirmation() {
    setConfirmationOpen(false);
    window.setTimeout(() => launchRef.current?.focus(), 0);
  }

  function onConfirmationKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeConfirmation();
    }
  }

  function simulationStatusLabel(): string {
    if (simulationScopeExceeded) return "! Simülasyon kapsamı sınırı";
    if (simulationStatus === "completed") return isFixedSliceUi ? "✓ Fixed-slice simülasyonu tamamlandı" : "✓ Simülasyon tamamlandı";
    if (simulationStatus === "indeterminate") return "! Belirsiz tarihsel sonuç";
    if (simulationStatus === "starting") return "… Simülasyon çalışıyor";
    if (simulationStatus === "error") return "! Simülasyon başlatılamadı";
    return "○ Çalıştırmaya hazır";
  }

  const simulationMessage = simulationScopeExceeded
    ? "Bu dataset server’ın 1.000 bar sınırını aşıyor; çalıştırma güvenli biçimde kapatıldı."
    : simulationStatus === "starting"
    ? "Kapalı barlar işleniyor…"
    : simulationStatus === "completed"
      ? `Simülasyon tamamlandı · ${simulation?.dataset.processed_bar_count.toLocaleString("tr-TR") ?? "—"} bar işlendi.`
      : simulationStatus === "indeterminate"
        ? `Sonuç belirsiz · bar ${simulation?.ambiguity?.bar_index ?? "—"} için OHLC içi sıra çıkarılamadı.`
        : simulationStatus === "error"
          ? simulationError
          : "Hazır · henüz çalıştırılmadı";
  return <section className={`preflight-card ${status}`} aria-labelledby="preflight-title">
    <div className="preflight-heading"><div><p className="eyebrow">PRE-RUN PREFLIGHT</p><h4 id="preflight-title">Koşu öncesi kontrol</h4></div><span className={`preflight-badge ${status}`}>{status === "ready" ? "✓ " : status === "error" ? "! " : status === "pending" ? "… " : ""}{statusLabel}</span></div>
    {status === "pending" && <div className="preflight-status-message" role="status" aria-live="polite">Ön kontrol bilgileri hazırlanıyor…</div>}
    {status === "error" && <div className="preflight-error-message" role="alert"><strong>! Ön kontrol gösterilemedi</strong><p>Dataset seçimi korunuyor. {error || "Özet bilgileri şu anda alınamadı."}</p></div>}
    {status === "ready" && preflight && <>
      <div className="preflight-ready" role="status" aria-live="polite"><span aria-hidden="true">✓</span><strong>Ön kontrol hazır</strong></div>
      <p className="preflight-section-label">KOŞU KAPSAMI</p>
      <dl className="preflight-facts"><div><dt>Enstrüman</dt><dd>{preflight.instrument}</dd></div><div><dt>Interval</dt><dd>{preflight.interval}</dd></div><div><dt>Zaman aralığı</dt><dd>{preflight.period_start} → {preflight.period_end} · {preflight.timezone}</dd></div><div><dt>Bar sayısı</dt><dd>{preflight.bar_count.toLocaleString("tr-TR")}</dd></div></dl>
      <p className="preflight-section-label">VERİ KALİTESİ</p>
      <div className="preflight-quality unknown"><strong>? Kalite bilgisi yok</strong><p>{preflight.data_quality_message}</p></div>
      <details className="preflight-integrity"><summary>Bütünlük ayrıntıları</summary><dl className="preflight-facts"><div><dt>Tür</dt><dd>Kline CSV ZIP</dd></div><div><dt>SHA-256</dt><dd><code>{shortSha256(preflight.artifact.sha256)}</code></dd></div><div><dt>Boyut</dt><dd>{formatDatasetBytes(preflight.artifact.byte_size)}</dd></div><div><dt>Zaman standardı</dt><dd>{preflight.timestamp_unit} · {preflight.timezone}</dd></div></dl></details>
          <HistoricalProfileSelector profiles={historicalProfiles} status={historicalProfilesStatus} error={historicalProfilesError} selectedProfileId={selectedHistoricalProfileId} disabled={simulationStatus === "starting"} onChange={onHistoricalProfileChange} onRetry={onRetryHistoricalProfiles} />
      {profileResetNotice && <p className="historical-profile-reset" role="status" aria-live="polite">{profileResetNotice}</p>}
      {selectedHistoricalProfileId && runPlanStatus === "idle" && <p className="historical-profile-status">Koşu planı hazırlanmayı bekliyor…</p>}
      {runPlanStatus === "pending" && <div className="preflight-status-message" role="status" aria-live="polite">Aktif DCA config koşu planına bağlanıyor…</div>}
      {runPlanStatus === "error" && <div className="preflight-error-message" role="alert"><strong>! Config özeti gösterilemedi</strong><p>Dataset seçimi korunuyor. {runPlanError || "Aktif config şu anda alınamadı."}</p></div>}
      {runPlanStatus === "ready" && runPlan && <>
        <p className="preflight-section-label">SEÇİLİ PROFİL</p>
        <dl className="preflight-facts historical-profile-meta"><div><dt>Profil</dt><dd>{runPlan.profile.label} · v{runPlan.profile.profile_version}</dd></div><div><dt>Eşleşme</dt><dd>{runPlan.profile.expected_dataset_id ? "Beklenen dataset ile eşleşti" : "Dataset bağımsız"}</dd></div><div><dt>Kaynak niteliği</dt><dd>{runPlan.profile.venue_filter_provenance}</dd></div></dl>
        {fixedSliceSelected && <p className="historical-profile-note fixed-slice-note" role="note"><strong>Model farkı:</strong> Her uygun kapalı barda en fazla bir fixed-slice dolumu uygulanır. Dataset sonunda kalan miktar açık bırakılır; sentetik iptal veya çıkış uygulanmaz.</p>}
        {runPlan.profile.venue_filter_provenance === "project_fixture" && <p className="historical-profile-note" role="note">Bilgi: Bu profil bir offline demo uyumluluk fixture’ıdır. İlgili tarih için venue filtrelerinin tarihsel olarak doğrulandığı anlamına gelmez.</p>}
        <details className="historical-profile-details"><summary>Profil kimliği ve eşleşme ayrıntıları</summary><dl className="preflight-facts"><div><dt>Profil ID</dt><dd><code>{runPlan.profile.profile_id}</code></dd></div><div><dt>Beklenen dataset</dt><dd><code>{runPlan.profile.expected_dataset_id ?? "—"}</code></dd></div><div><dt>Anchor kaynağı</dt><dd>{runPlan.profile.anchor_source}</dd></div><div><dt>Tarihsel filtre iddiası</dt><dd>{runPlan.profile.historical_filter_claim ? "Var" : "Yok"}</dd></div></dl></details>
        <p className="preflight-section-label">AKTİF DCA CONFIG</p>
        <dl className="preflight-facts"><div><dt>Mod</dt><dd>{runPlan.config.mode} · {runPlan.execution_mode}</dd></div><div><dt>Sembol</dt><dd>{runPlan.config.symbol}</dd></div><div><dt>Base / safety</dt><dd>{runPlan.config.base_qty} / {runPlan.config.safety_qty} {runPlan.config.base_asset}</dd></div><div><dt>Safety sayısı</dt><dd>{runPlan.config.safety_count}</dd></div><div><dt>Sapma</dt><dd>{runPlan.config.deviation}</dd></div><div><dt>Hedef modu</dt><dd>{runPlan.config.target_mode}</dd></div><div><dt>Fee / slippage</dt><dd>{runPlan.config.fee_rate} / {runPlan.config.slippage}</dd></div>{fixedSliceSelected && <div><dt>Fixed slice</dt><dd>{runPlan.config.slice_qty ?? runPlan.profile.slice_qty ?? "—"} {runPlan.config.base_asset}</dd></div>}<div><dt>Config hash</dt><dd><code>{shortSha256(runPlan.config.config_hash)}</code></dd></div></dl>
        {fixedSliceSelected && <div className="fixed-slice-opt-in"><label htmlFor="fixed-slice-acknowledgement"><input ref={fixedSliceCheckboxRef} id="fixed-slice-acknowledgement" type="checkbox" checked={fixedSliceAcknowledged} aria-invalid={fixedSliceError ? "true" : "false"} aria-describedby="fixed-slice-acknowledgement-help fixed-slice-acknowledgement-error" onChange={(event) => { setFixedSliceAcknowledged(event.target.checked); setFixedSliceError(""); }} /> <span>Bu fixed-slice tarihsel modelini anlıyorum ve çalıştırmayı onaylıyorum.</span></label><p id="fixed-slice-acknowledgement-help">Bu seçim yalnızca offline, salt okunur simülasyonu başlatır; gerçek emir vermez ve finansal sonuç garantisi taşımaz.</p>{fixedSliceError && <p id="fixed-slice-acknowledgement-error" className="fixed-slice-opt-in-error" role="alert">{fixedSliceError}</p>}</div>}
        <div className={`historical-simulation-area ${simulationStatus}`} aria-labelledby="historical-simulation-title">
          <p className="preflight-section-label">HISTORICAL EXECUTION</p>
          <div className="simulation-mode-badges" aria-label="Simülasyon kapsamı"><span>OFFLINE</span><span>TARİHSEL</span><span>SIMULATED</span></div>
          <h5 id="historical-simulation-title">Offline tarihsel simülasyon</h5>
          <div className={`simulation-status ${simulationScopeExceeded ? "error" : simulationStatus}`} role={simulationScopeExceeded || simulationStatus === "error" ? "alert" : "status"} aria-live="polite"><strong>{simulationStatusLabel()}</strong><p>{simulationMessage}</p></div>
          {simulation && simulationStatus === "completed" && economicSummary && <div className="historical-result-summary" aria-labelledby="historical-result-title">
            <p className="preflight-section-label" id="historical-result-title">SONUÇ ÖZETİ</p>
            <div className="historical-result-values"><ResultValue label={`Brüt gerçekleşen sonuç · ${quoteAsset}`} value={economicSummary.realized_gross} note="Backend modelinden gelir; UI yeniden hesaplamaz." /><ResultValue label={`İşlem ücretleri · ${quoteAsset}`} value={economicSummary.fees} note="Backend’in quote-asset fee toplamıdır." /><ResultValue label={`Model net gerçekleşen sonuç · ${quoteAsset}`} value={economicSummary.realized_net_after_all_costs} note="Backend model sonucudur; funding bu tarihsel modelde işlenmez." /><ResultValue label="Pozisyon durumu" value={economicSummary.position_status === "OPEN_AT_END" ? "OPEN_AT_END" : "CLOSED"} note={economicSummary.position_status === "OPEN_AT_END" ? "Dönem sonunda açık kaldı; forced close uygulanmadı. Exchange mark olmadığı için gerçekleşmemiş sonuç ve equity sayısal olarak gösterilmiyor." : "Dönem sonunda pozisyon kapalı."} /></div>
             <dl className="preflight-facts historical-result-meta"><div><dt>İşlenen bar</dt><dd>{simulation.dataset.processed_bar_count.toLocaleString("tr-TR")}</dd></div><div><dt>Dönem</dt><dd>{simulation.dataset.period_start} → {simulation.dataset.period_end}</dd></div><div><dt>Model</dt><dd>{simulation.assumptions.model}</dd></div><div><dt>Config</dt><dd><code>{shortSha256(simulation.config.config_hash)}</code></dd></div><div><dt>Artifact</dt><dd><code>{shortSha256(simulation.dataset.artifact_sha256)}</code></dd></div></dl>
             <ExplanationSection explanations={simulation.explanations} />
             <HistoricalChart data={chartData} status={chartStatus} error={chartError} simulation={simulation} selectedBarIndex={selectedBarIndex} onSelectBarIndex={setSelectedBarIndex} draftPrice={draftPrice} draftVerdict={draftVerdict} onDraftPrice={(price) => void onDraftPrice(price)} />
            <ActionTable actions={simulation.actions} fixedSlice={fixedSliceSimulation} selectedBarIndex={selectedBarIndex} onSelectBarIndex={setSelectedBarIndex} />
          </div>}
          {simulation && simulationStatus === "indeterminate" && <>
             <div className="simulation-indeterminate-detail" role="note"><strong>Tamamlanmamış simülasyon · kesin ekonomik özet yok.</strong><p>Belirsiz bar commit edilmediği için bu koşu final execution kabul edilmez. Grafik üzerinde normal trade/action marker gösterilmez; açık ise yalnız nötr incomplete boundary gösterilir.</p>{simulation.action_authority?.mode === "COMMITTED_PREFIX" && <dl className="preflight-facts simulation-prefix-cutoff"><div><dt>Yetkili kapsam</dt><dd>Belirsizlik öncesi prefix kanıtı</dd></div><div><dt>Commit sınırı</dt><dd>Bar {simulation.action_authority.committed_through_bar_index} · event {simulation.action_authority.committed_through_event_sequence}</dd></div><div><dt>Belirsiz bar</dt><dd>Bar {simulation.action_authority.ambiguity_bar_index} · {simulation.ambiguity?.open_time_us ?? "zaman yok"}</dd></div></dl>}</div>
             <ExplanationSection explanations={simulation.explanations} />
             {simulation.marker_authority === "PREFIX_BOUNDARY_ONLY" && <HistoricalChart data={chartData} status={chartStatus} error={chartError} simulation={simulation} selectedBarIndex={selectedBarIndex} onSelectBarIndex={setSelectedBarIndex} />}
            {simulation.action_authority?.mode === "COMMITTED_PREFIX" && <ActionTable actions={simulation.actions} fixedSlice={isFixedSliceUi} title="PREFIX KANITI · TAMAMLANMAMIŞ KOŞU" intro="Yalnız ambiguity öncesi backend-commit edilmiş action snapshot’larıdır; tam execution history veya final işlem sonucu değildir." selectedBarIndex={selectedBarIndex} onSelectBarIndex={setSelectedBarIndex} />}
          </>}
          {(simulationStatus === "completed" || simulationStatus === "indeterminate") && simulation && (isFixedSliceUi ? <div className="historical-save-area historical-save-readonly" role="note"><div><p className="preflight-section-label">KALICI KAYIT</p><p>Bu profilin sonucu bu aşamada kalıcı koşuya bağlı değildir ve kaydedilemez.</p></div></div> : <div className="historical-save-area" aria-live="polite">
            <div><p className="preflight-section-label">KALICI KAYIT</p><p>{simulationStatus === "indeterminate" ? "Belirsizlik kanıtlarıyla birlikte salt okunur historical run kaydı oluşturulur." : "Bu koşunun server-side immutable snapshot’ını daha sonra yeniden açmak için saklayın."}</p></div>
            <div className="historical-save-actions"><button className="catalog-select-button" type="button" disabled={historicalSaveStatus === "saving" || historicalSaveStatus === "saved" || historicalSaveStatus === "already_saved"} onClick={onSaveHistoricalRun}>{historicalSaveStatus === "saving" ? "Kaydediliyor…" : historicalSaveStatus === "saved" ? "Koşu kaydedildi" : historicalSaveStatus === "already_saved" ? "Koşu zaten kayıtlı" : "Koşuyu kaydet"}</button>{(historicalSaveStatus === "saved" || historicalSaveStatus === "already_saved") && <button className="catalog-secondary-button" type="button" onClick={onOpenSavedRuns}>Saved Runs’ı aç</button>}</div>
            {historicalSaveError && <div className="form-error" role="alert">{historicalSaveError}</div>}
          </div>)}
          {!simulationScopeExceeded && (simulationStatus === "idle" || simulationStatus === "error") && <button ref={launchRef} className="catalog-select-button simulation-start-button" type="button" onClick={() => { if (fixedSliceSelected && !fixedSliceAcknowledged) { setFixedSliceError("Devam etmek için fixed-slice model onayını işaretleyin."); fixedSliceCheckboxRef.current?.focus(); return; } if (fixedSliceSelected) { onStartHistoricalSimulation(); return; } setConfirmationOpen(true); }}>Offline tarihsel simülasyonu başlat</button>}
          {simulationStatus === "starting" && <button className="catalog-select-button simulation-start-button" type="button" disabled>Simülasyon çalıştırılıyor…</button>}
          {(simulationStatus === "completed" || simulationStatus === "indeterminate") && <p className="simulation-follow-up">{isFixedSliceUi ? "İlk fixed-slice koşu özeti hazırlandı; bu aşamada sonuç yalnızca salt okunur gösterilir." : "İlk koşu özeti hazırlandı. Kalıcı kayıt oluşturulduğunda ayrıntıları Saved Runs ekranından salt okunur açabilirsiniz."}</p>}
          <div className="simulation-limitations"><strong>Varsayımlar ve sınırlamalar</strong><p>Yalnızca kapalı OHLCV barları işlendi. Funding sayısal olarak modellenmez ({simulation?.final_economic_summary?.funding_status ?? simulation?.summary?.funding_status ?? "NOT_MODELED"}); exchange mark mevcut değildir ({simulation?.final_economic_summary?.mark_status ?? simulation?.summary?.mark_status ?? "NOT_AVAILABLE"}). Bu nedenle unrealized ve equity bu minimum özette sayısal olarak gösterilmez. Forced close uygulanmaz.</p><p>{historicalSaveStatus === "saved" || historicalSaveStatus === "already_saved" ? "Immutable snapshot kalıcı local run store içinde saklanıyor; sonuç contract’ındaki persisted=false alanı değiştirilmedi." : "Sonuç henüz kalıcı olarak kaydedilmedi (`persisted=false`)."} Gerçek emir veya testnet bağlantısı yoktur.</p></div>
          {confirmationOpen && <div className="simulation-confirmation" role="dialog" aria-modal="true" aria-labelledby="simulation-confirmation-title" onKeyDown={onConfirmationKeyDown}>
            <h5 id="simulation-confirmation-title">Simülasyonu başlat?</h5>
            <p>{runPlan.config.symbol} · {preflight.interval} · {preflight.bar_count.toLocaleString("tr-TR")} bar</p>
            <p className="simulation-confirmation-note">Kapalı barlar, doğrulanmış artifact ve aktif config snapshot’ı ile işlenecek. OHLC içi sıra çıkarılamayan bir bar olursa sonuç belirsiz olarak durur.</p>
            <div className="simulation-confirmation-actions"><button ref={confirmationRef} className="catalog-secondary-button" type="button" onClick={closeConfirmation}>Vazgeç</button><button className="catalog-select-button" type="button" onClick={() => { setConfirmationOpen(false); onStartHistoricalSimulation(); }}>Başlat</button></div>
          </div>}
        </div>
      </>}
      <div className="preflight-readonly" role="note"><strong>Güvenli yürütme sınırı</strong><p>Yalnız explicit offline tarihsel simülasyon çalışır; gerçek emir ve kalıcı kayıt yoktur.</p></div>
    </>}
  </section>;
}

function DownloadJobCard({
  dataset,
  job,
  uiStatus,
  error,
  onStart,
  onCancel,
  onRetry,
}: {
  dataset: DatasetSummary;
  job: DatasetDownloadJob | null;
  uiStatus: DownloadJobUiStatus;
  error: string;
  onStart: () => void;
  onCancel: () => void;
  onRetry: () => void;
}) {
  const active = job ? isActiveDownloadJob(job.status) : false;
  const hasProgress = job?.status === "RUNNING" || job?.status === "RETRYING";
  const determinate = hasProgress && job?.total_bytes !== null && job?.total_bytes !== undefined && job.total_bytes > 0;
  const percent = determinate && job ? Math.min(100, Math.round((job.bytes_downloaded / job.total_bytes!) * 100)) : null;
  const actionDisabled = uiStatus === "starting" || uiStatus === "canceling";

  return <div className="download-job-card">
    <div className="download-card-heading"><div><p className="eyebrow">LOCAL COPY</p><strong>Yerel kopya</strong></div>{job && <span className={`download-job-badge ${job.status.toLowerCase()}`}>{downloadJobLabel(job.status)}</span>}</div>
    {uiStatus === "starting" && <div className="download-status-message" role="status">Download job başlatılıyor…</div>}
    {job && active && <>
      <div className="download-status-message" role="status" aria-live="polite">{job.status === "RETRYING" ? "↻ Otomatik yeniden deneniyor" : job.status === "QUEUED" ? "Kuyrukta" : `İndiriliyor${percent === null ? "" : ` · %${percent}`}`}</div>
      {hasProgress && <progress className="download-progress" value={determinate ? job.bytes_downloaded : undefined} max={determinate ? job.total_bytes ?? undefined : undefined} aria-label="Dataset indirme ilerlemesi" />}
      {hasProgress && <div className="download-progress-meta"><span>{formatDatasetBytes(job.bytes_downloaded)}{determinate ? ` / ${formatDatasetBytes(job.total_bytes!)}` : " indirildi · Toplam boyut bilinmiyor"}</span><span>Deneme {job.attempt}/{job.max_attempts}</span></div>}
      {uiStatus === "error" && error && <div className="download-poll-warning" role="status">⚠ {error}</div>}
      <button className="catalog-secondary-button" type="button" disabled={actionDisabled} onClick={onCancel}>{uiStatus === "canceling" ? "İptal isteniyor…" : "İptal et"}</button>
    </>}
    {job?.status === "SUCCEEDED" && <div className="download-success" role="status">✓ Doğrulandı · yerel cache hazır.</div>}
    {job?.status === "FAILED" && <>
      <div className="download-error-message" role="alert">{job.error_message ?? "Public dataset indirilemedi; doğrulanmış cache yayımlanmadı."}</div>
      <button className="catalog-select-button" type="button" onClick={onRetry}>Tekrar dene</button>
    </>}
    {job?.status === "CANCELLED" && <>
      <div className="download-cancelled" role="status">İndirme iptal edildi; dataset doğrulanmış olarak işaretlenmedi.</div>
      <button className="catalog-select-button" type="button" onClick={onRetry}>Yeniden indir</button>
    </>}
    {!job && uiStatus !== "starting" && <>
      {error && <div className="download-error-message" role="alert">{error}</div>}
      {dataset.status === "MISSING" && <button className="catalog-select-button" type="button" onClick={onStart}>İndir ve doğrula</button>}
      {dataset.status === "CORRUPT" && <button className="catalog-select-button" type="button" onClick={onStart}>Yeniden indir ve doğrula</button>}
    </>}
  </div>;
}

export function DatasetCatalogPanel({
  datasets,
  status,
  error,
  filter,
  activeDatasetId,
  selectedDatasetId,
  selectionStatus,
  selectionError,
  downloadJob,
  downloadUiStatus,
  downloadError,
  preflight,
  preflightStatus,
  preflightError,
  historicalProfiles,
  historicalProfilesStatus,
  historicalProfilesError,
  selectedHistoricalProfileId,
  onHistoricalProfileChange,
  onRetryHistoricalProfiles,
  runPlan,
  runPlanStatus,
  runPlanError,
  simulation,
  simulationStatus,
  simulationError,
  chartData,
  chartStatus,
  chartError,
  onFilterChange,
  onDatasetFocus,
  onSelect,
  onStartDownload,
  onCancelDownload,
  onRetryDownload,
  onStartHistoricalSimulation,
  historicalSaveStatus,
  historicalSaveError,
  onSaveHistoricalRun,
  onOpenSavedRuns,
}: DatasetCatalogPanelProps) {
  const activeDataset = datasets.find((dataset) => dataset.dataset_id === activeDatasetId) ?? null;
  const visibleDatasets = filter === "ALL" ? datasets : datasets.filter((dataset) => dataset.status === filter);
  const counts = DATASET_STATUS_ORDER.reduce<Record<string, number>>((result, datasetStatus) => {
    result[datasetStatus] = datasets.filter((dataset) => dataset.status === datasetStatus).length;
    return result;
  }, {});
  const activeParserState = activeDataset ? parserState(activeDataset, selectedDatasetId) : null;
  const isSelecting = selectionStatus === "pending";

  return (
    <section className="panel catalog-panel" aria-labelledby="catalog-title">
      <div className="panel-heading">
        <div><p className="eyebrow">DATASET CATALOG</p><h2 id="catalog-title">Geçmiş veri kataloğu</h2></div>
        <span className={`catalog-state ${status}`}>{status === "pending" ? "Yükleniyor" : status === "error" ? "Hata" : `${datasets.length} tanım`}</span>
      </div>
      <p className="catalog-intro">Kayıtlı public dataset tanımlarını ve doğrulanmış yerel cache durumunu gösterir. İndirme yalnız explicit registry kaydı üzerinden başlatılır.</p>

      {error && <div className="form-error" role="alert">{error}</div>}
      {status === "pending" && <div className="catalog-empty" role="status">Dataset kataloğu okunuyor…</div>}
      {status !== "pending" && status !== "error" && datasets.length === 0 && <div className="catalog-empty">Katalogda dataset tanımı bulunamadı.</div>}

      {status !== "pending" && status !== "error" && datasets.length > 0 && <>
        <div className="catalog-filters" aria-label="Dataset durum filtresi">
          <button className={filter === "ALL" ? "active" : ""} type="button" onClick={() => onFilterChange("ALL")}>Tümü <span>{datasets.length}</span></button>
          {DATASET_STATUS_ORDER.map((datasetStatus) => <button className={`${filter === datasetStatus ? "active " : ""}${statusClass(datasetStatus)}`} type="button" key={datasetStatus} onClick={() => onFilterChange(datasetStatus)}>{datasetStatus} <span>{counts[datasetStatus]}</span></button>)}
        </div>
        <div className="catalog-layout">
          <div className="catalog-table-wrap">
            {visibleDatasets.length > 0 ? <table className="catalog-table"><caption className="sr-only">Geçmiş veri dataset listesi</caption><thead><tr><th>Dataset</th><th>Enstrüman</th><th>Aralık</th><th>Dönem</th><th>Durum</th></tr></thead><tbody>
              {visibleDatasets.map((dataset) => <tr className={dataset.dataset_id === activeDatasetId ? "active-row" : ""} key={dataset.dataset_id} aria-selected={dataset.dataset_id === activeDatasetId}>
                <td data-label="Dataset"><button className="dataset-open-button" type="button" onClick={() => onDatasetFocus(dataset.dataset_id)} aria-label={`${dataset.dataset_id} ayrıntılarını göster`}><strong>{dataset.dataset_id}</strong><small>{dataset.dataset_type}</small></button></td>
                <td data-label="Enstrüman">{dataset.instrument}</td><td data-label="Aralık">{dataset.interval}</td><td data-label="Dönem">{dataset.period_start} → {dataset.period_end}</td><td data-label="Durum"><StatusBadge status={dataset.status} /></td>
              </tr>)}
            </tbody></table> : <div className="catalog-empty">Bu filtre için dataset bulunamadı.</div>}
          </div>

          <aside className="catalog-detail" aria-labelledby="catalog-detail-title">
            {activeDataset && activeParserState ? <>
              <div className="detail-heading"><div><p className="eyebrow">SELECTED DETAIL</p><h3 id="catalog-detail-title">{activeDataset.dataset_id}</h3></div><StatusBadge status={activeDataset.status} /></div>
              <dl className="dataset-facts"><div><dt>Enstrüman</dt><dd>{activeDataset.instrument}</dd></div><div><dt>Aralık</dt><dd>{activeDataset.interval}</dd></div><div><dt>Dönem</dt><dd>{activeDataset.period_start} → {activeDataset.period_end}</dd></div><div><dt>Artifact</dt><dd>{activeDataset.artifact ? formatDatasetBytes(activeDataset.artifact.byte_size) : "Yerel kopya yok"}</dd></div></dl>
              <div className={`parser-state ${activeParserState.className}`}><span aria-hidden="true">{activeParserState.className === "blocked" ? "!" : activeParserState.className === "selected" ? "✓" : "·"}</span><div><strong>Parser / application</strong><p>{activeParserState.label}</p></div></div>
              {activeDataset.status === "VERIFIED" && <PreflightCard preflight={preflight?.dataset_id === activeDataset.dataset_id ? preflight : null} status={preflightStatus} error={preflightError} historicalProfiles={historicalProfiles} historicalProfilesStatus={historicalProfilesStatus} historicalProfilesError={historicalProfilesError} selectedHistoricalProfileId={selectedHistoricalProfileId} onHistoricalProfileChange={onHistoricalProfileChange} onRetryHistoricalProfiles={onRetryHistoricalProfiles} runPlan={runPlan?.dataset.dataset_id === activeDataset.dataset_id ? runPlan : null} runPlanStatus={runPlanStatus} runPlanError={runPlanError} simulation={simulation} simulationStatus={simulationStatus} simulationError={simulationError} chartData={chartData?.dataset_id === activeDataset.dataset_id ? chartData : null} chartStatus={chartStatus} chartError={chartError} onStartHistoricalSimulation={onStartHistoricalSimulation} historicalSaveStatus={historicalSaveStatus} historicalSaveError={historicalSaveError} onSaveHistoricalRun={onSaveHistoricalRun} onOpenSavedRuns={onOpenSavedRuns} />}
              <DownloadJobCard dataset={activeDataset} job={downloadJob?.dataset_id === activeDataset.dataset_id ? downloadJob : null} uiStatus={downloadUiStatus} error={downloadError} onStart={() => onStartDownload(activeDataset)} onCancel={onCancelDownload} onRetry={() => onRetryDownload(activeDataset)} />
              {selectionError && activeDataset.status === "VERIFIED" && <div className="form-error" role="alert">{selectionError}</div>}
              <button className="catalog-select-button" type="button" disabled={activeDataset.status !== "VERIFIED" || isSelecting || activeDataset.dataset_id === selectedDatasetId} onClick={() => onSelect(activeDataset)}>{isSelecting ? "Seçiliyor…" : activeDataset.dataset_id === selectedDatasetId ? "Dataset seçildi" : activeDataset.status === "VERIFIED" ? "Dataset’i seç" : "Doğrulanmış cache gerekli"}</button>
            </> : <div className="catalog-empty">Ayrıntıları görmek için bir dataset seçin.</div>}
          </aside>
        </div>
      </>}
    </section>
  );
}
