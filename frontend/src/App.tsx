import { FormEvent, useEffect, useReducer, useRef, useState } from "react";
import { DatasetCatalogPanel } from "./DatasetCatalogPanel";
import { HistoricalProfileStatus } from "./HistoricalProfileSelector";
import { SavedRunsPanel } from "./SavedRunsPanel";
import { BinancePublicSnapshotPanel, isBinancePublicSnapshot, type BinancePublicSnapshot } from "./BinancePublicSnapshotPanel";
import { DatasetCatalogStatus, DatasetDownloadJob, DatasetFilter, DatasetPreflight, DatasetRunPlan, DownloadJobUiStatus, DatasetSelectionStatus, DatasetSummary, HistoricalChartData, HistoricalProfile, HistoricalSimulationResult, isActiveDownloadJob } from "./datasetCatalog";
import { SavedRunApiError, SavedRunDetail, SavedRunListItem, SavedRunListResponse, SavedRunSaveResponse } from "./savedRuns";

type FormState = {
  anchor: string;
  safety_qty: string;
  safety_count: string;
  deviation: string;
};

type Level = { index: number; price: string; qty: string; notional: string };
type Preview = {
  symbol: string;
  quote_asset: string;
  planned_gross_notional: string;
  estimated_initial_margin: string;
  policy_required_collateral: string | null;
  within_gross_entry_cap: boolean;
  levels: Level[];
  assumption: string;
  revision: number;
};
type ApiError = { error?: { message?: string; fields?: Record<string, string> } };
type DatasetApiError = { code?: string; detail?: string; title?: string };
type HistoricalSimulationUiStatus = "idle" | "starting" | "completed" | "indeterminate" | "error";
type QualityStatus = "PASS" | "PASS_WITH_WARNINGS" | "REJECTED";
type QualityReport = {
  status: QualityStatus;
  source_filename: string;
  source_sha256: string;
  source_bytes: number;
  kind: "bar" | "trade" | null;
  symbol: string | null;
  symbols: string[];
  headers: string[];
  row_count: number;
  timestamp: { field: string | null; unit: string | null; timezone: string | null; start: string | null; end: string | null; out_of_order: number };
  duplicates: { same: number; conflicts: number };
  gaps: { interval_us: string | null; basis: string | null; count: number; largest_us: string | null };
  issues: Array<{ code: string; severity: "error" | "warning"; message: string; row?: number }>;
  issue_count: number;
  issues_truncated: boolean;
  error_count: number;
  warning_count: number;
};
type MappingTarget = { key: string; label: string };

const BAR_MAPPING_TARGETS: MappingTarget[] = [
  { key: "open_time_us", label: "Açılış zamanı" },
  { key: "close_time_us", label: "Kapanış zamanı" },
  { key: "open", label: "Açılış fiyatı" },
  { key: "high", label: "En yüksek" },
  { key: "low", label: "En düşük" },
  { key: "close", label: "Kapanış fiyatı" },
  { key: "base_volume", label: "Hacim" },
  { key: "is_closed", label: "Bar kapalı mı?" },
];
const TRADE_MAPPING_TARGETS: MappingTarget[] = [
  { key: "exchange_time_us", label: "İşlem zamanı" },
  { key: "source_trade_id", label: "Kaynak işlem ID" },
  { key: "price", label: "İşlem fiyatı" },
  { key: "base_qty", label: "İşlem miktarı" },
];

const initialForm: FormState = {
  anchor: "100",
  safety_qty: "1",
  safety_count: "2",
  deviation: "0.1",
};

type DatasetState = {
  datasets: DatasetSummary[];
  datasetCatalogStatus: DatasetCatalogStatus;
  datasetCatalogError: string;
  datasetFilter: DatasetFilter;
  activeDatasetId: string | null;
  selectedDatasetId: string | null;
  datasetSelectionStatus: DatasetSelectionStatus;
  datasetSelectionError: string;
  downloadJob: DatasetDownloadJob | null;
  downloadUiStatus: DownloadJobUiStatus;
  downloadError: string;
  historicalProfiles: HistoricalProfile[];
  historicalProfilesStatus: HistoricalProfileStatus;
  historicalProfilesError: string;
  selectedHistoricalProfileId: string | null;
  datasetPreflight: DatasetPreflight | null;
  datasetPreflightStatus: "idle" | "pending" | "ready" | "error";
  datasetPreflightError: string;
  datasetRunPlan: DatasetRunPlan | null;
  datasetRunPlanStatus: "idle" | "pending" | "ready" | "error";
  datasetRunPlanError: string;
};

const initialDatasetState: DatasetState = {
  datasets: [],
  datasetCatalogStatus: "idle",
  datasetCatalogError: "",
  datasetFilter: "ALL",
  activeDatasetId: null,
  selectedDatasetId: null,
  datasetSelectionStatus: "idle",
  datasetSelectionError: "",
  downloadJob: null,
  downloadUiStatus: "idle",
  downloadError: "",
  historicalProfiles: [],
  historicalProfilesStatus: "idle",
  historicalProfilesError: "",
  selectedHistoricalProfileId: null,
  datasetPreflight: null,
  datasetPreflightStatus: "idle",
  datasetPreflightError: "",
  datasetRunPlan: null,
  datasetRunPlanStatus: "idle",
  datasetRunPlanError: "",
};

type SimulationState = {
  historicalSimulation: HistoricalSimulationResult | null;
  historicalSimulationStatus: HistoricalSimulationUiStatus;
  historicalSimulationError: string;
  historicalChartData: HistoricalChartData | null;
  historicalChartStatus: "idle" | "loading" | "ready" | "error";
  historicalChartError: string;
  historicalSaveStatus: "idle" | "saving" | "saved" | "already_saved" | "error";
  historicalSaveError: string;
};

const initialSimulationState: SimulationState = {
  historicalSimulation: null,
  historicalSimulationStatus: "idle",
  historicalSimulationError: "",
  historicalChartData: null,
  historicalChartStatus: "idle",
  historicalChartError: "",
  historicalSaveStatus: "idle",
  historicalSaveError: "",
};

type SavedRunsState = {
  savedRunView: "studio" | "list" | "detail" | "compare";
  savedRuns: SavedRunListItem[];
  savedRunsStatus: "idle" | "loading" | "ready" | "error";
  savedRunsError: string;
  savedRunDetail: SavedRunDetail | null;
  savedRunDetailStatus: "idle" | "loading" | "ready" | "error";
  savedRunDetailError: string;
  savedRunCompareSelection: string[];
  savedRunCompareDetails: [SavedRunDetail, SavedRunDetail] | null;
  savedRunCompareStatus: "idle" | "loading" | "ready" | "error";
  savedRunCompareError: string;
};

const initialSavedRunsState: SavedRunsState = {
  savedRunView: "studio",
  savedRuns: [],
  savedRunsStatus: "idle",
  savedRunsError: "",
  savedRunDetail: null,
  savedRunDetailStatus: "idle",
  savedRunDetailError: "",
  savedRunCompareSelection: [],
  savedRunCompareDetails: null,
  savedRunCompareStatus: "idle",
  savedRunCompareError: "",
};

type GroupAction<T extends object> = {
  [K in keyof T]: {
    key: K;
    value: T[K] | ((current: T[K]) => T[K]);
  };
}[keyof T];

export function groupReducer<T extends object>(state: T, action: GroupAction<T>): T {
  const current = state[action.key];
  const value =
    typeof action.value === "function"
      ? (action.value as (current: T[keyof T]) => T[keyof T])(current)
      : action.value;
  return { ...state, [action.key]: value };
}

function useReducerGroup<T extends object>(initialState: T) {
  const [state, dispatch] = useReducer(
    (current: T, action: GroupAction<T>) => groupReducer(current, action),
    initialState,
  );
  function setGroup<K extends keyof T>(key: K, value: T[K] | ((current: T[K]) => T[K])) {
    dispatch({ key, value } as GroupAction<T>);
  }
  return [state, setGroup] as const;
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<"idle" | "pending" | "ready" | "error">("idle");
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [qualityStatus, setQualityStatus] = useState<"idle" | "pending" | "ready" | "error">("idle");
  const [qualityError, setQualityError] = useState("");
  const [mappingKind, setMappingKind] = useState<QualityReport["kind"]>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [mappingStatus, setMappingStatus] = useState<"idle" | "valid" | "error">("idle");
  const [mappingError, setMappingError] = useState("");
  const [datasetState, setDatasetState] = useReducerGroup(initialDatasetState);
  const {
    datasets,
    datasetCatalogStatus,
    datasetCatalogError,
    datasetFilter,
    activeDatasetId,
    selectedDatasetId,
    datasetSelectionStatus,
    datasetSelectionError,
    downloadJob,
    downloadUiStatus,
    downloadError,
    historicalProfiles,
    historicalProfilesStatus,
    historicalProfilesError,
    selectedHistoricalProfileId,
    datasetPreflight,
    datasetPreflightStatus,
    datasetPreflightError,
    datasetRunPlan,
    datasetRunPlanStatus,
    datasetRunPlanError,
  } = datasetState;
  const setDatasetFilter = (value: DatasetFilter) => setDatasetState("datasetFilter", value);
  const setActiveDatasetId = (value: string | null) => setDatasetState("activeDatasetId", value);
  const [simulationState, setSimulationState] = useReducerGroup(initialSimulationState);
  const {
    historicalSimulation,
    historicalSimulationStatus,
    historicalSimulationError,
    historicalChartData,
    historicalChartStatus,
    historicalChartError,
    historicalSaveStatus,
    historicalSaveError,
  } = simulationState;
  const [savedRunsState, setSavedRunsState] = useReducerGroup(initialSavedRunsState);
  const {
    savedRunView,
    savedRuns,
    savedRunsStatus,
    savedRunsError,
    savedRunDetail,
    savedRunDetailStatus,
    savedRunDetailError,
    savedRunCompareSelection,
    savedRunCompareDetails,
    savedRunCompareStatus,
    savedRunCompareError,
  } = savedRunsState;
  const [binancePublicSnapshot, setBinancePublicSnapshot] = useState<BinancePublicSnapshot | null>(null);
  const [binancePublicSnapshotStatus, setBinancePublicSnapshotStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [binancePublicSnapshotError, setBinancePublicSnapshotError] = useState("");
  const revision = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const qualityController = useRef<AbortController | null>(null);
  const datasetController = useRef<AbortController | null>(null);
  const downloadActionController = useRef<AbortController | null>(null);
  const historicalProfilesController = useRef<AbortController | null>(null);
  const preflightController = useRef<AbortController | null>(null);
  const runPlanController = useRef<AbortController | null>(null);
  const runPlanRequestGeneration = useRef(0);
  const historicalSimulationController = useRef<AbortController | null>(null);
  const historicalChartController = useRef<AbortController | null>(null);
  const savedRunsController = useRef<AbortController | null>(null);
  const savedRunDetailController = useRef<AbortController | null>(null);
  const historicalSaveController = useRef<AbortController | null>(null);
  const binancePublicSnapshotController = useRef<AbortController | null>(null);

  async function calculate(nextForm: FormState) {
    const currentRevision = revision.current + 1;
    revision.current = currentRevision;
    controller.current?.abort();
    const requestController = new AbortController();
    controller.current = requestController;
    setStatus("pending");
    setErrors({});
    try {
      const response = await fetch("/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...nextForm,
          safety_count: Number(nextForm.safety_count),
          revision: currentRevision,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as { data?: Preview } & ApiError;
      if (currentRevision !== revision.current) return;
      if (!response.ok || !body.data) {
        setPreview(null);
        setErrors(body.error?.fields ?? { form: body.error?.message ?? "Önizleme hesaplanamadı." });
        setStatus("error");
        return;
      }
      setPreview(body.data);
      setStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted || currentRevision !== revision.current) return;
      setPreview(null);
      setErrors({ form: "API yanıt vermedi. Local API'nin çalıştığını kontrol edin." });
      setStatus("error");
    }
  }

  useEffect(() => {
    void calculate(initialForm);
    void loadDatasets();
    void loadHistoricalProfiles();
    void loadBinancePublicSnapshot();
    return () => {
      controller.current?.abort();
      qualityController.current?.abort();
      datasetController.current?.abort();
      downloadActionController.current?.abort();
      historicalProfilesController.current?.abort();
      preflightController.current?.abort();
      runPlanController.current?.abort();
      historicalSimulationController.current?.abort();
      historicalChartController.current?.abort();
      savedRunsController.current?.abort();
      savedRunDetailController.current?.abort();
      historicalSaveController.current?.abort();
      binancePublicSnapshotController.current?.abort();
    };
  }, []);

  async function loadBinancePublicSnapshot() {
    binancePublicSnapshotController.current?.abort();
    const requestController = new AbortController();
    binancePublicSnapshotController.current = requestController;
    setBinancePublicSnapshotStatus("loading");
    setBinancePublicSnapshotError("");
    try {
      const response = await fetch("/api/venue-snapshots/binance-spot-testnet?symbol=BTCUSDT", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isBinancePublicSnapshot(body)) {
        const errorBody = body as { detail?: string; title?: string };
        setBinancePublicSnapshot(null);
        setBinancePublicSnapshotError(errorBody.detail ?? errorBody.title ?? "Public Testnet snapshot sözleşmesi doğrulanamadı.");
        setBinancePublicSnapshotStatus("error");
        return;
      }
      setBinancePublicSnapshot(body);
      setBinancePublicSnapshotStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setBinancePublicSnapshot(null);
      setBinancePublicSnapshotError("Public Testnet snapshot API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setBinancePublicSnapshotStatus("error");
    }
  }

  async function loadHistoricalProfiles() {
    historicalProfilesController.current?.abort();
    const requestController = new AbortController();
    historicalProfilesController.current = requestController;
    setDatasetState("historicalProfilesStatus", "loading");
    setDatasetState("historicalProfilesError", "");
    try {
      const response = await fetch("/api/historical-profiles", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as HistoricalProfile[] & DatasetApiError;
      if (!response.ok || !Array.isArray(body)) {
        setDatasetState("historicalProfilesError", body.detail ?? body.title ?? "Historical profile katalogu okunamadı.");
        setDatasetState("historicalProfilesStatus", "error");
        return;
      }
      setDatasetState("historicalProfiles", body);
      setDatasetState("historicalProfilesStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDatasetState("historicalProfilesError", "Historical profile API'ye bağlanamadı. Local API'nin çalıştığını kontrol edin.");
      setDatasetState("historicalProfilesStatus", "error");
    }
  }

  async function loadDatasets() {
    datasetController.current?.abort();
    const requestController = new AbortController();
    datasetController.current = requestController;
    setDatasetState("datasetCatalogStatus", "pending");
    setDatasetState("datasetCatalogError", "");
    try {
      const response = await fetch("/api/datasets", { signal: requestController.signal });
      const body = (await response.json()) as { datasets?: DatasetSummary[]; count?: number } & DatasetApiError;
      if (!response.ok || !body.datasets) {
        setDatasetState("datasetCatalogError", body.detail ?? body.title ?? "Dataset kataloğu okunamadı.");
        setDatasetState("datasetCatalogStatus", "error");
        return;
      }
      setDatasetState("datasets", body.datasets);
      setDatasetState("activeDatasetId", body.datasets[0]?.dataset_id ?? null);
      setDatasetState("datasetCatalogStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDatasetState("datasetCatalogError", "Dataset kataloğu API'ye bağlanamadı. Local API'nin çalıştığını kontrol edin.");
      setDatasetState("datasetCatalogStatus", "error");
    }
  }

  useEffect(() => {
    const activeDataset = datasets.find((dataset) => dataset.dataset_id === activeDatasetId);
    preflightController.current?.abort();
    runPlanController.current?.abort();
    runPlanRequestGeneration.current += 1;
    setDatasetState("selectedHistoricalProfileId", null);
    setDatasetState("datasetPreflight", null);
    setDatasetState("datasetPreflightError", "");
    setDatasetState("datasetRunPlan", null);
    setDatasetState("datasetRunPlanError", "");
    setDatasetState("datasetRunPlanStatus", "idle");
    setSimulationState("historicalSimulation", null);
    setSimulationState("historicalSimulationStatus", "idle");
    setSimulationState("historicalSimulationError", "");
    setSimulationState("historicalSaveStatus", "idle");
    setSimulationState("historicalSaveError", "");
    historicalChartController.current?.abort();
    setSimulationState("historicalChartData", null);
    setSimulationState("historicalChartStatus", "idle");
    setSimulationState("historicalChartError", "");
    if (!activeDataset || activeDataset.status !== "VERIFIED") {
      setDatasetState("datasetPreflightStatus", "idle");
      return;
    }
    const activeDatasetIdForRequest = activeDataset.dataset_id;
    const requestController = new AbortController();
    preflightController.current = requestController;
    setDatasetState("datasetPreflightStatus", "pending");
    async function loadPreflight() {
      try {
        const response = await fetch(`/api/datasets/${encodeURIComponent(activeDatasetIdForRequest)}/preflight`, { signal: requestController.signal });
        const body = (await response.json()) as DatasetPreflight & DatasetApiError;
        if (!response.ok || body.preflight_status !== "READY") {
          setDatasetState("datasetPreflightError", body.detail ?? body.title ?? "Ön kontrol gösterilemedi. Dataset seçimi korunuyor.");
          setDatasetState("datasetPreflightStatus", "error");
          return;
        }
        setDatasetState("datasetPreflight", body);
        setDatasetState("datasetPreflightStatus", "ready");
      } catch (error) {
        if (requestController.signal.aborted) return;
        setDatasetState("datasetPreflightError", "Ön kontrol gösterilemedi. Dataset seçimi korunuyor.");
        setDatasetState("datasetPreflightStatus", "error");
      }
    }
    void loadPreflight();
    return () => requestController.abort();
  }, [activeDatasetId, datasets]);

  async function selectHistoricalProfile(profileId: string) {
    const selectedProfile = historicalProfiles.find((profile) => profile.profile_id === profileId);
    if (!selectedProfile || !activeDatasetId || datasetPreflight?.dataset_id !== activeDatasetId || datasetPreflightStatus !== "ready") return;
    const requestGeneration = runPlanRequestGeneration.current + 1;
    runPlanRequestGeneration.current = requestGeneration;
    runPlanController.current?.abort();
    const requestController = new AbortController();
    runPlanController.current = requestController;
    setDatasetState("selectedHistoricalProfileId", selectedProfile.profile_id);
    setDatasetState("datasetRunPlan", null);
    setDatasetState("datasetRunPlanError", "");
    setDatasetState("datasetRunPlanStatus", "pending");
    setSimulationState("historicalSimulation", null);
    setSimulationState("historicalSimulationStatus", "idle");
    setSimulationState("historicalSimulationError", "");
    historicalChartController.current?.abort();
    setSimulationState("historicalChartData", null);
    setSimulationState("historicalChartStatus", "idle");
    setSimulationState("historicalChartError", "");
    setSimulationState("historicalSaveStatus", "idle");
    setSimulationState("historicalSaveError", "");
    try {
      const response = await fetch(`/api/datasets/${encodeURIComponent(activeDatasetId)}/run-plan?profile_id=${encodeURIComponent(selectedProfile.profile_id)}`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as Partial<DatasetRunPlan> & DatasetApiError;
      if (requestGeneration !== runPlanRequestGeneration.current) return;
      if (!response.ok || body.run_status !== "NOT_STARTED" || !body.config || !body.dataset || !body.profile || body.profile.profile_id !== selectedProfile.profile_id || body.dataset.dataset_id !== activeDatasetId) {
        setDatasetState("datasetRunPlanError", body.detail ?? body.title ?? "Seçili historical profile bu dataset ile güvenli biçimde eşleştirilemedi.");
        setDatasetState("datasetRunPlanStatus", "error");
        return;
      }
      setDatasetState("datasetRunPlan", body as DatasetRunPlan);
      setDatasetState("datasetRunPlanStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted || requestGeneration !== runPlanRequestGeneration.current) return;
      setDatasetState("datasetRunPlanError", "Seçili historical profile için koşu planı alınamadı. Local API'nin çalıştığını kontrol edin.");
      setDatasetState("datasetRunPlanStatus", "error");
    }
  }

  async function loadHistoricalChartData(datasetId: string, expectedArtifactSha256: string, expectedProcessedBarCount: number) {
    historicalChartController.current?.abort();
    const requestController = new AbortController();
    historicalChartController.current = requestController;
    setSimulationState("historicalChartData", null);
    setSimulationState("historicalChartError", "");
    setSimulationState("historicalChartStatus", "loading");
    try {
      const response = await fetch(`/api/datasets/${encodeURIComponent(datasetId)}/chart-data`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as HistoricalChartData & DatasetApiError;
      if (!response.ok || body.model_id !== "historical_ohlcv_v1" || body.dataset_id !== datasetId || body.artifact_sha256 !== expectedArtifactSha256 || body.processed_bar_count !== expectedProcessedBarCount || !Array.isArray(body.bars)) {
        setSimulationState("historicalChartError", response.status === 409 ? "Grafik kapsamı izin verilen sınır içinde değil; görünüm oluşturulmadı." : "Tarihsel OHLC görünümü güvenli biçimde oluşturulamadı.");
        setSimulationState("historicalChartStatus", "error");
        return;
      }
      setSimulationState("historicalChartData", body);
      setSimulationState("historicalChartStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSimulationState("historicalChartError", "Tarihsel OHLC görünümü alınamadı. Local API'nin çalıştığını kontrol edin.");
      setSimulationState("historicalChartStatus", "error");
    }
  }

  async function startHistoricalSimulation() {
    if (!datasetPreflight || !datasetRunPlan || !selectedHistoricalProfileId || datasetRunPlan.profile.profile_id !== selectedHistoricalProfileId || datasetRunPlanStatus !== "ready") return;
    historicalSimulationController.current?.abort();
    const requestController = new AbortController();
    historicalSimulationController.current = requestController;
    setSimulationState("historicalSimulation", null);
    setSimulationState("historicalSimulationError", "");
    setSimulationState("historicalSaveStatus", "idle");
    setSimulationState("historicalSaveError", "");
    setSimulationState("historicalSimulationStatus", "starting");
    try {
      const response = await fetch("/api/historical-runs/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: datasetRunPlan.dataset.dataset_id,
          profile_id: selectedHistoricalProfileId,
          artifact_sha256: datasetRunPlan.dataset.artifact.sha256,
          config_hash: datasetRunPlan.config.config_hash,
          execution_mode: datasetRunPlan.profile.simulation_model ?? "historical_ohlcv_v1",
          action_authority: datasetRunPlan.profile.simulation_model === "historical_ohlcv_partial_fixed_v1" ? "COMMITTED_PREFIX" : "NONE",
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as HistoricalSimulationResult & DatasetApiError;
      if (!response.ok || !body.execution_status) {
        setSimulationState("historicalSimulationError", body.detail ?? body.title ?? "Tarihsel simülasyon başlatılamadı.");
        setSimulationState("historicalSimulationStatus", "error");
        return;
      }
      setSimulationState("historicalSimulation", body);
      const completed = body.execution_status === "COMPLETED";
      setSimulationState("historicalSimulationStatus", completed ? "completed" : "indeterminate");
      if (completed) void loadHistoricalChartData(datasetRunPlan.dataset.dataset_id, body.dataset.artifact_sha256, body.dataset.processed_bar_count);
      else if (body.marker_authority === "PREFIX_BOUNDARY_ONLY" && datasetPreflight) void loadHistoricalChartData(datasetRunPlan.dataset.dataset_id, body.dataset.artifact_sha256, datasetPreflight.bar_count);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSimulationState("historicalSimulationError", "Simülasyon API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setSimulationState("historicalSimulationStatus", "error");
    }
  }

  async function loadSavedRuns() {
    savedRunsController.current?.abort();
    const requestController = new AbortController();
    savedRunsController.current = requestController;
    setSavedRunsState("savedRunsStatus", "loading");
    setSavedRunsState("savedRunsError", "");
    try {
      const response = await fetch("/api/historical-runs?limit=50", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as SavedRunListResponse & SavedRunApiError;
      if (!response.ok || !Array.isArray(body.runs) || typeof body.count !== "number") {
        setSavedRunsState("savedRunsError", body.detail ?? body.title ?? "Kaydedilmiş koşular okunamadı.");
        setSavedRunsState("savedRunsStatus", "error");
        return;
      }
      setSavedRunsState("savedRuns", body.runs);
      setSavedRunsState("savedRunsStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSavedRunsState("savedRunsError", "Saved Runs API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setSavedRunsState("savedRunsStatus", "error");
    }
  }

  function openSavedRuns() {
    setSavedRunsState("savedRunView", "list");
    void loadSavedRuns();
  }

  async function openSavedRunDetail(runId: string) {
    savedRunDetailController.current?.abort();
    const requestController = new AbortController();
    savedRunDetailController.current = requestController;
    setSavedRunsState("savedRunView", "detail");
    setSavedRunsState("savedRunDetail", null);
    setSavedRunsState("savedRunDetailError", "");
    setSavedRunsState("savedRunDetailStatus", "loading");
    try {
      const response = await fetch(`/api/historical-runs/${encodeURIComponent(runId)}`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as SavedRunDetail & SavedRunApiError;
      if (!response.ok || body.storage_state !== "STORED" || !body.run_id) {
        setSavedRunsState("savedRunDetailError", response.status === 409 ? "Bu kayıt doğrulanamadı; güvenli ayrıntı görünümü açılmadı." : body.detail ?? body.title ?? "Koşu ayrıntısı okunamadı.");
        setSavedRunsState("savedRunDetailStatus", "error");
        return;
      }
      setSavedRunsState("savedRunDetail", body);
      setSavedRunsState("savedRunDetailStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSavedRunsState("savedRunDetailError", "Koşu ayrıntısı API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setSavedRunsState("savedRunDetailStatus", "error");
    }
  }

  function toggleCompareSelection(runId: string) {
    const next = savedRunCompareSelection.includes(runId)
      ? savedRunCompareSelection.filter((id) => id !== runId)
      : savedRunCompareSelection.length < 2
        ? [...savedRunCompareSelection, runId]
        : savedRunCompareSelection;
    setSavedRunsState("savedRunCompareSelection", next);
  }

  async function openSavedRunCompare() {
    if (savedRunCompareSelection.length !== 2) return;
    const [firstId, secondId] = savedRunCompareSelection;
    savedRunDetailController.current?.abort();
    const requestController = new AbortController();
    savedRunDetailController.current = requestController;
    setSavedRunsState("savedRunView", "compare");
    setSavedRunsState("savedRunCompareDetails", null);
    setSavedRunsState("savedRunCompareError", "");
    setSavedRunsState("savedRunCompareStatus", "loading");
    try {
      const [firstResponse, secondResponse] = await Promise.all([
        fetch(`/api/historical-runs/${encodeURIComponent(firstId)}`, { cache: "no-store", signal: requestController.signal }),
        fetch(`/api/historical-runs/${encodeURIComponent(secondId)}`, { cache: "no-store", signal: requestController.signal }),
      ]);
      const [firstBody, secondBody] = await Promise.all([
        firstResponse.json() as Promise<SavedRunDetail & SavedRunApiError>,
        secondResponse.json() as Promise<SavedRunDetail & SavedRunApiError>,
      ]);
      if (!firstResponse.ok || !secondResponse.ok || firstBody.storage_state !== "STORED" || secondBody.storage_state !== "STORED") {
        setSavedRunsState("savedRunCompareError", "Seçilen koşulardan biri okunamadı; karşılaştırma açılmadı.");
        setSavedRunsState("savedRunCompareStatus", "error");
        return;
      }
      setSavedRunsState("savedRunCompareDetails", [firstBody, secondBody]);
      setSavedRunsState("savedRunCompareStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSavedRunsState("savedRunCompareError", "Karşılaştırma API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setSavedRunsState("savedRunCompareStatus", "error");
    }
  }

  async function saveHistoricalRun() {
    if (!historicalSimulation || historicalSimulation.execution_id === null || !["completed", "indeterminate"].includes(historicalSimulationStatus) || historicalSaveStatus === "saving" || historicalSaveStatus === "saved" || historicalSaveStatus === "already_saved") return;
    historicalSaveController.current?.abort();
    const requestController = new AbortController();
    historicalSaveController.current = requestController;
    setSimulationState("historicalSaveStatus", "saving");
    setSimulationState("historicalSaveError", "");
    try {
      const response = await fetch("/api/historical-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ execution_id: historicalSimulation.execution_id }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as SavedRunSaveResponse & SavedRunApiError;
      if (!response.ok || !body.run_id || body.record_health !== "OK") {
        setSimulationState("historicalSaveError", body.detail ?? body.title ?? "Tarihsel koşu kalıcı olarak kaydedilemedi.");
        setSimulationState("historicalSaveStatus", "error");
        return;
      }
      setSimulationState("historicalSaveStatus", body.created ? "saved" : "already_saved");
      void loadSavedRuns();
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSimulationState("historicalSaveError", "Koşuyu kaydetme API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setSimulationState("historicalSaveStatus", "error");
    }
  }

  async function startDatasetDownload(dataset: DatasetSummary) {
    if (dataset.status === "VERIFIED" || (downloadJob && isActiveDownloadJob(downloadJob.status))) return;
    downloadActionController.current?.abort();
    const requestController = new AbortController();
    downloadActionController.current = requestController;
    setDatasetState("downloadJob", null);
    setDatasetState("downloadError", "");
    setDatasetState("downloadUiStatus", "starting");
    try {
      const response = await fetch("/api/dataset-downloads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: dataset.dataset_id }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as { job?: DatasetDownloadJob } & DatasetApiError;
      if (!response.ok || !body.job) {
        setDatasetState("downloadError", response.status === 409 ? "Bu dataset için başka bir indirme devam ediyor." : body.detail ?? body.title ?? "Dataset download başlatılamadı.");
        setDatasetState("downloadUiStatus", "error");
        return;
      }
      setDatasetState("downloadJob", body.job);
      setDatasetState("downloadUiStatus", "polling");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDatasetState("downloadError", "Download job API'ye bağlanamadı. Local API'nin çalıştığını kontrol edin.");
      setDatasetState("downloadUiStatus", "error");
    }
  }

  useEffect(() => {
    const jobId = downloadJob?.job_id;
    if (!jobId || !downloadJob || !isActiveDownloadJob(downloadJob.status)) return;
    const activeJobId = jobId;
    const requestController = new AbortController();
    let timer: number | undefined;
    async function poll() {
      try {
        const response = await fetch(`/api/dataset-downloads/${encodeURIComponent(activeJobId)}`, { signal: requestController.signal });
        const body = (await response.json()) as DatasetDownloadJob & DatasetApiError;
        if (response.status === 404) {
          setDatasetState("downloadJob", null);
          setDatasetState("downloadError", "İş kaydı artık bulunamıyor. Uygulama yeniden başlatılmış olabilir; katalog durumu yeniden kontrol edildi.");
          setDatasetState("downloadUiStatus", "error");
          void loadDatasets();
          return;
        }
        if (!response.ok || !body.job_id) {
          setDatasetState("downloadError", "Durum güncellenemiyor; indirme arka planda devam ediyor olabilir. Son bilinen durum gösteriliyor.");
          setDatasetState("downloadUiStatus", "error");
          timer = window.setTimeout(poll, 1200);
          return;
        }
        setDatasetState("downloadJob", body);
        if (isActiveDownloadJob(body.status)) {
          setDatasetState("downloadError", "");
          setDatasetState("downloadUiStatus", "polling");
          timer = window.setTimeout(poll, 750);
          return;
        }
        setDatasetState("downloadUiStatus", "idle");
        if (body.status === "SUCCEEDED") void loadDatasets();
      } catch (error) {
        if (requestController.signal.aborted) return;
        setDatasetState("downloadError", "Durum güncellenemiyor; indirme arka planda devam ediyor olabilir. Son bilinen durum gösteriliyor.");
        setDatasetState("downloadUiStatus", "error");
        timer = window.setTimeout(poll, 1200);
      }
    }
    void poll();
    return () => {
      requestController.abort();
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [downloadJob?.job_id]);

  async function cancelDatasetDownload() {
    if (!downloadJob || !isActiveDownloadJob(downloadJob.status)) return;
    downloadActionController.current?.abort();
    const requestController = new AbortController();
    downloadActionController.current = requestController;
    setDatasetState("downloadError", "");
    setDatasetState("downloadUiStatus", "canceling");
    try {
      const response = await fetch(`/api/dataset-downloads/${encodeURIComponent(downloadJob.job_id)}/cancel`, { method: "POST", signal: requestController.signal });
      const body = (await response.json()) as DatasetDownloadJob & DatasetApiError;
      if (!response.ok || !body.job_id) {
        setDatasetState("downloadError", body.detail ?? body.title ?? "İptal isteği gönderilemedi. Durumu yeniden kontrol edin.");
        setDatasetState("downloadUiStatus", "error");
        return;
      }
      setDatasetState("downloadJob", body);
      setDatasetState("downloadUiStatus", isActiveDownloadJob(body.status) ? "polling" : "idle");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDatasetState("downloadError", "İptal isteği gönderilemedi. Durumu yeniden kontrol edin.");
      setDatasetState("downloadUiStatus", "error");
    }
  }

  async function selectDataset(dataset: DatasetSummary) {
    if (dataset.status !== "VERIFIED") return;
    setDatasetState("datasetSelectionStatus", "pending");
    setDatasetState("datasetSelectionError", "");
    try {
      const response = await fetch("/api/dataset-selection", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: dataset.dataset_id }),
      });
      const body = (await response.json()) as { selected?: DatasetSummary } & DatasetApiError;
      if (!response.ok || !body.selected) {
        setDatasetState("datasetSelectionError", body.detail ?? body.title ?? "Dataset seçilemedi.");
        setDatasetState("datasetSelectionStatus", "error");
        return;
      }
      setDatasetState("selectedDatasetId", body.selected.dataset_id);
      setDatasetState("datasets", (current) => current.map((item) => item.dataset_id === body.selected?.dataset_id ? body.selected : item));
      setDatasetState("datasetSelectionStatus", "ready");
    } catch (error) {
      setDatasetState("datasetSelectionError", "Dataset seçimi API'ye gönderilemedi. Local API'nin çalıştığını kontrol edin.");
      setDatasetState("datasetSelectionStatus", "error");
    }
  }

  async function inspectFile(file: File) {
    qualityController.current?.abort();
    const requestController = new AbortController();
    qualityController.current = requestController;
    setQualityStatus("pending");
    setQualityError("");
    setQuality(null);
    setMappingKind(null);
    setMapping({});
    setMappingStatus("idle");
    setMappingError("");
    try {
      const response = await fetch("/api/data-quality", {
        method: "POST",
        headers: { "X-Filename": file.name },
        body: file,
        signal: requestController.signal,
      });
      const body = (await response.json()) as { data?: QualityReport } & ApiError;
      if (!body.data) {
        setQualityError(body.error?.message ?? "Veri kalite raporu alınamadı.");
        setQualityStatus("error");
        return;
      }
      setQuality(body.data);
      setMappingKind(body.data.kind);
      setMapping(defaultMapping(body.data, body.data.kind));
      setQualityStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setQualityError("Dosya API'ye gönderilemedi. Local API'nin çalıştığını kontrol edin.");
      setQualityStatus("error");
    }
  }

  function update(name: keyof FormState, value: string) {
    const nextForm = { ...form, [name]: value };
    setForm(nextForm);
    void calculate(nextForm);
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void calculate(form);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Ana menü">
        <div className="brand"><span>DCA</span>BOT</div>
        <nav>
          <a className={`nav-item ${savedRunView === "studio" ? "active" : ""}`} href="#studio" onClick={() => setSavedRunsState("savedRunView", "studio")}><span className="nav-icon">▦</span>Bot stüdyosu</a>
          <a className="nav-item disabled" href="#settings"><span className="nav-icon">⚙</span>Ayarlar</a>
          <a className="nav-item disabled" href="#plans"><span className="nav-icon">▤</span>Planlar</a>
          <a className={`nav-item ${savedRunView !== "studio" ? "active" : ""}`} href="#history" onClick={(event) => { event.preventDefault(); openSavedRuns(); }}><span className="nav-icon">◷</span>Geçmiş</a>
        </nav>
        <div className="sidebar-footer"><span className="nav-icon">⚙</span>Uygulama ayarları</div>
      </aside>

      <main className="main-content" id="studio">
        <header className="topbar">
          <h1>{savedRunView === "studio" ? "Bot stüdyosu" : "Saved Runs"}</h1>
          <div className="topbar-meta">
            <span className="mode-chip"><span className="mode-dot" /> OFFLINE DEMO</span>
            <span className="data-status"><span className="online-dot" />Public veri</span>
          </div>
        </header>

        {savedRunView !== "studio" && <div className="saved-runs-workspace"><SavedRunsPanel view={savedRunView} runs={savedRuns} listStatus={savedRunsStatus} listError={savedRunsError} detail={savedRunDetail} detailStatus={savedRunDetailStatus} detailError={savedRunDetailError} onOpenDetail={(runId) => void openSavedRunDetail(runId)} onBackToList={openSavedRuns} compareSelection={savedRunCompareSelection} onToggleCompareSelection={toggleCompareSelection} onOpenCompare={() => void openSavedRunCompare()} compareDetails={savedRunCompareDetails} compareStatus={savedRunCompareStatus} compareError={savedRunCompareError} /></div>}
        {savedRunView === "studio" && <div className="workspace">
          <section className="panel builder-panel" aria-labelledby="builder-title">
            <div className="panel-heading"><div><p className="eyebrow">CONFIGURATION</p><h2 id="builder-title">Bot stüdyosu</h2></div><span className="revision">r{preview?.revision ?? "—"}</span></div>
            <form onSubmit={submit} noValidate>
              <Field label="Anchor fiyatı" name="anchor" value={form.anchor} suffix="USDT" error={errors.anchor} onChange={(value) => update("anchor", value)} />
              <Field label="Safety miktarı" name="safety_qty" value={form.safety_qty} suffix="BTC" error={errors.safety_qty} onChange={(value) => update("safety_qty", value)} />
              <Field label="Safety sayısı" name="safety_count" value={form.safety_count} suffix="seviye" error={errors.safety_count} onChange={(value) => update("safety_count", value)} type="number" min="0" max="50" />
              <Field label="Sapma" name="deviation" value={form.deviation} suffix="oran" error={errors.deviation} onChange={(value) => update("deviation", value)} />
              <button className="primary-button" type="submit" disabled={status === "pending"}>
                <span aria-hidden="true">▣</span>{status === "pending" ? "Hesaplanıyor…" : "Önizlemeyi hesapla"}
              </button>
            </form>
            <p className="helper-text">Ladder planı ve ekonomik özet, girdi değerlerinize göre gerçek çekirdek hesabından gelir.</p>
            {errors.form && <div className="form-error" role="alert">{errors.form}</div>}
          </section>

          <section className="panel ladder-panel" aria-labelledby="ladder-title">
            <div className="panel-heading"><div><p className="eyebrow">PLAN OUTPUT</p><h2 id="ladder-title">Ladder planı</h2></div><span className={`state-label ${status}`}>{status === "pending" ? "Bekliyor" : status === "error" ? "Hata" : "Güncel"}</span></div>
            {preview ? <div className="table-wrap"><table><thead><tr><th>Seviye</th><th>Fiyat (USDT)</th><th>Miktar (BTC)</th><th>Notional (USDT)</th></tr></thead><tbody>{preview.levels.map((level) => <tr key={level.index}><td>{level.index}</td><td>{level.price}</td><td>{level.qty}</td><td>{level.notional}</td></tr>)}</tbody><tfoot><tr><td>TOPLAM</td><td>—</td><td>—</td><td>{preview.planned_gross_notional}</td></tr></tfoot></table></div> : <div className="empty-state">İlk önizleme hazırlanıyor…</div>}
            <div className="table-note"><span className="note-icon">↳</span> Form değiştiğinde sonuç revision {preview?.revision ?? "—"} ile eşleştirilir; eski yanıt yeni ayarı ezemez.</div>
          </section>

           <section className="panel summary-panel" aria-labelledby="summary-title">
            <div className="panel-heading"><div><p className="eyebrow">ECONOMICS</p><h2 id="summary-title">Ekonomik özet</h2></div></div>
            {preview ? <><Metric label="Planlanan brüt notional" value={preview.planned_gross_notional} unit={preview.quote_asset} /><Metric label="Tahmini başlangıç marjı" value={preview.estimated_initial_margin} unit={preview.quote_asset} /><div className="assumption"><div className="assumption-title"><span className="warning-icon">!</span>Teorik tam dolum varsayımı</div><p>{preview.assumption}</p></div></> : <div className="empty-state">Sonuç bekleniyor…</div>}
           </section>

          <BinancePublicSnapshotPanel snapshot={binancePublicSnapshot} status={binancePublicSnapshotStatus} error={binancePublicSnapshotError} onRetry={() => void loadBinancePublicSnapshot()} />

           <DatasetCatalogPanel
            datasets={datasets}
            status={datasetCatalogStatus}
            error={datasetCatalogError}
            filter={datasetFilter}
            activeDatasetId={activeDatasetId}
            selectedDatasetId={selectedDatasetId}
            selectionStatus={datasetSelectionStatus}
            selectionError={datasetSelectionError}
            downloadJob={downloadJob}
            downloadUiStatus={downloadUiStatus}
            downloadError={downloadError}
            preflight={datasetPreflight}
            preflightStatus={datasetPreflightStatus}
            preflightError={datasetPreflightError}
            historicalProfiles={historicalProfiles}
            historicalProfilesStatus={historicalProfilesStatus}
            historicalProfilesError={historicalProfilesError}
            selectedHistoricalProfileId={selectedHistoricalProfileId}
            onHistoricalProfileChange={(profileId) => void selectHistoricalProfile(profileId)}
            onRetryHistoricalProfiles={() => void loadHistoricalProfiles()}
            runPlan={datasetRunPlan}
            runPlanStatus={datasetRunPlanStatus}
            runPlanError={datasetRunPlanError}
            simulation={historicalSimulation}
            simulationStatus={historicalSimulationStatus}
            simulationError={historicalSimulationError}
            chartData={historicalChartData}
            chartStatus={historicalChartStatus}
            chartError={historicalChartError}
            historicalSaveStatus={historicalSaveStatus}
            historicalSaveError={historicalSaveError}
            onFilterChange={setDatasetFilter}
            onDatasetFocus={setActiveDatasetId}
            onSelect={(dataset) => void selectDataset(dataset)}
            onStartDownload={(dataset) => void startDatasetDownload(dataset)}
            onCancelDownload={() => void cancelDatasetDownload()}
            onRetryDownload={(dataset) => void startDatasetDownload(dataset)}
            onStartHistoricalSimulation={() => void startHistoricalSimulation()}
            onSaveHistoricalRun={() => void saveHistoricalRun()}
            onOpenSavedRuns={openSavedRuns}
          />

          <DataQualityPanel
            quality={quality}
            mappingKind={mappingKind}
            status={qualityStatus}
            error={qualityError}
            mapping={mapping}
            mappingStatus={mappingStatus}
            mappingError={mappingError}
            onFile={inspectFile}
            onKindChange={(kind) => {
              setMappingKind(kind);
              setMapping(kind && quality ? defaultMapping(quality, kind) : {});
              setMappingStatus("idle");
              setMappingError("");
            }}
            onMappingChange={(key, value) => {
              setMapping((current) => ({ ...current, [key]: value }));
              setMappingStatus("idle");
              setMappingError("");
            }}
            onValidateMapping={() => {
              const result = validateMapping(quality, mappingKind, mapping);
              setMappingStatus(result ? "error" : "valid");
              setMappingError(result);
            }}
          />
        </div>}
        <footer className="statusbar"><span><span className="online-dot" />Local-only çalışma</span><span>Credential gerekmez</span><span>{preview?.symbol ?? "BTCUSDT"}</span></footer>
      </main>
    </div>
  );
}

function mappingTargets(kind: QualityReport["kind"]): MappingTarget[] {
  return kind === "trade" ? TRADE_MAPPING_TARGETS : BAR_MAPPING_TARGETS;
}

function defaultMapping(report: QualityReport, kind: QualityReport["kind"]): Record<string, string> {
  return Object.fromEntries(mappingTargets(kind).map(({ key }) => [key, report.headers.includes(key) ? key : ""]));
}

function validateMapping(report: QualityReport | null, kind: QualityReport["kind"], mapping: Record<string, string>): string {
  if (!report || !kind) return "Önce veri tipini seçin.";
  const targets = mappingTargets(kind);
  const missing = targets.filter(({ key }) => !mapping[key]).map(({ label }) => label);
  if (missing.length) return `Eksik eşleme: ${missing.join(", ")}.`;
  const selected = targets.map(({ key }) => mapping[key]);
  if (new Set(selected).size !== selected.length) return "Aynı kaynak kolonu birden fazla canonical alana eşlenemez.";
  return "";
}

function DataQualityPanel({
  quality,
  mappingKind,
  status,
  error,
  mapping,
  mappingStatus,
  mappingError,
  onFile,
  onKindChange,
  onMappingChange,
  onValidateMapping,
}: {
  quality: QualityReport | null;
  mappingKind: QualityReport["kind"];
  status: "idle" | "pending" | "ready" | "error";
  error: string;
  mapping: Record<string, string>;
  mappingStatus: "idle" | "valid" | "error";
  mappingError: string;
  onFile: (file: File) => void;
  onKindChange: (kind: QualityReport["kind"]) => void;
  onMappingChange: (key: string, value: string) => void;
  onValidateMapping: () => void;
}) {
  const statusLabel = quality?.status === "PASS_WITH_WARNINGS" ? "Uyarılı" : quality?.status === "REJECTED" ? "Reddedildi" : "Temiz";
  return (
    <section className="panel data-panel" aria-labelledby="data-title">
      <div className="panel-heading"><div><p className="eyebrow">HISTORICAL DATA</p><h2 id="data-title">Veri merkezi</h2></div><span className={`quality-label ${quality?.status.toLowerCase() ?? status}`}>{status === "pending" ? "Okunuyor" : quality ? statusLabel : "Dosya bekliyor"}</span></div>
      <div className="data-toolbar">
        <div><strong>Yerel CSV veya ZIP seç</strong><p>Dosya yalnızca bu local demo API'sinde okunur; kalıcı kayıt yapılmaz.</p></div>
        <label className="file-button">Dosya seç<input type="file" accept=".csv,.zip,text/csv,application/zip" onChange={(event) => { const file = event.target.files?.[0]; if (file) void onFile(file); }} /></label>
      </div>
      {error && <div className="form-error" role="alert">{error}</div>}
      {quality && <>
        <div className="quality-summary">
          <Metric label="Kaynak" value={quality.source_filename} unit={`${formatBytes(quality.source_bytes)} · ${quality.row_count} satır`} />
          <Metric label="Şema" value={quality.kind ?? "Belirsiz"} unit={quality.symbol ?? "symbol belirtilmedi"} />
          <Metric label="Timestamp" value={quality.timestamp.unit ?? "—"} unit={quality.timestamp.timezone ?? "—"} />
          <Metric label="Bulgular" value={`${quality.error_count} / ${quality.warning_count}`} unit="hata / uyarı" />
        </div>
        <div className="quality-meta"><span>SHA-256: <code>{quality.source_sha256}</code></span><span>Gap: {quality.gaps.count} · Duplicate: {quality.duplicates.same + quality.duplicates.conflicts}</span></div>
        {!quality.kind && <div className="mapping-kind"><label htmlFor="mapping-kind">Veri tipi</label><select id="mapping-kind" aria-label="Veri tipi" value={mappingKind ?? ""} onChange={(event) => onKindChange(event.target.value === "bar" || event.target.value === "trade" ? event.target.value : null)}><option value="">Bar veya trade seçin</option><option value="bar">Bar / OHLCV</option><option value="trade">Trade / işlemler</option></select><p>Şema reddedildi; mapping yalnızca header eşleşmesini hazırlamak için gösterilir.</p></div>}
        {mappingKind && <div className="mapping-section">
          <div className="mapping-heading"><div><h3>Canonical alan eşleme</h3><p>Exact kolonlar otomatik seçildi; bu fazda eşleme yalnızca yerel doğrulanır.</p></div><button className="secondary-button" type="button" onClick={onValidateMapping}>Eşlemeyi doğrula</button></div>
          <div className="mapping-grid">{mappingTargets(mappingKind).map(({ key, label }) => <label className="mapping-row" key={key}><span>{label}<small>{key}</small></span><select aria-label={`${label} eşlemesi`} value={mapping[key] ?? ""} onChange={(event) => onMappingChange(key, event.target.value)}><option value="">Kaynak kolon seçin</option>{quality.headers.map((header) => <option key={header} value={header}>{header}</option>)}</select></label>)}</div>
          {mappingStatus === "valid" && <div className="mapping-success" role="status">Eşleme tamamlandı. Kalıcı import bu fazın dışında.</div>}
          {mappingStatus === "error" && <div className="form-error" role="alert">{mappingError}</div>}
        </div>}
        {quality.issues.length > 0 && <div className="quality-issues"><h3>Kalite bulguları</h3>{quality.issues.slice(0, 4).map((issue, index) => <div className={`issue-row ${issue.severity}`} key={`${issue.code}-${index}`}><span>{issue.severity === "error" ? "Hata" : "Uyarı"}</span><p>{issue.message}{issue.row ? ` Satır ${issue.row}.` : ""}</p></div>)}</div>}
      </>}
      {!quality && status !== "pending" && !error && <div className="empty-state data-empty">Bir dosya seçerek header, timestamp ve kalite bulgularını görün.</div>}
    </section>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function Field({ label, name, value, suffix, error, onChange, type = "text", min, max }: { label: string; name: string; value: string; suffix: string; error?: string; onChange: (value: string) => void; type?: string; min?: string; max?: string }) {
  return <label className={`field ${error ? "has-error" : ""}`}><span className="field-label">{label}</span><span className="input-wrap"><input aria-label={label} name={name} value={value} type={type} min={min} max={max} onChange={(event) => onChange(event.target.value)} aria-invalid={Boolean(error)} aria-describedby={error ? `${name}-error` : undefined} /><span className="suffix">{suffix}</span></span>{error && <span className="field-error" id={`${name}-error`} role="alert">{error}</span>}</label>;
}

function Metric({ label, value, unit }: { label: string; value: string; unit: string }) {
  return <div className="metric"><span className="metric-label">{label}</span><strong>{value}</strong><span className="metric-unit">{unit}</span></div>;
}

export default App;
