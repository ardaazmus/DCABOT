import { FormEvent, type Dispatch, type SetStateAction, Suspense, lazy, useEffect, useReducer, useRef, useState, useTransition } from "react";
import { sectionById, type AppSectionId } from "./appSections";
import { SectionNav } from "./SectionNav";
import { NumericParameter, SegmentedControl } from "./forms";
import { BotWizard, readDraftPreviewParams, type WizardExternalFill, type WizardPreviewParams } from "./BotWizard";
import { FuturesDcaForm } from "./FuturesDcaForm";
import { BotCreateView, type BotCreateType } from "./BotCreateView";
import { HeroChartPanel } from "./HeroChartPanel";
import { previewToPriceLines } from "./previewOverlay";
import { BotDetailView } from "./BotDetailView";
import { DealDetailView } from "./DealDetailView";
import { BotContextHeader, BotTable } from "./BotTable";
import { Banner, ConfirmDialog, NotificationCenter, NotificationStore, ToastStack } from "./notifications";
import { THEME_STORAGE_KEY, applyTheme, resolveTheme, type Theme } from "./theme";
import { useI18n } from "./i18n";
import { RebalancePanel, isRebalanceValuation, parsePairLines, type RebalanceValuation } from "./RebalancePanel";
import { PaperPanel, isPaperPrints, isPaperSnapshot, type PaperOrderDraft, type PaperPrint, type PaperSnapshot } from "./PaperPanel";
import { TemplatePanel, isTemplateBindResponse, isTemplateDetail, isTemplateDiffRows, isTemplateMetaList, type TemplateBindPayload, type TemplateBindResult, type TemplateDetail, type TemplateDiffRow, type TemplateImportPayload, type TemplateMeta } from "./TemplatePanel";
import { RebalancePlanPanel, isRebalanceDisclosureView, isRebalancePlanView, type RebalanceCandidateView, type RebalanceDisclosePayload, type RebalanceDisclosureView, type RebalancePlanPayload, type RebalancePlanView } from "./RebalancePlanPanel";
import { SignalPanel, isSignalCandidateView, isSignalReadinessView, type SignalAssessPayload, type SignalBindPayload, type SignalCandidateView, type SignalReadinessView } from "./SignalPanel";
import { FuturesPanel, isFuturesFundingView, isFuturesGridView, isFuturesPnlView, isFuturesTrailingView, type FuturesFundingPayload, type FuturesFundingView, type FuturesGridPayload, type FuturesGridView, type FuturesPnlPayload, type FuturesPnlView, type FuturesTrailingArmPayload, type FuturesTrailingObservePayload, type FuturesTrailingView } from "./FuturesPanel";
import { TwoLegPanel, isTwoLegProjectionView, type TwoLegFillPayload, type TwoLegProjectionView } from "./TwoLegPanel";
import { BotPanel, isBotCheckView, isBotDcaDealCountResponse, isBotDcaPerformanceResponse, isBotProfileView, type BotBindPayload, type BotCheckView, type BotDcaPerformanceView, type BotListsPayload, type BotProfileView, type BotRegisterPayload } from "./BotPanel";
import { DealPanel, isDealReplayView, type DealAppendPayload, type DealBulkAction, type DealCreatePayload, type DealEventView, type DealLifecycleView } from "./DealPanel";
import { ExitPanel, isBreakevenView, isPercentStateView, isTrailingBindView, type BreakevenView, type PercentStateView, type TrailingBindPayload, type TrailingBindView } from "./ExitPanel";
import { BackupPanel, isBackupManifestList, isBackupVerdictView, type BackupManifestView, type BackupVerdictView } from "./BackupPanel";
import { DatastorePanel } from "./DatastorePanel";
import { GridSkeletonCard } from "./GridSkeletonCard";
import { AssistantPanel } from "./AssistantPanel";
import { DashboardPanel, isDashboardView, type DashboardView } from "./DashboardPanel";
import { LabPanel } from "./LabPanel";
import { isLiquidationStatusView, type LiquidationStatusView } from "./LiquidationStatusSection";
import { SystemStatusCard, isCapabilitiesView, type CapabilitiesView } from "./SystemStatusCard";
import { TimelinePanel, isTimelineFrameView, type TimelineFrameView } from "./TimelinePanel";
import { RecurringPanel, isRecurringScheduleView, type RecurringSchedulePayload, type RecurringScheduleView } from "./RecurringPanel";
import { EventPanel, isCenterEventList, type CenterEventView } from "./EventPanel";
import { KillSwitchBanner, RiskPanel, isCanaryStatusView, isRiskExplainView, type CanaryStatusView, type RiskExplainPayload, type RiskExplainView } from "./RiskPanel";
import { CorrelationPanel, isCorrelationGateResponse, type CorrelationGatePayload, type CorrelationGateResult } from "./CorrelationPanel";
import { DepthPanel, isDepthBookResponse, type DepthBook } from "./DepthPanel";
import { IndicatorRegistryPanel, isIndicatorRegistryResponse } from "./IndicatorRegistryPanel";
import { RegimePanel, isRegimeGateResponse, type RegimeGatePayload, type RegimeGateResult } from "./RegimePanel";
import { SystemStatusPanel, isSystemStatusResponse, type SystemStatusView } from "./SystemStatusPanel";
const DatasetCatalogPanel = lazy(() => import("./DatasetCatalogPanel").then((m) => ({ default: m.DatasetCatalogPanel })));
import { HistoricalProfileStatus } from "./HistoricalProfileSelector";
const SavedRunsPanel = lazy(() => import("./SavedRunsPanel").then((m) => ({ default: m.SavedRunsPanel })));
import { BinancePublicSnapshotPanel, isBinancePublicSnapshot, type BinancePublicSnapshot } from "./BinancePublicSnapshotPanel";
import { isVenueLastPrice, isVenueSymbolList, type VenueSymbol } from "./SymbolSelector";
import { GlobalSymbolSelect } from "./GlobalSymbolSelect";
import { StatTile } from "./StatTile";
import { buildDetailHash, buildSectionHash, parseHashRoute } from "./hashRoute";
import { isVenueTicker24h, MarketTickerPanel, type VenueTicker24h } from "./MarketTickerPanel";
import { DcaPlaceConfirmDialog, DcaSessionCreateForm, DcaSessionDetailPanel, DcaSessionsPanel, isDcaSessionCreateResponse, isDcaSessionDecisionResponse, isDcaSessionDetailResponse, isDcaSessionList, isDcaSessionPlaceResponse, type DcaPlaceDraft, type DcaSessionCreateFields, type DcaSessionDecision, type DcaSessionDetail, type DcaSessionRow } from "./DcaSessionsPanel";
import { SweepOptimizePanel, isSweepOptimizeResponse, type SweepOptimizePayload, type SweepOptimizeResult, type SweepTrialOverrides } from "./SweepOptimizePanel";
import { OverfittingPanel, isOverfittingResponse, type OverfittingPayload, type OverfittingResult } from "./OverfittingPanel";
import { PortfolioPanel, isPortfolioDcaPerformanceResponse, type PortfolioDcaPerformance } from "./PortfolioPanel";
import { PresetComparePanel, isPresetCompareResponse, type PresetComparePayload, type PresetCompareResult } from "./PresetComparePanel";
import { FullPreviewPanel, isFullPreviewResponse, isFuturesStyleConfig, mergeConfigOverrides, studioLeverageIssue, type FullPreview, type FullPreviewStatus } from "./FullPreviewPanel";
import { INDICATOR_ROUTES, IndicatorPanel, indicatorRequestBody, isBollingerResponse, isIndicatorResponse, isMacdResponse, isStochRsiResponse, type IndicatorKind, type IndicatorSeries, type IndicatorStatus } from "./IndicatorPanel";
import { BinanceAccountPanel, isBinanceAccountSnapshot, isBinanceOpenOrdersSnapshot, isTestnetCredentialNotConfigured, type BinanceAccountSnapshot, type BinanceOpenOrdersSnapshot } from "./BinanceAccountPanel";
import { DatasetCatalogStatus, DatasetDownloadJob, DatasetFilter, DatasetPreflight, DatasetRunPlan, DownloadJobUiStatus, DatasetSelectionStatus, DatasetSummary, HistoricalChartBar, HistoricalChartData, HistoricalProfile, HistoricalSimulationResult, isActiveDownloadJob } from "./datasetCatalog";
import { SavedRunApiError, SavedRunDetail, SavedRunListItem, SavedRunListResponse, SavedRunSaveResponse } from "./savedRuns";

type FormState = {
  anchor: string;
  safety_qty: string;
  safety_count: string;
  deviation: string;
  leverage: string;
  direction: string;
  margin_mode: string;
};

type Level = { index: number; price: string; qty: string; notional: string };
type Preview = {
  symbol: string;
  anchor?: string;
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
  leverage: "1",
  direction: "LONG",
  margin_mode: "ISOLATED",
};

/* Faz 17 A.3: overlay ön-doğrulama desenleri (BotWizard emsali — girdi
 * doğrulama kategorisi, finansal hesap değil; yetki backend'dedir). */
const PREVIEW_DECIMAL = /^(?:0|[1-9]\d*)(?:\.\d+)?$/;
const PREVIEW_COUNT = /^(?:0|[1-9]\d*)$/;

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
  savedRunExportStatus: "idle" | "loading" | "ready" | "error";
  savedRunExportError: string;
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
  savedRunExportStatus: "idle",
  savedRunExportError: "",
};

type ConfigState = {
  form: FormState;
  preview: Preview | null;
  errors: Record<string, string>;
  status: "idle" | "pending" | "ready" | "error";
};

const initialConfigState: ConfigState = {
  form: initialForm,
  preview: null,
  errors: {},
  status: "idle",
};

type QualityState = {
  quality: QualityReport | null;
  qualityStatus: "idle" | "pending" | "ready" | "error";
  qualityError: string;
  mappingKind: QualityReport["kind"];
  mapping: Record<string, string>;
  mappingStatus: "idle" | "valid" | "error";
  mappingError: string;
};

const initialQualityState: QualityState = {
  quality: null,
  qualityStatus: "idle",
  qualityError: "",
  mappingKind: null,
  mapping: {},
  mappingStatus: "idle",
  mappingError: "",
};

type BinancePublicState = {
  binancePublicSnapshot: BinancePublicSnapshot | null;
  binancePublicSnapshotStatus: "idle" | "loading" | "ready" | "error";
  binancePublicSnapshotError: string;
  venueSymbols: VenueSymbol[];
  venueSymbolsCount: number;
  venueSymbolsStatus: "idle" | "loading" | "ready" | "error";
  venueSymbolsError: string;
  selectedVenueSymbol: string | null;
  venueLastPrice: { symbol: string; price: string } | null;
  venueLastPriceStatus: "idle" | "loading" | "ready" | "error";
  venueTicker24h: VenueTicker24h | null;
  venueTicker24hStatus: "idle" | "loading" | "ready" | "error";
  venueTicker24hError: string;
};

const DEFAULT_VENUE_SYMBOL = "BTCUSDT";

const initialBinancePublicState: BinancePublicState = {
  binancePublicSnapshot: null,
  binancePublicSnapshotStatus: "idle",
  binancePublicSnapshotError: "",
  venueSymbols: [],
  venueSymbolsCount: 0,
  venueSymbolsStatus: "idle",
  venueSymbolsError: "",
  selectedVenueSymbol: DEFAULT_VENUE_SYMBOL,
  venueLastPrice: null,
  venueLastPriceStatus: "idle",
  venueTicker24h: null,
  venueTicker24hStatus: "idle",
  venueTicker24hError: "",
};

type BinanceAccountState = {
  binanceAccount: BinanceAccountSnapshot | null;
  binanceOpenOrders: BinanceOpenOrdersSnapshot | null;
  binanceAccountStatus: "idle" | "loading" | "ready" | "not_configured" | "error";
  binanceAccountError: string;
};

const initialBinanceAccountState: BinanceAccountState = {
  binanceAccount: null,
  binanceOpenOrders: null,
  binanceAccountStatus: "idle",
  binanceAccountError: "",
};

function initialTheme(): Theme {
  let stored: string | null = null;
  try {
    stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    stored = null;
  }
  return resolveTheme(stored, () => window.matchMedia?.("(prefers-color-scheme: light)").matches ?? false);
}

type ShellState = {
  activeSection: AppSectionId;
  theme: Theme;
};

const initialShellState: ShellState = {
  activeSection: "overview",
  theme: "dark",
};

type RebalanceState = {
  rebalanceHoldingsText: string;
  rebalancePricesText: string;
  rebalanceValuation: RebalanceValuation | null;
  rebalanceStatus: "idle" | "pending" | "ready" | "error";
  rebalanceError: string;
};

const initialRebalanceState: RebalanceState = {
  rebalanceHoldingsText: "BTC 0.01\nUSDT 100",
  rebalancePricesText: "BTC 50000",
  rebalanceValuation: null,
  rebalanceStatus: "idle",
  rebalanceError: "",
};

type PaperState = {
  paperSnapshot: PaperSnapshot | null;
  paperPrints: PaperPrint[];
  paperBusy: boolean;
  paperError: string;
  paperOrderDraft: PaperOrderDraft;
};

const initialPaperState: PaperState = {
  paperSnapshot: null,
  paperPrints: [],
  paperBusy: false,
  paperError: "",
  paperOrderDraft: { symbol: "BTCUSDT", side: "BUY", qty: "0.01", clientOrderId: "c1" },
};

type TemplateState = {
  templateMetas: TemplateMeta[];
  templateDetail: TemplateDetail | null;
  templateBindResult: TemplateBindResult | null;
  templateDiffRows: TemplateDiffRow[];
  templateBusy: boolean;
  templateError: string;
};

const initialTemplateState: TemplateState = {
  templateMetas: [],
  templateDetail: null,
  templateBindResult: null,
  templateDiffRows: [],
  templateBusy: false,
  templateError: "",
};

type RebalancePlanState = {
  rebalancePlan: RebalancePlanView | null;
  rebalanceDisclosure: RebalanceDisclosureView | null;
  rebalanceCandidates: RebalanceCandidateView[];
  rebalancePlanBusy: boolean;
  rebalancePlanError: string;
};

const initialRebalancePlanState: RebalancePlanState = {
  rebalancePlan: null,
  rebalanceDisclosure: null,
  rebalanceCandidates: [],
  rebalancePlanBusy: false,
  rebalancePlanError: "",
};

type SignalState = {
  signalHash: string | null;
  signalReadiness: SignalReadinessView | null;
  signalCandidate: SignalCandidateView | null;
  signalBusy: boolean;
  signalError: string;
};

const initialSignalState: SignalState = {
  signalHash: null,
  signalReadiness: null,
  signalCandidate: null,
  signalBusy: false,
  signalError: "",
};

type FuturesState = {
  futuresGrid: FuturesGridView | null;
  futuresPnl: FuturesPnlView | null;
  futuresTrailing: FuturesTrailingView | null;
  futuresFunding: FuturesFundingView | null;
  futuresBusy: boolean;
  futuresError: string;
};

const initialFuturesState: FuturesState = {
  futuresGrid: null,
  futuresPnl: null,
  futuresTrailing: null,
  futuresFunding: null,
  futuresBusy: false,
  futuresError: "",
};

type TwoLegState = {
  twoLegSession: string;
  twoLegProjection: TwoLegProjectionView | null;
  twoLegBusy: boolean;
  twoLegError: string;
};

const initialTwoLegState: TwoLegState = {
  twoLegSession: "sess-1",
  twoLegProjection: null,
  twoLegBusy: false,
  twoLegError: "",
};

type BotState = {
  botIds: string[];
  botProfile: BotProfileView | null;
  botSessions: Record<string, string>;
  botCheck: BotCheckView | null;
  botBusy: boolean;
  botError: string;
  selectedBotId: string;
  botDealCounts: Record<string, number | null>;
  botDcaPerf: BotDcaPerformanceView | null;
  botDcaActive: number | null;
  botDcaBusy: boolean;
  botDcaError: string;
};

const initialBotState: BotState = {
  botIds: [],
  botProfile: null,
  botSessions: {},
  botCheck: null,
  botBusy: false,
  botError: "",
  selectedBotId: "bot-1",
  botDealCounts: {},
  botDcaPerf: null,
  botDcaActive: null,
  botDcaBusy: false,
  botDcaError: "",
};

type DealBulkResultRow = {
  deal_id: string;
  event_id: string;
  result?: string;
  error?: string;
};

type DealState = {
  dealId: string;
  dealLifecycle: DealLifecycleView | null;
  dealHistory: DealEventView[];
  dealBulkResults: DealBulkResultRow[];
  dealReplayVerified: boolean;
  dealBusy: boolean;
  dealError: string;
};

const initialDealState: DealState = {
  dealId: "deal-1",
  dealLifecycle: null,
  dealHistory: [],
  dealBulkResults: [],
  dealReplayVerified: false,
  dealBusy: false,
  dealError: "",
};

type ExitState = {
  exitBinding: TrailingBindView | null;
  exitPercent: PercentStateView | null;
  exitBreakeven: BreakevenView | null;
  exitBusy: boolean;
  exitError: string;
};

const initialExitState: ExitState = {
  exitBinding: null,
  exitPercent: null,
  exitBreakeven: null,
  exitBusy: false,
  exitError: "",
};

type OpsState = {
  backupList: BackupManifestView[];
  backupVerdict: BackupVerdictView | null;
  backupBusy: boolean;
  backupError: string;
  dashboard: DashboardView | null;
  dashboardBusy: boolean;
  dashboardError: string;
  timelineFrame: TimelineFrameView | null;
  timelineBusy: boolean;
  timelineError: string;
  recurring: RecurringScheduleView | null;
  recurringBusy: boolean;
  recurringError: string;
  centerEvents: CenterEventView[];
  centerBusy: boolean;
  centerError: string;
  riskExplain: RiskExplainView | null;
  riskBusy: boolean;
  riskError: string;
};

const initialOpsState: OpsState = {
  backupList: [],
  backupVerdict: null,
  backupBusy: false,
  backupError: "",
  dashboard: null,
  dashboardBusy: false,
  dashboardError: "",
  timelineFrame: null,
  timelineBusy: false,
  timelineError: "",
  recurring: null,
  recurringBusy: false,
  recurringError: "",
  centerEvents: [],
  centerBusy: false,
  centerError: "",
  riskExplain: null,
  riskBusy: false,
  riskError: "",
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


function isRecordWithSnapshot(value: unknown): value is Record<string, unknown> & { snapshot: PaperSnapshot; prints?: unknown } {
  return typeof value === "object" && value !== null && isPaperSnapshot((value as Record<string, unknown>).snapshot);
}

function App() {
  const [configState, setConfigState] = useReducerGroup(initialConfigState);
  const { lang, setLang, t } = useI18n();
  const { form, preview, errors, status } = configState;
  const setForm: Dispatch<SetStateAction<FormState>> = (value) => setConfigState("form", value);
  const setPreview: Dispatch<SetStateAction<Preview | null>> = (value) => setConfigState("preview", value);
  const setErrors: Dispatch<SetStateAction<Record<string, string>>> = (value) => setConfigState("errors", value);
  const setStatus: Dispatch<SetStateAction<"idle" | "pending" | "ready" | "error">> = (value) => setConfigState("status", value);
  const [qualityState, setQualityState] = useReducerGroup(initialQualityState);
  const { quality, qualityStatus, qualityError, mappingKind, mapping, mappingStatus, mappingError } = qualityState;
  const setQuality: Dispatch<SetStateAction<QualityReport | null>> = (value) => setQualityState("quality", value);
  const setQualityStatus: Dispatch<SetStateAction<"idle" | "pending" | "ready" | "error">> = (value) => setQualityState("qualityStatus", value);
  const setQualityError: Dispatch<SetStateAction<string>> = (value) => setQualityState("qualityError", value);
  const setMappingKind: Dispatch<SetStateAction<QualityReport["kind"]>> = (value) => setQualityState("mappingKind", value);
  const setMapping: Dispatch<SetStateAction<Record<string, string>>> = (value) => setQualityState("mapping", value);
  const setMappingStatus: Dispatch<SetStateAction<"idle" | "valid" | "error">> = (value) => setQualityState("mappingStatus", value);
  const setMappingError: Dispatch<SetStateAction<string>> = (value) => setQualityState("mappingError", value);
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
    savedRunExportStatus,
    savedRunExportError,
  } = savedRunsState;
  const [binancePublicState, setBinancePublicState] = useReducerGroup(initialBinancePublicState);
  const { binancePublicSnapshot, binancePublicSnapshotStatus, binancePublicSnapshotError, venueSymbols, venueSymbolsCount, venueSymbolsStatus, venueSymbolsError, selectedVenueSymbol, venueLastPrice, venueLastPriceStatus, venueTicker24h, venueTicker24hStatus, venueTicker24hError } = binancePublicState;
  const setBinancePublicSnapshot: Dispatch<SetStateAction<BinancePublicSnapshot | null>> = (value) => setBinancePublicState("binancePublicSnapshot", value);
  const setBinancePublicSnapshotStatus: Dispatch<SetStateAction<"idle" | "loading" | "ready" | "error">> = (value) => setBinancePublicState("binancePublicSnapshotStatus", value);
  const setBinancePublicSnapshotError: Dispatch<SetStateAction<string>> = (value) => setBinancePublicState("binancePublicSnapshotError", value);
  const setVenueSymbols: Dispatch<SetStateAction<VenueSymbol[]>> = (value) => setBinancePublicState("venueSymbols", value);
  const setVenueSymbolsCount: Dispatch<SetStateAction<number>> = (value) => setBinancePublicState("venueSymbolsCount", value);
  const setVenueSymbolsStatus: Dispatch<SetStateAction<"idle" | "loading" | "ready" | "error">> = (value) => setBinancePublicState("venueSymbolsStatus", value);
  const setVenueSymbolsError: Dispatch<SetStateAction<string>> = (value) => setBinancePublicState("venueSymbolsError", value);
  const setSelectedVenueSymbol: Dispatch<SetStateAction<string | null>> = (value) => setBinancePublicState("selectedVenueSymbol", value);
  const setVenueLastPrice: Dispatch<SetStateAction<{ symbol: string; price: string } | null>> = (value) => setBinancePublicState("venueLastPrice", value);
  const setVenueLastPriceStatus: Dispatch<SetStateAction<"idle" | "loading" | "ready" | "error">> = (value) => setBinancePublicState("venueLastPriceStatus", value);
  const setVenueTicker24h: Dispatch<SetStateAction<VenueTicker24h | null>> = (value) => setBinancePublicState("venueTicker24h", value);
  const setVenueTicker24hStatus: Dispatch<SetStateAction<"idle" | "loading" | "ready" | "error">> = (value) => setBinancePublicState("venueTicker24hStatus", value);
  const setVenueTicker24hError: Dispatch<SetStateAction<string>> = (value) => setBinancePublicState("venueTicker24hError", value);
  const [binanceAccountState, setBinanceAccountState] = useReducerGroup(initialBinanceAccountState);
  const { binanceAccount, binanceOpenOrders, binanceAccountStatus, binanceAccountError } = binanceAccountState;
  const setBinanceAccount: Dispatch<SetStateAction<BinanceAccountSnapshot | null>> = (value) => setBinanceAccountState("binanceAccount", value);
  const setBinanceOpenOrders: Dispatch<SetStateAction<BinanceOpenOrdersSnapshot | null>> = (value) => setBinanceAccountState("binanceOpenOrders", value);
  const setBinanceAccountStatus: Dispatch<SetStateAction<"idle" | "loading" | "ready" | "not_configured" | "error">> = (value) => setBinanceAccountState("binanceAccountStatus", value);
  const [shellState, setShellState] = useReducerGroup({...initialShellState, theme: initialTheme()});
  const { activeSection, theme } = shellState;
  const [createView, setCreateView] = useState<BotCreateType | null>(null);
  const [createPreview, setCreatePreview] = useState<Preview | null>(null);
  const [createPreviewNote, setCreatePreviewNote] = useState("");
  const [detailView, setDetailView] = useState<{ kind: "bot"; botId: string } | { kind: "deal"; dealId: string } | null>(null);
  const [indicatorKind, setIndicatorKind] = useState<IndicatorKind>("sma");
  const [indicatorSeries, setIndicatorSeries] = useState<IndicatorSeries | null>(null);
  const [indicatorStatus, setIndicatorStatus] = useState<IndicatorStatus>("idle");
  const [indicatorError, setIndicatorError] = useState("");
  const [paperConfig, setPaperConfig] = useState<Record<string, unknown> | null>(null);
  const [fullPreview, setFullPreview] = useState<FullPreview | null>(null);
  const [fullPreviewStatus, setFullPreviewStatus] = useState<FullPreviewStatus>("idle");
  const [fullPreviewError, setFullPreviewError] = useState("");
  const [dcaSessionCreateBusy, setDcaSessionCreateBusy] = useState(false);
  const [dcaSessionCreateError, setDcaSessionCreateError] = useState("");
  const [dcaSessionCreatedId, setDcaSessionCreatedId] = useState<string | null>(null);
  const [dcaSessions, setDcaSessions] = useState<DcaSessionRow[]>([]);
  const [dcaSessionsBusy, setDcaSessionsBusy] = useState(false);
  const [dcaSessionsError, setDcaSessionsError] = useState("");
  const [dcaSelectedId, setDcaSelectedId] = useState<string | null>(null);
  const [dcaDetail, setDcaDetail] = useState<DcaSessionDetail | null>(null);
  const [dcaDecision, setDcaDecision] = useState<DcaSessionDecision>(null);
  const [dcaDecisionLoaded, setDcaDecisionLoaded] = useState(false);
  const [dcaDetailBusy, setDcaDetailBusy] = useState(false);
  const [dcaDetailError, setDcaDetailError] = useState("");
  const [dcaSyncBusyRole, setDcaSyncBusyRole] = useState<string | null>(null);
  const [dcaSyncError, setDcaSyncError] = useState("");
  const [dcaSyncNotice, setDcaSyncNotice] = useState("");
  const [dcaPlaceDraft, setDcaPlaceDraft] = useState<DcaPlaceDraft | null>(null);
  const [dcaPlaceBusy, setDcaPlaceBusy] = useState(false);
  const [dcaPlaceError, setDcaPlaceError] = useState("");
  const [dcaPlaceNotice, setDcaPlaceNotice] = useState("");
  const [dcaPlaceDialogError, setDcaPlaceDialogError] = useState("");
  const [paperFillBusy, setPaperFillBusy] = useState(false);
  const [paperFillError, setPaperFillError] = useState("");
  const [paperFillNotice, setPaperFillNotice] = useState("");
  const [sweepBusy, setSweepBusy] = useState(false);
  const [sweepError, setSweepError] = useState("");
  const [sweepResult, setSweepResult] = useState<SweepOptimizeResult | null>(null);
  const [overfitBusy, setOverfitBusy] = useState(false);
  const [overfitError, setOverfitError] = useState("");
  const [overfitResult, setOverfitResult] = useState<OverfittingResult | null>(null);
  const [compareBusy, setCompareBusy] = useState(false);
  const [compareError, setCompareError] = useState("");
  const [compareResult, setCompareResult] = useState<PresetCompareResult | null>(null);
  const [portfolioData, setPortfolioData] = useState<PortfolioDcaPerformance | null>(null);
  const [portfolioBusy, setPortfolioBusy] = useState(false);
  const [portfolioError, setPortfolioError] = useState("");
  const [corrClosesX, setCorrClosesX] = useState<string[]>([]);
  const [corrClosesY, setCorrClosesY] = useState<string[]>([]);
  const [corrLabelX, setCorrLabelX] = useState("");
  const [corrLabelY, setCorrLabelY] = useState("");
  const [corrSeriesBusy, setCorrSeriesBusy] = useState(false);
  const [corrSeriesError, setCorrSeriesError] = useState("");
  const [corrBusy, setCorrBusy] = useState(false);
  const [corrError, setCorrError] = useState("");
  const [corrResult, setCorrResult] = useState<CorrelationGateResult | null>(null);
  const [regimeBars, setRegimeBars] = useState<HistoricalChartBar[]>([]);
  const [regimeLabel, setRegimeLabel] = useState("");
  const [regimeSeriesBusy, setRegimeSeriesBusy] = useState(false);
  const [regimeSeriesError, setRegimeSeriesError] = useState("");
  const [regimeBusy, setRegimeBusy] = useState(false);
  const [regimeError, setRegimeError] = useState("");
  const [regimeResult, setRegimeResult] = useState<RegimeGateResult | null>(null);
  const [registryNames, setRegistryNames] = useState<string[]>([]);
  const [registryBusy, setRegistryBusy] = useState(false);
  const [registryError, setRegistryError] = useState("");
  const [systemStatus, setSystemStatus] = useState<SystemStatusView | null>(null);
  const [systemBusy, setSystemBusy] = useState(false);
  const [systemError, setSystemError] = useState("");
  const [depthBook, setDepthBook] = useState<DepthBook | null>(null);
  const [depthBusy, setDepthBusy] = useState(false);
  const [depthError, setDepthError] = useState("");
  const [sweepFill, setSweepFill] = useState<WizardExternalFill>(null);
  const sweepFillNonce = useRef(0);
  const [canary, setCanary] = useState<CanaryStatusView | null>(null);
  const [canaryBusy, setCanaryBusy] = useState(false);
  const [canaryError, setCanaryError] = useState("");
  const [capabilities, setCapabilities] = useState<CapabilitiesView | null>(null);
  const [capabilitiesBusy, setCapabilitiesBusy] = useState(false);
  const [capabilitiesError, setCapabilitiesError] = useState("");
  const [liquidation, setLiquidation] = useState<LiquidationStatusView | null>(null);
  const [liquidationBusy, setLiquidationBusy] = useState(false);
  const [liquidationError, setLiquidationError] = useState("");
  const setActiveSection: Dispatch<SetStateAction<AppSectionId>> = (value) => setShellState("activeSection", value);
  const setTheme: Dispatch<SetStateAction<Theme>> = (value) => setShellState("theme", value);
  const setBinanceAccountError: Dispatch<SetStateAction<string>> = (value) => setBinanceAccountState("binanceAccountError", value);
  const [rebalanceState, setRebalanceState] = useReducerGroup(initialRebalanceState);
  const { rebalanceHoldingsText, rebalancePricesText, rebalanceValuation, rebalanceStatus, rebalanceError } = rebalanceState;
  const setRebalanceHoldingsText: Dispatch<SetStateAction<string>> = (value) => setRebalanceState("rebalanceHoldingsText", value);
  const setRebalancePricesText: Dispatch<SetStateAction<string>> = (value) => setRebalanceState("rebalancePricesText", value);
  const setRebalanceValuation: Dispatch<SetStateAction<RebalanceValuation | null>> = (value) => setRebalanceState("rebalanceValuation", value);
  const setRebalanceStatus: Dispatch<SetStateAction<"idle" | "pending" | "ready" | "error">> = (value) => setRebalanceState("rebalanceStatus", value);
  const setRebalanceError: Dispatch<SetStateAction<string>> = (value) => setRebalanceState("rebalanceError", value);
  const [paperState, setPaperState] = useReducerGroup(initialPaperState);
  const { paperSnapshot, paperPrints, paperBusy, paperError, paperOrderDraft } = paperState;
  const setPaperSnapshot: Dispatch<SetStateAction<PaperSnapshot | null>> = (value) => setPaperState("paperSnapshot", value);
  const setPaperPrints: Dispatch<SetStateAction<PaperPrint[]>> = (value) => setPaperState("paperPrints", value);
  const setPaperBusy: Dispatch<SetStateAction<boolean>> = (value) => setPaperState("paperBusy", value);
  const setPaperError: Dispatch<SetStateAction<string>> = (value) => setPaperState("paperError", value);
  const setPaperOrderDraft: Dispatch<SetStateAction<PaperOrderDraft>> = (value) => setPaperState("paperOrderDraft", value);
  const [templateState, setTemplateState] = useReducerGroup(initialTemplateState);
  const { templateMetas, templateDetail, templateBindResult, templateDiffRows, templateBusy, templateError } = templateState;
  const setTemplateMetas: Dispatch<SetStateAction<TemplateMeta[]>> = (value) => setTemplateState("templateMetas", value);
  const setTemplateDetail: Dispatch<SetStateAction<TemplateDetail | null>> = (value) => setTemplateState("templateDetail", value);
  const setTemplateBindResult: Dispatch<SetStateAction<TemplateBindResult | null>> = (value) => setTemplateState("templateBindResult", value);
  const setTemplateDiffRows: Dispatch<SetStateAction<TemplateDiffRow[]>> = (value) => setTemplateState("templateDiffRows", value);
  const setTemplateBusy: Dispatch<SetStateAction<boolean>> = (value) => setTemplateState("templateBusy", value);
  const setTemplateError: Dispatch<SetStateAction<string>> = (value) => setTemplateState("templateError", value);
  const [rebalancePlanState, setRebalancePlanState] = useReducerGroup(initialRebalancePlanState);
  const { rebalancePlan, rebalanceDisclosure, rebalanceCandidates, rebalancePlanBusy, rebalancePlanError } = rebalancePlanState;
  const setRebalancePlan: Dispatch<SetStateAction<RebalancePlanView | null>> = (value) => setRebalancePlanState("rebalancePlan", value);
  const setRebalanceDisclosure: Dispatch<SetStateAction<RebalanceDisclosureView | null>> = (value) => setRebalancePlanState("rebalanceDisclosure", value);
  const setRebalanceCandidates: Dispatch<SetStateAction<RebalanceCandidateView[]>> = (value) => setRebalancePlanState("rebalanceCandidates", value);
  const setRebalancePlanBusy: Dispatch<SetStateAction<boolean>> = (value) => setRebalancePlanState("rebalancePlanBusy", value);
  const setRebalancePlanError: Dispatch<SetStateAction<string>> = (value) => setRebalancePlanState("rebalancePlanError", value);
  const [signalState, setSignalState] = useReducerGroup(initialSignalState);
  const { signalHash, signalReadiness, signalCandidate, signalBusy, signalError } = signalState;
  const setSignalHash: Dispatch<SetStateAction<string | null>> = (value) => setSignalState("signalHash", value);
  const setSignalReadiness: Dispatch<SetStateAction<SignalReadinessView | null>> = (value) => setSignalState("signalReadiness", value);
  const setSignalCandidate: Dispatch<SetStateAction<SignalCandidateView | null>> = (value) => setSignalState("signalCandidate", value);
  const setSignalBusy: Dispatch<SetStateAction<boolean>> = (value) => setSignalState("signalBusy", value);
  const setSignalError: Dispatch<SetStateAction<string>> = (value) => setSignalState("signalError", value);
  const [futuresState, setFuturesState] = useReducerGroup(initialFuturesState);
  const { futuresGrid, futuresPnl, futuresTrailing, futuresFunding, futuresBusy, futuresError } = futuresState;
  const setFuturesGrid: Dispatch<SetStateAction<FuturesGridView | null>> = (value) => setFuturesState("futuresGrid", value);
  const setFuturesPnl: Dispatch<SetStateAction<FuturesPnlView | null>> = (value) => setFuturesState("futuresPnl", value);
  const setFuturesTrailing: Dispatch<SetStateAction<FuturesTrailingView | null>> = (value) => setFuturesState("futuresTrailing", value);
  const setFuturesFunding: Dispatch<SetStateAction<FuturesFundingView | null>> = (value) => setFuturesState("futuresFunding", value);
  const setFuturesBusy: Dispatch<SetStateAction<boolean>> = (value) => setFuturesState("futuresBusy", value);
  const setFuturesError: Dispatch<SetStateAction<string>> = (value) => setFuturesState("futuresError", value);
  const [twoLegState, setTwoLegState] = useReducerGroup(initialTwoLegState);
  const { twoLegSession, twoLegProjection, twoLegBusy, twoLegError } = twoLegState;
  const setTwoLegSession: Dispatch<SetStateAction<string>> = (value) => setTwoLegState("twoLegSession", value);
  const setTwoLegProjection: Dispatch<SetStateAction<TwoLegProjectionView | null>> = (value) => setTwoLegState("twoLegProjection", value);
  const setTwoLegBusy: Dispatch<SetStateAction<boolean>> = (value) => setTwoLegState("twoLegBusy", value);
  const setTwoLegError: Dispatch<SetStateAction<string>> = (value) => setTwoLegState("twoLegError", value);
  const [botState, setBotState] = useReducerGroup(initialBotState);
  const { botIds, botProfile, botSessions, botCheck, botBusy, botError, selectedBotId, botDealCounts, botDcaPerf, botDcaActive, botDcaBusy, botDcaError } = botState;
  const setBotIds: Dispatch<SetStateAction<string[]>> = (value) => setBotState("botIds", value);
  const setBotProfile: Dispatch<SetStateAction<BotProfileView | null>> = (value) => setBotState("botProfile", value);
  const setBotSessions: Dispatch<SetStateAction<Record<string, string>>> = (value) => setBotState("botSessions", value);
  const setBotCheck: Dispatch<SetStateAction<BotCheckView | null>> = (value) => setBotState("botCheck", value);
  const setBotBusy: Dispatch<SetStateAction<boolean>> = (value) => setBotState("botBusy", value);
  const setBotError: Dispatch<SetStateAction<string>> = (value) => setBotState("botError", value);
  const setSelectedBotId: Dispatch<SetStateAction<string>> = (value) => setBotState("selectedBotId", value);
  const setBotDealCounts: Dispatch<SetStateAction<Record<string, number | null>>> = (value) => setBotState("botDealCounts", value);
  const setBotDcaPerf: Dispatch<SetStateAction<BotDcaPerformanceView | null>> = (value) => setBotState("botDcaPerf", value);
  const setBotDcaActive: Dispatch<SetStateAction<number | null>> = (value) => setBotState("botDcaActive", value);
  const setBotDcaBusy: Dispatch<SetStateAction<boolean>> = (value) => setBotState("botDcaBusy", value);
  const setBotDcaError: Dispatch<SetStateAction<string>> = (value) => setBotState("botDcaError", value);
  const [noticeUiState, setNoticeUiState] = useReducerGroup({ pendingBulk: null as DealBulkAction[] | null });
  const { pendingBulk } = noticeUiState;
  const [dealState, setDealState] = useReducerGroup(initialDealState);
  const { dealId, dealLifecycle, dealHistory, dealBulkResults, dealBusy, dealError, dealReplayVerified } = dealState;
  const setDealId: Dispatch<SetStateAction<string>> = (value) => setDealState("dealId", value);
  const setDealLifecycle: Dispatch<SetStateAction<DealLifecycleView | null>> = (value) => setDealState("dealLifecycle", value);
  const setDealHistory: Dispatch<SetStateAction<DealEventView[]>> = (value) => setDealState("dealHistory", value);
  const setDealBulkResults: Dispatch<SetStateAction<DealBulkResultRow[]>> = (value) => setDealState("dealBulkResults", value);
  const setDealBusy: Dispatch<SetStateAction<boolean>> = (value) => setDealState("dealBusy", value);
  const setDealError: Dispatch<SetStateAction<string>> = (value) => setDealState("dealError", value);
  const setDealReplayVerified: Dispatch<SetStateAction<boolean>> = (value) => setDealState("dealReplayVerified", value);
  const [exitState, setExitState] = useReducerGroup(initialExitState);
  const { exitBinding, exitPercent, exitBreakeven, exitBusy, exitError } = exitState;
  const setExitBinding: Dispatch<SetStateAction<TrailingBindView | null>> = (value) => setExitState("exitBinding", value);
  const setExitPercent: Dispatch<SetStateAction<PercentStateView | null>> = (value) => setExitState("exitPercent", value);
  const setExitBreakeven: Dispatch<SetStateAction<BreakevenView | null>> = (value) => setExitState("exitBreakeven", value);
  const setExitBusy: Dispatch<SetStateAction<boolean>> = (value) => setExitState("exitBusy", value);
  const [opsState, setOpsState] = useReducerGroup(initialOpsState);
  const { backupList, backupVerdict, backupBusy, backupError, dashboard, dashboardBusy, dashboardError, timelineFrame, timelineBusy, timelineError, recurring, recurringBusy, recurringError, centerEvents, centerBusy, centerError, riskExplain, riskBusy, riskError } = opsState;
  const setBackupList: Dispatch<SetStateAction<BackupManifestView[]>> = (value) => setOpsState("backupList", value);
  const setBackupVerdict: Dispatch<SetStateAction<BackupVerdictView | null>> = (value) => setOpsState("backupVerdict", value);
  const setBackupBusy: Dispatch<SetStateAction<boolean>> = (value) => setOpsState("backupBusy", value);
  const setDashboard: Dispatch<SetStateAction<DashboardView | null>> = (value) => setOpsState("dashboard", value);
  const setDashboardBusy: Dispatch<SetStateAction<boolean>> = (value) => setOpsState("dashboardBusy", value);
  const setTimelineFrame: Dispatch<SetStateAction<TimelineFrameView | null>> = (value) => setOpsState("timelineFrame", value);
  const setTimelineBusy: Dispatch<SetStateAction<boolean>> = (value) => setOpsState("timelineBusy", value);
  const setRecurring: Dispatch<SetStateAction<RecurringScheduleView | null>> = (value) => setOpsState("recurring", value);
  const setRecurringBusy: Dispatch<SetStateAction<boolean>> = (value) => setOpsState("recurringBusy", value);
  const setCenterEvents: Dispatch<SetStateAction<CenterEventView[]>> = (value) => setOpsState("centerEvents", value);
  const setCenterBusy: Dispatch<SetStateAction<boolean>> = (value) => setOpsState("centerBusy", value);
  const setRiskExplain: Dispatch<SetStateAction<RiskExplainView | null>> = (value) => setOpsState("riskExplain", value);
  const setRiskBusy: Dispatch<SetStateAction<boolean>> = (value) => setOpsState("riskBusy", value);
  const setRiskError: Dispatch<SetStateAction<string>> = (value) => setOpsState("riskError", value);
  const setCenterError: Dispatch<SetStateAction<string>> = (value) => setOpsState("centerError", value);
  const setRecurringError: Dispatch<SetStateAction<string>> = (value) => setOpsState("recurringError", value);
  const setTimelineError: Dispatch<SetStateAction<string>> = (value) => setOpsState("timelineError", value);
  const setDashboardError: Dispatch<SetStateAction<string>> = (value) => setOpsState("dashboardError", value);
  const setBackupError: Dispatch<SetStateAction<string>> = (value) => setOpsState("backupError", value);
  const setExitError: Dispatch<SetStateAction<string>> = (value) => setExitState("exitError", value);
  const revision = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const createPreviewRevision = useRef(0);
  const createPreviewController = useRef<AbortController | null>(null);
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
  const venueSymbolsController = useRef<AbortController | null>(null);
  const venueLastPriceController = useRef<AbortController | null>(null);
  const venueTicker24hController = useRef<AbortController | null>(null);
  const binanceAccountController = useRef<AbortController | null>(null);
  const rebalanceController = useRef<AbortController | null>(null);
  const paperController = useRef<AbortController | null>(null);
  const templateController = useRef<AbortController | null>(null);
  const rebalancePlanController = useRef<AbortController | null>(null);
  const signalController = useRef<AbortController | null>(null);
  const futuresController = useRef<AbortController | null>(null);
  const twoLegController = useRef<AbortController | null>(null);
  const botController = useRef<AbortController | null>(null);
  const botDcaController = useRef<AbortController | null>(null);
  const dealController = useRef<AbortController | null>(null);
  const dcaSessionsController = useRef<AbortController | null>(null);
  const dcaDetailController = useRef<AbortController | null>(null);
  const sweepController = useRef<AbortController | null>(null);
  const overfitController = useRef<AbortController | null>(null);
  const compareController = useRef<AbortController | null>(null);
  const portfolioController = useRef<AbortController | null>(null);
  const corrSeriesController = useRef<AbortController | null>(null);
  const corrGateController = useRef<AbortController | null>(null);
  const regimeSeriesController = useRef<AbortController | null>(null);
  const regimeGateController = useRef<AbortController | null>(null);
  const registryController = useRef<AbortController | null>(null);
  const systemController = useRef<AbortController | null>(null);
  const depthController = useRef<AbortController | null>(null);
  const paperConfigController = useRef<AbortController | null>(null);
  const fullPreviewController = useRef<AbortController | null>(null);
  const indicatorController = useRef<AbortController | null>(null);
  const exitController = useRef<AbortController | null>(null);
  const backupController = useRef<AbortController | null>(null);
  const dashboardController = useRef<AbortController | null>(null);
  const timelineController = useRef<AbortController | null>(null);
  const noticeStoreRef = useRef<NotificationStore | null>(null);
  if (noticeStoreRef.current === null) noticeStoreRef.current = new NotificationStore();
  const noticeStore = noticeStoreRef.current;
  const [, startPollTransition] = useTransition();
  const recurringController = useRef<AbortController | null>(null);
  const centerController = useRef<AbortController | null>(null);
  const riskController = useRef<AbortController | null>(null);
  const canaryController = useRef<AbortController | null>(null);
  const capabilitiesController = useRef<AbortController | null>(null);
  const liquidationController = useRef<AbortController | null>(null);
  const liquidationSymbolRef = useRef<string | null>(null);

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
          anchor: nextForm.anchor,
          safety_qty: nextForm.safety_qty,
          safety_count: Number(nextForm.safety_count),
          deviation: nextForm.deviation,
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
  /**
   * Faz 17 A.3: Bot Oluştur (DCA) canlı overlay hesabı — `calculate()` ile
   * aynı disiplin (ön-doğrulama + abort + revision), ayrı state. Anchor =
   * grafikteki son barın kapanışı: overlay her zaman görünen barlarla aynı
   * sembol/ölçekte kalır (venue/paper canlı fiyatı başka sembole ait olabilir).
   */
  async function calculateCreate(params: WizardPreviewParams) {
    const bars = historicalChartData?.bars ?? [];
    const anchor = bars.length > 0 ? bars[bars.length - 1].close : null;
    if (anchor === null || anchor.trim() === "") {
      createPreviewController.current?.abort();
      setCreatePreview(null);
      setCreatePreviewNote(t("create.overlay.nodata"));
      return;
    }
    const safetyQty = params.safetyQty.trim();
    const safetyCount = params.safetyCount.trim();
    const deviation = params.deviation.trim();
    if (
      !PREVIEW_DECIMAL.test(safetyQty) || !PREVIEW_COUNT.test(safetyCount) || !PREVIEW_DECIMAL.test(deviation)
      || Number(safetyCount) > 50 || Number(safetyQty) <= 0 || Number(deviation) <= 0 || Number(anchor) <= 0
    ) {
      createPreviewController.current?.abort();
      setCreatePreview(null);
      setCreatePreviewNote("");
      return;
    }
    const currentRevision = createPreviewRevision.current + 1;
    createPreviewRevision.current = currentRevision;
    createPreviewController.current?.abort();
    const requestController = new AbortController();
    createPreviewController.current = requestController;
    setCreatePreviewNote("");
    try {
      const response = await fetch("/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          anchor,
          safety_qty: safetyQty,
          safety_count: Number(safetyCount),
          deviation,
          revision: currentRevision,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as { data?: Preview } & ApiError;
      if (currentRevision !== createPreviewRevision.current) return;
      if (!response.ok || !body.data) {
        setCreatePreview(null);
        setCreatePreviewNote(t("create.overlay.error"));
        return;
      }
      setCreatePreview(body.data);
      setCreatePreviewNote("");
    } catch {
      if (requestController.signal.aborted || currentRevision !== createPreviewRevision.current) return;
      setCreatePreview(null);
      setCreatePreviewNote(t("create.overlay.error"));
    }
  }


  useEffect(() => {
    void calculate(initialForm);
    void loadDatasets();
    void loadHistoricalProfiles();
    void loadBinancePublicSnapshot(DEFAULT_VENUE_SYMBOL);
    void loadVenueSymbols();
    void loadVenueLastPrice(DEFAULT_VENUE_SYMBOL);
    void loadVenueTicker24h(DEFAULT_VENUE_SYMBOL);
    void loadDcaSessions();
    void loadPaperConfig();
    void loadBinanceAccount();
    void loadTemplates();
    void fetchIndicatorRegistry();
    void fetchSystemStatus();
    void loadDepth(DEFAULT_VENUE_SYMBOL, 20);
    void fetchCapabilities();
    void fetchCanary();
    return () => {
      controller.current?.abort();
      createPreviewController.current?.abort();
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
      venueSymbolsController.current?.abort();
      venueLastPriceController.current?.abort();
      venueTicker24hController.current?.abort();
      dcaSessionsController.current?.abort();
      dcaDetailController.current?.abort();
      botDcaController.current?.abort();
      compareController.current?.abort();
      corrGateController.current?.abort();
      corrSeriesController.current?.abort();
      portfolioController.current?.abort();
      sweepController.current?.abort();
      overfitController.current?.abort();
      indicatorController.current?.abort();
      paperConfigController.current?.abort();
      fullPreviewController.current?.abort();
      binanceAccountController.current?.abort();
      rebalanceController.current?.abort();
      paperController.current?.abort();
      templateController.current?.abort();
      rebalancePlanController.current?.abort();
      signalController.current?.abort();
      futuresController.current?.abort();
      regimeSeriesController.current?.abort();
      regimeGateController.current?.abort();
      registryController.current?.abort();
      systemController.current?.abort();
      depthController.current?.abort();
      capabilitiesController.current?.abort();
    };
  }, []);

  useEffect(() => {
    const bars = historicalChartData?.bars ?? [];
    if (bars.length >= 2) {
      void loadIndicator(indicatorKind, bars.map((bar) => bar.close).slice(-5000));
    } else {
      setIndicatorSeries(null);
      setIndicatorStatus("idle");
    }
  }, [historicalChartData, indicatorKind]);

  useEffect(() => {
    if (paperConfig === null) return;
    void calculateFull(paperConfig, form);
  }, [paperConfig, form]);

  useEffect(() => {
    applyTheme(document.documentElement, theme);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      /* private mode: theme still applies for this session */
    }
  }, [theme]);

  async function loadBinancePublicSnapshot(symbol: string) {
    binancePublicSnapshotController.current?.abort();
    const requestController = new AbortController();
    binancePublicSnapshotController.current = requestController;
    setBinancePublicSnapshotStatus("loading");
    setBinancePublicSnapshotError("");
    try {
      const response = await fetch(`/api/venue-snapshots/binance-spot-testnet?symbol=${encodeURIComponent(symbol)}`, { cache: "no-store", signal: requestController.signal });
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

  async function loadVenueSymbols() {
    venueSymbolsController.current?.abort();
    const requestController = new AbortController();
    venueSymbolsController.current = requestController;
    setVenueSymbolsStatus("loading");
    setVenueSymbolsError("");
    try {
      const response = await fetch("/api/public/exchange-symbols", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isVenueSymbolList(body)) {
        const errorBody = body as { detail?: string; title?: string };
        setVenueSymbols([]);
        setVenueSymbolsCount(0);
        setVenueSymbolsError(errorBody.detail ?? errorBody.title ?? "Public sembol listesi sözleşmesi doğrulanamadı.");
        setVenueSymbolsStatus("error");
        return;
      }
      setVenueSymbols(body.symbols);
      setVenueSymbolsCount(body.count);
      setVenueSymbolsStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setVenueSymbols([]);
      setVenueSymbolsCount(0);
      setVenueSymbolsError("Public sembol listesi API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setVenueSymbolsStatus("error");
    }
  }

  async function loadVenueLastPrice(symbol: string) {
    venueLastPriceController.current?.abort();
    const requestController = new AbortController();
    venueLastPriceController.current = requestController;
    setVenueLastPriceStatus("loading");
    try {
      const response = await fetch(`/api/public/last-price?symbol=${encodeURIComponent(symbol)}`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isVenueLastPrice(body) || body.symbol !== symbol) {
        setVenueLastPrice(null);
        setVenueLastPriceStatus("error");
        return;
      }
      setVenueLastPrice({ symbol: body.symbol, price: body.price });
      setVenueLastPriceStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setVenueLastPrice(null);
      setVenueLastPriceStatus("error");
    }
  }

  async function loadVenueTicker24h(symbol: string) {
    venueTicker24hController.current?.abort();
    const requestController = new AbortController();
    venueTicker24hController.current = requestController;
    setVenueTicker24hStatus("loading");
    setVenueTicker24hError("");
    try {
      const response = await fetch(`/api/public/ticker-24h?symbol=${encodeURIComponent(symbol)}`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isVenueTicker24h(body) || body.symbol !== symbol) {
        setVenueTicker24h(null);
        setVenueTicker24hStatus("error");
        setVenueTicker24hError("Piyasa özeti doğrulanamadı.");
        return;
      }
      setVenueTicker24h(body);
      setVenueTicker24hStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setVenueTicker24h(null);
      setVenueTicker24hStatus("error");
      setVenueTicker24hError("Piyasa özeti alınamadı.");
    }
  }

  function selectVenueSymbol(symbol: string) {
    setSelectedVenueSymbol(symbol);
    void loadVenueLastPrice(symbol);
    void loadVenueTicker24h(symbol);
    void loadBinancePublicSnapshot(symbol);
  }

  async function loadBinanceAccount() {
    binanceAccountController.current?.abort();
    const requestController = new AbortController();
    binanceAccountController.current = requestController;
    setBinanceAccountStatus("loading");
    setBinanceAccountError("");
    try {
      const accountResponse = await fetch("/api/testnet/account", { cache: "no-store", signal: requestController.signal });
      const accountBody = (await accountResponse.json()) as unknown;
      const ordersResponse = await fetch("/api/testnet/open-orders", { cache: "no-store", signal: requestController.signal });
      const ordersBody = (await ordersResponse.json()) as unknown;
      if ((accountResponse.status === 409 && isTestnetCredentialNotConfigured(accountBody))
        || (ordersResponse.status === 409 && isTestnetCredentialNotConfigured(ordersBody))) {
        setBinanceAccount(null);
        setBinanceOpenOrders(null);
        setBinanceAccountStatus("not_configured");
        return;
      }
      const accountValid = accountResponse.ok && isBinanceAccountSnapshot(accountBody);
      const ordersValid = ordersResponse.ok && isBinanceOpenOrdersSnapshot(ordersBody);
      if (!accountValid || !ordersValid) {
        const failingBody = (!accountValid ? accountBody : ordersBody) as { detail?: string; title?: string };
        setBinanceAccount(null);
        setBinanceOpenOrders(null);
        setBinanceAccountError(failingBody.detail ?? failingBody.title ?? "Testnet hesap snapshot sözleşmesi doğrulanamadı.");
        setBinanceAccountStatus("error");
        return;
      }
      setBinanceAccount(accountBody);
      setBinanceOpenOrders(ordersBody);
      setBinanceAccountStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setBinanceAccount(null);
      setBinanceOpenOrders(null);
      setBinanceAccountError("Testnet hesap API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setBinanceAccountStatus("error");
    }
  }

  async function calculateRebalance() {
    const holdings = parsePairLines(rebalanceHoldingsText);
    const prices = parsePairLines(rebalancePricesText);
    if (holdings.error) {
      setRebalanceValuation(null);
      setRebalanceError(`Varlıklar: ${holdings.error}`);
      setRebalanceStatus("error");
      return;
    }
    if (prices.error) {
      setRebalanceValuation(null);
      setRebalanceError(`Fiyatlar: ${prices.error}`);
      setRebalanceStatus("error");
      return;
    }
    rebalanceController.current?.abort();
    const requestController = new AbortController();
    rebalanceController.current = requestController;
    setRebalanceStatus("pending");
    setRebalanceError("");
    try {
      const response = await fetch("/api/rebalance/valuation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ valuation_asset: "USDT", holdings: holdings.rows, prices: prices.rows }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok || !isRebalanceValuation(body.data)) {
        setRebalanceValuation(null);
        setRebalanceError(body.error?.message ?? "Değerleme hesaplanamadı.");
        setRebalanceStatus("error");
        return;
      }
      setRebalanceValuation(body.data);
      setRebalanceStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setRebalanceValuation(null);
      setRebalanceError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      setRebalanceStatus("error");
    }
  }

  async function paperRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    paperController.current?.abort();
    const requestController = new AbortController();
    paperController.current = requestController;
    setPaperBusy(true);
    setPaperError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setPaperError(parsed.error?.message ?? "Paper trading isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setPaperError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setPaperBusy(false);
    }
  }

  async function activatePaper() {
    const parsed = await paperRequest("/api/paper/sessions", {
      confirmed: true, symbols: ["BTCUSDT"], max_staleness_us: 5000000, starting_cash: "10000",
    });
    if (parsed && isPaperSnapshot(parsed.data)) setPaperSnapshot(parsed.data);
    else if (parsed) setPaperError("Paper session yanıtı doğrulanamadı.");
  }

  async function refreshPaperMarket() {
    if (!paperSnapshot) return;
    const parsed = await paperRequest(`/api/paper/sessions/${encodeURIComponent(paperSnapshot.session_id)}/market-refresh`, {});
    if (parsed && isRecordWithSnapshot(parsed.data) && isPaperPrints(parsed.data.prints)) {
      setPaperPrints(parsed.data.prints);
      setPaperSnapshot(parsed.data.snapshot);
    } else if (parsed) setPaperError("Piyasa yanıtı doğrulanamadı.");
  }

  async function placePaperOrder() {
    if (!paperSnapshot) return;
    const parsed = await paperRequest(`/api/paper/sessions/${encodeURIComponent(paperSnapshot.session_id)}/orders`, {
      symbol: paperOrderDraft.symbol, side: paperOrderDraft.side, order_type: "MARKET",
      qty: paperOrderDraft.qty, limit_price: null, client_order_id: paperOrderDraft.clientOrderId,
    });
    if (parsed && isRecordWithSnapshot(parsed.data)) setPaperSnapshot(parsed.data.snapshot);
    else if (parsed) setPaperError("Emir yanıtı doğrulanamadı.");
  }

  async function fillPaperOrder(clientOrderId: string, eventId: string) {
    if (!paperSnapshot) return;
    const parsed = await paperRequest(`/api/paper/sessions/${encodeURIComponent(paperSnapshot.session_id)}/fills`, {
      client_order_id: clientOrderId, event_id: eventId,
    });
    if (parsed && isRecordWithSnapshot(parsed.data)) setPaperSnapshot(parsed.data.snapshot);
    else if (parsed) setPaperError("Dolum yanıtı doğrulanamadı.");
  }

  async function templateRequest(path: string, method: string, body?: unknown): Promise<{ data?: unknown } & ApiError | null> {
    templateController.current?.abort();
    const requestController = new AbortController();
    templateController.current = requestController;
    setTemplateBusy(true);
    setTemplateError("");
    try {
      const response = await fetch(path, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setTemplateError(parsed.error?.message ?? "Şablon isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setTemplateError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setTemplateBusy(false);
    }
  }

  async function loadTemplates() {
    const parsed = await templateRequest("/api/templates", "GET");
    if (parsed && isTemplateMetaList(parsed.data)) setTemplateMetas(parsed.data);
    else if (parsed) setTemplateError("Şablon listesi doğrulanamadı.");
  }

  async function selectTemplate(templateId: string) {
    const parsed = await templateRequest(`/api/templates/${encodeURIComponent(templateId)}`, "GET");
    if (parsed && isTemplateDetail(parsed.data)) {
      setTemplateDetail(parsed.data);
      setTemplateBindResult(null);
      setTemplateDiffRows([]);
    } else if (parsed) setTemplateError("Şablon detayı doğrulanamadı.");
  }

  async function importTemplate(payload: TemplateImportPayload) {
    const parsed = await templateRequest("/api/templates/import", "POST", payload);
    if (parsed) {
      await loadTemplates();
      if (payload.template_id) await selectTemplate(payload.template_id);
    }
  }

  async function bindTemplate(templateId: string, payload: TemplateBindPayload) {
    const parsed = await templateRequest(`/api/templates/${encodeURIComponent(templateId)}/bind`, "POST", payload);
    if (parsed && isTemplateBindResponse(parsed.data)) {
      setTemplateBindResult({ ...parsed.data.binding, config_hash: parsed.data.materialized.config_hash });
    } else if (parsed) setTemplateError("Bağlama yanıtı doğrulanamadı.");
  }

  async function diffTemplates(firstId: string, secondId: string) {
    const parsed = await templateRequest("/api/templates/diff", "POST", { first_id: firstId, second_id: secondId });
    if (parsed && isTemplateDiffRows(parsed.data)) setTemplateDiffRows(parsed.data);
    else if (parsed) setTemplateError("Fark yanıtı doğrulanamadı.");
  }

  async function rebalancePlanRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    rebalancePlanController.current?.abort();
    const requestController = new AbortController();
    rebalancePlanController.current = requestController;
    setRebalancePlanBusy(true);
    setRebalancePlanError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setRebalancePlanError(parsed.error?.message ?? "Rebalancing isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setRebalancePlanError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setRebalancePlanBusy(false);
    }
  }

  async function submitRebalancePlan(payload: RebalancePlanPayload) {
    const parsed = await rebalancePlanRequest("/api/rebalance/plan", payload);
    if (parsed && isRebalancePlanView(parsed.data)) {
      setRebalancePlan(parsed.data);
      setRebalanceDisclosure(null);
      setRebalanceCandidates([]);
    } else if (parsed) setRebalancePlanError("Plan yanıtı doğrulanamadı.");
  }

  async function submitRebalanceDisclose(payload: RebalanceDisclosePayload) {
    const parsed = await rebalancePlanRequest("/api/rebalance/disclose", payload);
    if (parsed && isRebalanceDisclosureView(parsed.data)) {
      setRebalanceDisclosure(parsed.data.disclosure);
      setRebalanceCandidates(parsed.data.candidates);
    } else if (parsed) setRebalancePlanError("Disclosure yanıtı doğrulanamadı.");
  }

  async function signalRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    signalController.current?.abort();
    const requestController = new AbortController();
    signalController.current = requestController;
    setSignalBusy(true);
    setSignalError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setSignalError(parsed.error?.message ?? "Sinyal isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setSignalError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setSignalBusy(false);
    }
  }

  async function hashSignalPayload(payload: Record<string, unknown>) {
    const parsed = await signalRequest("/api/signals/hash", { payload });
    if (parsed && typeof parsed.data === "object" && parsed.data !== null && typeof (parsed.data as Record<string, unknown>).payload_hash === "string") {
      setSignalHash((parsed.data as Record<string, unknown>).payload_hash as string);
      setSignalReadiness(null);
      setSignalCandidate(null);
    } else if (parsed) setSignalError("Hash yanıtı doğrulanamadı.");
  }

  async function assessSignal(payload: SignalAssessPayload) {
    const parsed = await signalRequest("/api/signals/assess", payload);
    if (parsed && isSignalReadinessView(parsed.data)) setSignalReadiness(parsed.data);
    else if (parsed) setSignalError("Readiness yanıtı doğrulanamadı.");
  }

  async function bindSignal(payload: SignalBindPayload) {
    const parsed = await signalRequest("/api/signals/candidates", payload);
    if (parsed && isSignalCandidateView(parsed.data)) setSignalCandidate(parsed.data);
    else if (parsed) setSignalError("Aday yanıtı doğrulanamadı.");
  }

  async function futuresRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    futuresController.current?.abort();
    const requestController = new AbortController();
    futuresController.current = requestController;
    setFuturesBusy(true);
    setFuturesError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setFuturesError(parsed.error?.message ?? "Futures isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setFuturesError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setFuturesBusy(false);
    }
  }

  async function submitFuturesGrid(payload: FuturesGridPayload) {
    const parsed = await futuresRequest("/api/futures/grid/levels", payload);
    if (parsed && isFuturesGridView(parsed.data)) setFuturesGrid(parsed.data);
    else if (parsed) setFuturesError("Grid yanıtı doğrulanamadı.");
  }

  async function submitFuturesPnl(payload: FuturesPnlPayload) {
    const parsed = await futuresRequest("/api/futures/position/pnl", payload);
    if (parsed && isFuturesPnlView(parsed.data)) setFuturesPnl(parsed.data);
    else if (parsed) setFuturesError("PnL yanıtı doğrulanamadı.");
  }

  async function submitTrailingArm(payload: FuturesTrailingArmPayload) {
    const parsed = await futuresRequest("/api/futures/trailing/arm", payload);
    if (parsed && isFuturesTrailingView(parsed.data)) setFuturesTrailing(parsed.data);
    else if (parsed) setFuturesError("Trailing yanıtı doğrulanamadı.");
  }

  async function submitTrailingObserve(payload: FuturesTrailingObservePayload) {
    const parsed = await futuresRequest("/api/futures/trailing/observe", payload);
    if (parsed && isFuturesTrailingView(parsed.data)) setFuturesTrailing(parsed.data);
    else if (parsed) setFuturesError("Trailing yanıtı doğrulanamadı.");
  }

  async function submitFuturesFunding(payload: FuturesFundingPayload) {
    const parsed = await futuresRequest("/api/futures/funding", payload);
    if (parsed && isFuturesFundingView(parsed.data)) setFuturesFunding(parsed.data);
    else if (parsed) setFuturesError("Funding yanıtı doğrulanamadı.");
  }

  async function twoLegRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    twoLegController.current?.abort();
    const requestController = new AbortController();
    twoLegController.current = requestController;
    setTwoLegBusy(true);
    setTwoLegError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setTwoLegError(parsed.error?.message ?? "Two-leg isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setTwoLegError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setTwoLegBusy(false);
    }
  }

  function applyTwoLegProjection(parsed: { data?: unknown } & ApiError) {
    const body = parsed.data as { projection?: unknown } | undefined;
    if (body && isTwoLegProjectionView(body.projection)) setTwoLegProjection(body.projection);
    else setTwoLegError("Two-leg yanıtı doğrulanamadı.");
  }

  async function startTwoLegSession(sessionId: string) {
    setTwoLegSession(sessionId);
    const parsed = await twoLegRequest("/api/two-leg/sessions", { session_id: sessionId });
    if (parsed) applyTwoLegProjection(parsed);
  }

  async function acceptTwoLegFill(payload: TwoLegFillPayload) {
    const parsed = await twoLegRequest(`/api/two-leg/sessions/${encodeURIComponent(twoLegSession)}/fills`, payload);
    if (parsed) applyTwoLegProjection(parsed);
  }

  async function markTwoLegRecovery() {
    const parsed = await twoLegRequest(`/api/two-leg/sessions/${encodeURIComponent(twoLegSession)}/recovery`, {});
    if (parsed) applyTwoLegProjection(parsed);
  }

  async function markTwoLegTimeout() {
    const parsed = await twoLegRequest(`/api/two-leg/sessions/${encodeURIComponent(twoLegSession)}/timeout`, {});
    if (parsed) applyTwoLegProjection(parsed);
  }

  async function replayTwoLegSession() {
    const parsed = await twoLegRequest(`/api/two-leg/sessions/${encodeURIComponent(twoLegSession)}/replay`, {});
    if (parsed) applyTwoLegProjection(parsed);
  }

  async function botRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    botController.current?.abort();
    const requestController = new AbortController();
    botController.current = requestController;
    setBotBusy(true);
    setBotError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setBotError(parsed.error?.message ?? "Bot isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setBotError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setBotBusy(false);
    }
  }

  async function botGet(path: string): Promise<{ data?: unknown } & ApiError | null> {
    botController.current?.abort();
    const requestController = new AbortController();
    botController.current = requestController;
    setBotBusy(true);
    setBotError("");
    try {
      const response = await fetch(path, { cache: "no-store", signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setBotError(parsed.error?.message ?? "Bot isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setBotError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setBotBusy(false);
    }
  }

  function applyBotDetail(parsed: { data?: unknown } & ApiError) {
    const body = parsed.data as { profile?: unknown; sessions?: unknown } | undefined;
    if (
      body &&
      isBotProfileView(body.profile) &&
      typeof body.sessions === "object" &&
      body.sessions !== null
    ) {
      setBotProfile(body.profile);
      setBotSessions(body.sessions as Record<string, string>);
    } else setBotError("Bot yanıtı doğrulanamadı.");
  }

  async function registerBot(payload: BotRegisterPayload) {
    setSelectedBotId(payload.bot_id);
    const parsed = await botRequest("/api/bots", payload);
    if (parsed) {
      const body = parsed.data as { profile?: unknown } | undefined;
      if (body && isBotProfileView(body.profile)) {
        setBotProfile(body.profile);
        setBotSessions({});
        setBotIds((ids) => (ids.includes(payload.bot_id) ? ids : [...ids, payload.bot_id]));
        void refreshBotDealCounts([payload.bot_id]);
        noticeStore.push(`${payload.bot_id} kaydedildi.`, "success");
      } else setBotError("Bot yanıtı doğrulanamadı.");
    }
  }

  async function refreshBots() {
    const parsed = await botGet("/api/bots");
    if (parsed) {
      const body = parsed.data as { bot_ids?: unknown } | undefined;
      if (body && Array.isArray(body.bot_ids) && body.bot_ids.every((id) => typeof id === "string")) {
        setBotIds(body.bot_ids as string[]);
        void refreshBotDealCounts(body.bot_ids as string[]);
      } else setBotError("Bot yanıtı doğrulanamadı.");
    }
  }

  async function selectBot(botId: string) {
    setSelectedBotId(botId);
    const parsed = await botGet(`/api/bots/${encodeURIComponent(botId)}`);
    if (parsed) applyBotDetail(parsed);
  }
  /**
   * Faz 17 A.4: tam sayfa detay gezinmesi (popup yok). Bot detayında overlay
   * için istemci taslağı okunur; taslak yoksa overlay boş kalır (uydurma yok).
   */
  /* Faz 17 AA.3a: bot DCA toplamları — profil akışından BAĞIMSIZ controller
   * (botGet paylaşılsaydı profil-yüklemeyi iptal eder / botBusy'yi ezerdi).
   * Kart-rozeti (deal-count) + detay-kutusu (performance + deal-count). */
  async function loadBotDcaStats(botId: string) {
    botDcaController.current?.abort();
    const requestController = new AbortController();
    botDcaController.current = requestController;
    setBotDcaBusy(true);
    setBotDcaError("");
    setBotDcaPerf(null);
    setBotDcaActive(null);
    try {
      const perfResponse = await fetch(`/api/bots/${encodeURIComponent(botId)}/dca-sessions/performance`, { cache: "no-store", signal: requestController.signal });
      const perfBody = (await perfResponse.json()) as unknown;
      if (!perfResponse.ok || !isBotDcaPerformanceResponse(perfBody)) {
        setBotDcaError("Bot DCA istatistiği alınamadı.");
        return;
      }
      setBotDcaPerf(perfBody.data);
      const countResponse = await fetch(`/api/bots/${encodeURIComponent(botId)}/dca-sessions/deal-count`, { cache: "no-store", signal: requestController.signal });
      const countBody = (await countResponse.json()) as unknown;
      if (!countResponse.ok || !isBotDcaDealCountResponse(countBody)) {
        setBotDcaError("Bot aktif-deal sayısı alınamadı (performans okundu).");
        return;
      }
      setBotDcaActive(countBody.data.active);
      setBotDealCounts((current) => ({ ...current, [botId]: countBody.data.active }));
    } catch (error) {
      if (requestController.signal.aborted) return;
      setBotDcaError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setBotDcaBusy(false);
    }
  }

  async function refreshBotDealCounts(ids: string[]) {
    const entries: Record<string, number | null> = {};
    for (const id of ids) {
      try {
        const response = await fetch(`/api/bots/${encodeURIComponent(id)}/dca-sessions/deal-count`, { cache: "no-store" });
        const body = (await response.json()) as unknown;
        entries[id] = response.ok && isBotDcaDealCountResponse(body) ? body.data.active : null;
      } catch {
        entries[id] = null;
      }
    }
    setBotDealCounts(entries);
  }

  function openBotDetail(botId: string) {
    setCreateView(null);
    setDetailView({ kind: "bot", botId });
    setActiveSection("bots");
    window.location.hash = buildDetailHash("bot", botId);
    void selectBot(botId);
    void loadBotDcaStats(botId);
    const params = readDraftPreviewParams(botId);
    if (params) void calculateCreate(params);
    else {
      createPreviewController.current?.abort();
      setCreatePreview(null);
      setCreatePreviewNote(t("create.overlay.nodraft"));
    }
  }

  function openDealDetail(overrideId?: string) {
    const targetId = overrideId ?? dealId;
    if (overrideId !== undefined) setDealId(overrideId);
    setCreateView(null);
    setDetailView({ kind: "deal", dealId: targetId });
    setActiveSection("deals");
    window.location.hash = buildDetailHash("deal", targetId);
    void refreshDeal(targetId);
  }

  function closeDetail() {
    window.location.hash = buildSectionHash(activeSection);
    setDetailView(null);
    setCreatePreview(null);
    setCreatePreviewNote("");
  }


  async function updateBotLists(payload: BotListsPayload) {
    const parsed = await botRequest(`/api/bots/${encodeURIComponent(selectedBotId)}/lists`, payload);
    if (parsed) {
      const body = parsed.data as { profile?: unknown } | undefined;
      if (body && isBotProfileView(body.profile)) setBotProfile(body.profile);
      else setBotError("Bot yanıtı doğrulanamadı.");
    }
  }

  async function bindBotSession(payload: BotBindPayload) {
    const parsed = await botRequest(`/api/bots/${encodeURIComponent(selectedBotId)}/sessions`, payload);
    if (parsed) await selectBot(selectedBotId);
  }

  async function checkBotPair(symbol: string) {
    const parsed = await botRequest(`/api/bots/${encodeURIComponent(selectedBotId)}/check`, { symbol });
    if (parsed) {
      const body = parsed.data as unknown;
      if (isBotCheckView(body)) setBotCheck(body);
      else setBotError("Bot yanıtı doğrulanamadı.");
    }
  }

  async function dealRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    dealController.current?.abort();
    const requestController = new AbortController();
    dealController.current = requestController;
    setDealBusy(true);
    setDealError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setDealError(parsed.error?.message ?? "Deal isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setDealError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setDealBusy(false);
    }
  }

  async function refreshDeal(id: string) {
    const parsed = await dealRequest(`/api/deals/${encodeURIComponent(id)}/replay`, {});
    if (parsed) {
      if (isDealReplayView(parsed.data)) {
        setDealLifecycle(parsed.data.lifecycle);
        setDealHistory(parsed.data.history);
        setDealReplayVerified(true);
      } else {
        setDealReplayVerified(false);
        setDealError("Deal yanıtı doğrulanamadı.");
      }
    }
  }

  async function createDeal(payload: DealCreatePayload) {
    setDealId(payload.deal_id);
    const parsed = await dealRequest("/api/deals", payload);
    if (parsed) {
      noticeStore.push(`${payload.deal_id} oluşturuldu.`, "success");
      await refreshDeal(payload.deal_id);
    }
  }

  async function appendDealEvent(payload: DealAppendPayload) {
    const parsed = await dealRequest(`/api/deals/${encodeURIComponent(dealId)}/events`, payload);
    if (parsed) await refreshDeal(dealId);
  }

  async function bulkDealEvents(actions: DealBulkAction[]) {
    const parsed = await dealRequest("/api/deals/bulk", { actions });
    if (parsed) {
      const body = parsed.data as { results?: unknown } | undefined;
      if (body && Array.isArray(body.results)) {
        const bulkRows = body.results as { deal_id: string; event_id: string; result?: string; error?: string }[];
        setDealBulkResults(bulkRows);
        const bulkOk = bulkRows.filter((row) => !row.error).length;
        noticeStore.push(`Toplu gönderim: ${bulkOk}/${bulkRows.length} başarılı.`, bulkOk === bulkRows.length ? "success" : "error");
        await refreshDeal(dealId);
      } else setDealError("Deal yanıtı doğrulanamadı.");
    }
  }

  async function exitRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    exitController.current?.abort();
    const requestController = new AbortController();
    exitController.current = requestController;
    setExitBusy(true);
    setExitError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setExitError(parsed.error?.message ?? "Çıkış isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setExitError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setExitBusy(false);
    }
  }

  async function bindExitCandidate(payload: TrailingBindPayload) {
    const parsed = await exitRequest("/api/exits/trailing", payload);
    if (parsed) {
      if (isTrailingBindView(parsed.data)) setExitBinding(parsed.data);
      else setExitError("Çıkış yanıtı doğrulanamadı.");
    }
  }

  async function armExitPercent(payload: { side: string; activation_price: string; rate: string }) {
    const parsed = await exitRequest("/api/exits/trailing/percent-arm", payload);
    if (parsed) {
      if (isPercentStateView(parsed.data)) setExitPercent(parsed.data);
      else setExitError("Çıkış yanıtı doğrulanamadı.");
    }
  }

  async function observeExitPercent(payload: { side: string; state: Record<string, unknown>; price: string }) {
    const parsed = await exitRequest("/api/exits/trailing/percent-observe", payload);
    if (parsed) {
      if (isPercentStateView(parsed.data)) setExitPercent(parsed.data);
      else setExitError("Çıkış yanıtı doğrulanamadı.");
    }
  }

  async function backupRequest(path: string, body: unknown): Promise<{ data?: unknown } & ApiError | null> {
    backupController.current?.abort();
    const requestController = new AbortController();
    backupController.current = requestController;
    setBackupBusy(true);
    setBackupError("");
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setBackupError(parsed.error?.message ?? "Backup isteği başarısız.");
        return null;
      }
      return parsed;
    } catch (error) {
      if (requestController.signal.aborted) return null;
      setBackupError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
      return null;
    } finally {
      setBackupBusy(false);
    }
  }

  async function takeBackup(store: string) {
    const parsed = await backupRequest("/api/admin/backup", { store });
    if (parsed) {
      noticeStore.push("Backup alındı.", "success");
      await refreshBackups();
    }
  }

  async function verifyBackupFile(backupFile: string) {
    const parsed = await backupRequest("/api/admin/backup/verify", { backup_file: backupFile });
    if (parsed) {
      if (isBackupVerdictView(parsed.data)) setBackupVerdict(parsed.data);
      else setBackupError("Backup yanıtı doğrulanamadı.");
    }
  }

  async function refreshBackups() {
    backupController.current?.abort();
    const requestController = new AbortController();
    backupController.current = requestController;
    setBackupBusy(true);
    setBackupError("");
    try {
      const response = await fetch("/api/admin/backups", { cache: "no-store", signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setBackupError(parsed.error?.message ?? "Backup isteği başarısız.");
        return;
      }
      const body = parsed.data as { backups?: unknown } | undefined;
      if (body && isBackupManifestList(body.backups)) setBackupList(body.backups);
      else setBackupError("Backup yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setBackupError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setBackupBusy(false);
    }
  }

  async function refreshDashboard() {
    dashboardController.current?.abort();
    const requestController = new AbortController();
    dashboardController.current = requestController;
    setDashboardBusy(true);
    setDashboardError("");
    try {
      const response = await fetch("/api/dashboard", { cache: "no-store", signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setDashboardError(parsed.error?.message ?? "Özet isteği başarısız.");
        return;
      }
      if (isDashboardView(parsed.data)) setDashboard(parsed.data);
      else setDashboardError("Özet yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDashboardError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDashboardBusy(false);
    }
  }

  async function seekTimeline(step: number) {
    timelineController.current?.abort();
    const requestController = new AbortController();
    timelineController.current = requestController;
    setTimelineBusy(true);
    setTimelineError("");
    try {
      const response = await fetch(`/api/deals/${encodeURIComponent(dealId)}/timeline?step=${step}`, { cache: "no-store", signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setTimelineError(parsed.error?.message ?? "Zaman çizgisi isteği başarısız.");
        return;
      }
      if (isTimelineFrameView(parsed.data)) setTimelineFrame(parsed.data);
      else setTimelineError("Zaman çizgisi yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setTimelineError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setTimelineBusy(false);
    }
  }

  async function projectRecurring(payload: RecurringSchedulePayload) {
    recurringController.current?.abort();
    const requestController = new AbortController();
    recurringController.current = requestController;
    setRecurringBusy(true);
    setRecurringError("");
    try {
      const response = await fetch("/api/recurring/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setRecurringError(parsed.error?.message ?? "Takvim isteği başarısız.");
        return;
      }
      if (isRecurringScheduleView(parsed.data)) setRecurring(parsed.data);
      else setRecurringError("Takvim yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setRecurringError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setRecurringBusy(false);
    }
  }

  async function refreshCenterEvents() {
    centerController.current?.abort();
    const requestController = new AbortController();
    centerController.current = requestController;
    setCenterBusy(true);
    setCenterError("");
    try {
      const response = await fetch("/api/events?limit=50", { cache: "no-store", signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setCenterError(parsed.error?.message ?? "Olay isteği başarısız.");
        return;
      }
      const body = parsed.data as { events?: unknown } | undefined;
      if (body && isCenterEventList(body.events)) setCenterEvents(body.events);
      else setCenterError("Olay yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCenterError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCenterBusy(false);
    }
  }

  async function explainRisk(payload: RiskExplainPayload) {
    riskController.current?.abort();
    const requestController = new AbortController();
    riskController.current = requestController;
    setRiskBusy(true);
    setRiskError("");
    try {
      const response = await fetch("/api/risk/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setRiskError(parsed.error?.message ?? "Açıklama isteği başarısız.");
        return;
      }
      if (isRiskExplainView(parsed.data)) setRiskExplain(parsed.data);
      else setRiskError("Açıklama yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setRiskError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setRiskBusy(false);
    }
  }

  async function loadIndicator(kind: IndicatorKind, closes: string[]) {
    indicatorController.current?.abort();
    const requestController = new AbortController();
    indicatorController.current = requestController;
    setIndicatorStatus("loading");
    setIndicatorError("");
    try {
      const response = await fetch(`/api/indicators/${INDICATOR_ROUTES[kind]}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(indicatorRequestBody(kind, closes)),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (!response.ok) {
        setIndicatorSeries(null);
        setIndicatorStatus("error");
        setIndicatorError("Gösterge hesaplanamadı.");
        return;
      }
      if ((kind === "sma" || kind === "ema") && isIndicatorResponse(body)) {
        setIndicatorSeries({ kind, points: body.data.points });
      } else if (kind === "macd" && isMacdResponse(body)) {
        setIndicatorSeries({ kind, points: body.data.points });
      } else if (kind === "stoch_rsi" && isStochRsiResponse(body)) {
        setIndicatorSeries({ kind, points: body.data.points });
      } else if (kind === "bollinger" && isBollingerResponse(body)) {
        setIndicatorSeries({ kind, points: body.data.points });
      } else {
        setIndicatorSeries(null);
        setIndicatorStatus("error");
        setIndicatorError("Gösterge hesaplanamadı.");
        return;
      }
      setIndicatorStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setIndicatorSeries(null);
      setIndicatorStatus("error");
      setIndicatorError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    }
  }

  async function loadPaperConfig() {
    paperConfigController.current?.abort();
    const requestController = new AbortController();
    paperConfigController.current = requestController;
    try {
      const response = await fetch("/api/config/paper", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || typeof body !== "object" || body === null || Array.isArray(body)
        || !("data" in body) || typeof (body as { data: unknown }).data !== "object"
        || (body as { data: unknown }).data === null || Array.isArray((body as { data: unknown }).data)) {
        setFullPreviewStatus("error");
        setFullPreviewError("Taban config alınamadı.");
        return;
      }
      setPaperConfig((body as { data: Record<string, unknown> }).data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setFullPreviewStatus("error");
      setFullPreviewError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    }
  }

  async function calculateFull(base: Record<string, unknown>, nextForm: FormState) {
    fullPreviewController.current?.abort();
    const requestController = new AbortController();
    fullPreviewController.current = requestController;
    setFullPreviewStatus("loading");
    setFullPreviewError("");
    try {
      const response = await fetch("/api/preview/full", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          config: mergeConfigOverrides(base, nextForm),
          anchor: nextForm.anchor,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isFullPreviewResponse(body)) {
        setFullPreview(null);
        setFullPreviewStatus("error");
        setFullPreviewError("Seviye önizlemesi hesaplanamadı.");
        return;
      }
      setFullPreview(body.data);
      setFullPreviewStatus("ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setFullPreview(null);
      setFullPreviewStatus("error");
      setFullPreviewError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    }
  }

  async function createDcaSession(fields: DcaSessionCreateFields) {
    if (paperConfig === null) {
      setDcaSessionCreateError("Taban config henüz yüklenmedi.");
      return;
    }
    dcaSessionsController.current?.abort();
    const requestController = new AbortController();
    dcaSessionsController.current = requestController;
    setDcaSessionCreateBusy(true);
    setDcaSessionCreateError("");
    setDcaSessionCreatedId(null);
    try {
      const response = await fetch("/api/testnet/dca-sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: fields.session_id,
          symbol: fields.symbol,
          config: mergeConfigOverrides(paperConfig, form),
          bot_id: fields.bot_id === "" ? null : fields.bot_id,
          starting_balance: fields.starting_balance === "" ? null : fields.starting_balance,
          mode: fields.mode,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isDcaSessionCreateResponse(body)) {
        setDcaSessionCreateError("Oturum açılamadı (kimlik çakışması ya da config reddi olabilir).");
        return;
      }
      setDcaSessionCreatedId(body.data.session_id);
      void loadDcaSessions();
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDcaSessionCreateError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDcaSessionCreateBusy(false);
    }
  }

  /* Faz 17 AA.13: stüdyodan tek-tık paper-açılış — mevcut createDcaSession
   * handler'ı aynen yeniden kullanılır (config = o anki studio bindirmesi,
   * mode PAPER sabit, kimlik otomatik). Başarı/hata reaktif: liste otomatik
   * tazelenir, sonuç studio-panelinde bildirilir (aynı ekran, yönlendirme
   * gerekmez). */
  function launchPaperFromStudio() {
    const symbol = paperConfig !== null && typeof paperConfig.symbol === "string" ? paperConfig.symbol : "";
    if (paperConfig === null || symbol === "") {
      setDcaSessionCreateError("Taban config/sembol hazır değil — paper.json bekleniyor.");
      return;
    }
    void createDcaSession({
      session_id: `paper-${symbol}-${Date.now()}`,
      symbol,
      bot_id: "",
      starting_balance: "",
      mode: "PAPER",
    });
  }

  async function loadDcaSessions() {
    dcaSessionsController.current?.abort();
    const requestController = new AbortController();
    dcaSessionsController.current = requestController;
    setDcaSessionsBusy(true);
    setDcaSessionsError("");
    try {
      const response = await fetch("/api/testnet/dca-sessions", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isDcaSessionList(body)) {
        setDcaSessionsError("DCA oturumları alınamadı.");
        return;
      }
      setDcaSessions(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDcaSessionsError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDcaSessionsBusy(false);
    }
  }

  /* Faz 17 AA.4b: satır-seçimi → detay + öneri okuma (salt-okunur). */
  function selectDcaSession(sessionId: string) {
    setDcaSelectedId(sessionId);
    setDcaSyncError("");
    setDcaSyncNotice("");
    setDcaPlaceError("");
    setDcaPlaceNotice("");
    setPaperFillError("");
    setPaperFillNotice("");
    setDcaPlaceDraft(null);
    setDcaPlaceDialogError("");
    void loadDcaSessionDetail(sessionId);
  }

  function closeDcaSessionDetail() {
    dcaDetailController.current?.abort();
    setDcaSelectedId(null);
    setDcaDetail(null);
    setDcaDecision(null);
    setDcaDecisionLoaded(false);
    setDcaDetailBusy(false);
    setDcaDetailError("");
    setDcaSyncBusyRole(null);
    setDcaSyncError("");
    setDcaSyncNotice("");
    setDcaPlaceDraft(null);
    setDcaPlaceBusy(false);
    setDcaPlaceError("");
    setDcaPlaceNotice("");
    setDcaPlaceDialogError("");
    setPaperFillBusy(false);
    setPaperFillError("");
    setPaperFillNotice("");
  }

  async function loadDcaSessionDetail(sessionId: string) {
    dcaDetailController.current?.abort();
    const requestController = new AbortController();
    dcaDetailController.current = requestController;
    setDcaDetailBusy(true);
    setDcaDetailError("");
    setDcaDetail(null);
    setDcaDecision(null);
    setDcaDecisionLoaded(false);
    try {
      const detailResponse = await fetch(`/api/testnet/dca-sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store", signal: requestController.signal });
      const detailBody = (await detailResponse.json()) as unknown;
      if (!detailResponse.ok || !isDcaSessionDetailResponse(detailBody)) {
        setDcaDetailError("Oturum detayı alınamadı.");
        return;
      }
      setDcaDetail(detailBody.data);
      const decisionResponse = await fetch(`/api/testnet/dca-sessions/${encodeURIComponent(sessionId)}/decision`, { cache: "no-store", signal: requestController.signal });
      const decisionBody = (await decisionResponse.json()) as unknown;
      if (!decisionResponse.ok || !isDcaSessionDecisionResponse(decisionBody)) {
        setDcaDetailError("Motor önerisi alınamadı (detay okundu, öneri yok sayılır).");
        return;
      }
      setDcaDecision(decisionBody.data);
      setDcaDecisionLoaded(true);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDcaDetailError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDcaDetailBusy(false);
    }
  }

  /* Faz 17 AA.4c: sync — salt-okunur venue okuması, onay gerektirmez.
   * Gövde yalnız {role}; başarı yanıtı tam rapordur (detay aynen yenilenir). */
  async function syncDcaSessionRole(role: string) {
    if (dcaSelectedId === null) return;
    const sessionId = dcaSelectedId;
    dcaDetailController.current?.abort();
    const requestController = new AbortController();
    dcaDetailController.current = requestController;
    setDcaSyncBusyRole(role);
    setDcaSyncError("");
    setDcaSyncNotice("");
    try {
      const response = await fetch(`/api/testnet/dca-sessions/${encodeURIComponent(sessionId)}/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isDcaSessionDetailResponse(body)) {
        setDcaSyncError(`'${role}' eşitlenemedi (bağlantı ya da venue yanıtı olabilir).`);
        return;
      }
      setDcaDetail(body.data);
      setDcaSyncNotice(`'${role}' venue'den okundu — emir verilmedi.`);
      void loadDcaSessionDetail(sessionId);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDcaSyncError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDcaSyncBusyRole(null);
    }
  }

  /* Faz 17 AA.4c: place — diyalog açılırken öneri DONDURULUR; gönderilen
   * (role, qty) HER ZAMAN bu dondurulmuş kopyadır, serbest girdi yoktur.
   * Fiyat/notional yalnız ÖNİZLEME olarak taşınır, /place'e gönderilmez. */
  function openDcaPlaceDialog() {
    if (dcaSelectedId === null || dcaDetail === null || !dcaDecisionLoaded || dcaDecision === null) return;
    setDcaPlaceError("");
    setDcaPlaceDialogError("");
    setDcaPlaceDraft({ role: dcaDecision.role, qty: dcaDecision.qty, limit_price: dcaDecision.limit_price, notional: dcaDecision.notional });
  }

  function closeDcaPlaceDialog() {
    if (dcaPlaceBusy) return;
    setDcaPlaceDraft(null);
    setDcaPlaceDialogError("");
  }

  /* Paper-spot: paper-fill — place'in ONAYSIZ kardeşi (gerçek para yok,
   * credential/kill-switch/confirmed YOK). Gövde {role, qty} YALNIZ o anki
   * önerinin dondurulmuş kopyasıdır; serbest girdi yoktur. 409'da place ile
   * AYNI davranış (öneri değişti → yeniden-oku). Yanıt tam detay-raporudur. */
  async function paperFillDcaSession() {
    if (dcaSelectedId === null || !dcaDecisionLoaded || dcaDecision === null) return;
    const sessionId = dcaSelectedId;
    const draft = { role: dcaDecision.role, qty: dcaDecision.qty };
    dcaDetailController.current?.abort();
    const requestController = new AbortController();
    dcaDetailController.current = requestController;
    setPaperFillBusy(true);
    setPaperFillError("");
    setPaperFillNotice("");
    try {
      const response = await fetch(`/api/testnet/dca-sessions/${encodeURIComponent(sessionId)}/paper-fill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: draft.role, qty: draft.qty }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (response.status === 409) {
        setPaperFillError("Motorun önerisi değişti — doldurulmadı. Güncel öneri okunuyor.");
        void loadDcaSessionDetail(sessionId);
        void loadDcaSessions();
        return;
      }
      if (!response.ok || !isDcaSessionDetailResponse(body)) {
        setPaperFillError("Paper dolum yapılamadı (422 ya da bağlantı olabilir).");
        return;
      }
      setDcaDetail(body.data);
      setPaperFillNotice(`Paper dolduruldu (${draft.role} ${draft.qty}) — gerçek emir verilmedi.`);
      void loadDcaSessionDetail(sessionId);
      void loadDcaSessions();
    } catch (error) {
      if (requestController.signal.aborted) return;
      setPaperFillError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setPaperFillBusy(false);
    }
  }

  /* Faz 17 AA.4c: confirmed:true YALNIZ bu fonksiyonda yazılır; çağrı yolu
   * yalnız diyalogdaki "Onayla ve gönder" düğmesidir (başka çağrı YOK). */
  async function confirmDcaPlaceOrder() {
    if (dcaSelectedId === null || dcaPlaceDraft === null) return;
    const sessionId = dcaSelectedId;
    const draft = dcaPlaceDraft;
    dcaDetailController.current?.abort();
    const requestController = new AbortController();
    dcaDetailController.current = requestController;
    setDcaPlaceBusy(true);
    setDcaPlaceDialogError("");
    try {
      const response = await fetch(`/api/testnet/dca-sessions/${encodeURIComponent(sessionId)}/place`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: draft.role, qty: draft.qty, confirmed: true }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (response.status === 409) {
        setDcaPlaceDraft(null);
        setDcaPlaceError("Motorun önerisi değişti — gönderilmedi. Güncel öneri okunuyor.");
        void loadDcaSessionDetail(sessionId);
        void loadDcaSessions();
        return;
      }
      if (!response.ok || !isDcaSessionPlaceResponse(body)) {
        setDcaPlaceDialogError("Emir gönderilemedi (gate kapalı, 422 ya da bağlantı olabilir).");
        return;
      }
      setDcaPlaceDraft(null);
      setDcaPlaceNotice(`Emir iletildi: venue #${String(body.data.venue_order_id)} (${body.data.venue_status}).`);
      void loadDcaSessionDetail(sessionId);
      void loadDcaSessions();
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDcaPlaceDialogError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDcaPlaceBusy(false);
    }
  }

  /* Faz 17 AA.7b: OPT taraması — salt-okunur sweep, offline.
   * 409 (sweep meşgul) ve 422 (uzay/config reddi) ayrı mesajlanır. */
  async function runSweepOptimize(payload: SweepOptimizePayload) {
    if (selectedDatasetId === null || selectedHistoricalProfileId === null) {
      setSweepError("Dataset + profil seçilmeden tarama koşulamaz.");
      return;
    }
    sweepController.current?.abort();
    const requestController = new AbortController();
    sweepController.current = requestController;
    setSweepBusy(true);
    setSweepError("");
    setSweepResult(null);
    try {
      const response = await fetch("/api/sweeps/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          profile_id: selectedHistoricalProfileId,
          space: payload.space,
          max_trials: payload.max_trials,
          sampler: payload.sampler,
          seed: payload.seed,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (response.status === 409) {
        setSweepError("Başka bir tarihsel koşu sürüyor — bitince tekrar deneyin.");
        return;
      }
      if (!response.ok || !isSweepOptimizeResponse(body)) {
        setSweepError("Tarama koşulamadı (uzay reddi ya da bağlantı olabilir).");
        return;
      }
      setSweepResult(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSweepError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setSweepBusy(false);
    }
  }

  /* Faz 17 AA.7c: overfitting değerlendirmesi — PBO/DSR salt-okunur. */
  async function runOverfitting(payload: OverfittingPayload) {
    if (selectedDatasetId === null || selectedHistoricalProfileId === null) {
      setOverfitError("Dataset + profil seçilmeden değerlendirme koşulamaz.");
      return;
    }
    overfitController.current?.abort();
    const requestController = new AbortController();
    overfitController.current = requestController;
    setOverfitBusy(true);
    setOverfitError("");
    setOverfitResult(null);
    try {
      const response = await fetch("/api/sweeps/overfitting", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          profile_id: selectedHistoricalProfileId,
          space: payload.space,
          max_trials: payload.max_trials,
          sampler: payload.sampler,
          seed: payload.seed,
          block_count: payload.block_count,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (response.status === 409) {
        setOverfitError("Başka bir tarihsel koşu sürüyor — bitince tekrar deneyin.");
        return;
      }
      if (!response.ok || !isOverfittingResponse(body)) {
        setOverfitError("Değerlendirme koşulamadı (uzay/blok reddi ya da bağlantı olabilir).");
        return;
      }
      setOverfitResult(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setOverfitError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setOverfitBusy(false);
    }
  }

  /* Faz 17 AA.7b: tarif → sihirbaza doldur (yalnız eşleme, hesap yok).
   * Nonce her dolduruşta artar; sihirbaz nonce-başına tek-kez uygular. */
  function fillSweepWizard(overrides: SweepTrialOverrides) {
    sweepFillNonce.current += 1;
    setSweepFill({ values: { ...overrides }, nonce: sweepFillNonce.current });
    selectSection("create");
  }

  /* Faz 17 AA.13a: preset-compare — iki şablon AYNI datasette, salt-okunur.
   * 409 ikiye ayrılır: ARTIFACT_MISMATCH (seçim bayat) vs EXECUTION_BUSY. */
  async function runPresetCompare(payload: PresetComparePayload) {
    const dataset = datasets.find((entry) => entry.dataset_id === selectedDatasetId) ?? null;
    const artifact = dataset?.artifact?.sha256 ?? null;
    if (selectedDatasetId === null || artifact === null) {
      setCompareError("Dataset + artifact seçilmeden karşılaştırma koşulamaz.");
      return;
    }
    compareController.current?.abort();
    const requestController = new AbortController();
    compareController.current = requestController;
    setCompareBusy(true);
    setCompareError("");
    setCompareResult(null);
    try {
      const response = await fetch("/api/presets/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: selectedDatasetId,
          artifact_sha256: artifact,
          a: payload.a,
          b: payload.b,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (response.status === 409 && typeof body === "object" && body !== null && (body as Record<string, unknown>).code === "ARTIFACT_MISMATCH") {
        setCompareError("Dataset artifact değişmiş — kataloğu yenileyip tekrar seçin.");
        return;
      }
      if (response.status === 409) {
        setCompareError("Başka bir tarihsel koşu sürüyor — bitince tekrar deneyin.");
        return;
      }
      if (!response.ok || !isPresetCompareResponse(body)) {
        setCompareError("Karşılaştırma koşulamadı (şablon/profil/cap reddi olabilir).");
        return;
      }
      setCompareResult(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCompareError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCompareBusy(false);
    }
  }

  /* Faz 17 AA.10b: korelasyon serisi — seçili datasetin kapanışları (salt
   * metin-taşıma; simülasyon-grafiği state'inden BAĞIMSIZ slot-state). */
  async function loadCorrelationSeries(slot: "x" | "y", datasetId: string) {
    const expectedArtifact = datasets.find((entry) => entry.dataset_id === datasetId)?.artifact?.sha256 ?? null;
    if (expectedArtifact === null) {
      setCorrSeriesError("Dataset artifact yok — katalogdan doğrulayın.");
      return;
    }
    corrSeriesController.current?.abort();
    const requestController = new AbortController();
    corrSeriesController.current = requestController;
    setCorrSeriesBusy(true);
    setCorrSeriesError("");
    try {
      const response = await fetch(`/api/datasets/${encodeURIComponent(datasetId)}/chart-data`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as HistoricalChartData & DatasetApiError;
      if (!response.ok || body.model_id !== "historical_ohlcv_v1" || body.dataset_id !== datasetId || body.artifact_sha256 !== expectedArtifact || !Array.isArray(body.bars)) {
        setCorrSeriesError("Seri yüklenemedi (kapsam-dışı ya da artifact-uyumsuz olabilir).");
        return;
      }
      const closes = body.bars.map((bar) => bar.close);
      if (slot === "x") {
        setCorrClosesX(closes);
        setCorrLabelX(datasetId);
      } else {
        setCorrClosesY(closes);
        setCorrLabelY(datasetId);
      }
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCorrSeriesError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCorrSeriesBusy(false);
    }
  }

  /* Faz 17 AA.10b: korelasyon kapısı — salt-okunur değerlendirme. */
  async function runCorrelationGate(payload: CorrelationGatePayload) {
    corrGateController.current?.abort();
    const requestController = new AbortController();
    corrGateController.current = requestController;
    setCorrBusy(true);
    setCorrError("");
    setCorrResult(null);
    try {
      const response = await fetch("/api/risk/correlation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prices_x: payload.prices_x,
          prices_y: payload.prices_y,
          windows: payload.windows,
          threshold_numerator: payload.threshold_numerator,
          threshold_denominator: payload.threshold_denominator,
          scale: payload.scale,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isCorrelationGateResponse(body)) {
        setCorrError("Kapı değerlendirilemedi (seri/eşik/pencere reddi olabilir).");
        return;
      }
      setCorrResult(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCorrError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCorrBusy(false);
    }
  }

  /* Faz 17 AA.13b: portföy-halkası — salt-okunur testnet toplamı. */
  /* Faz 17 AA.8: rejim serisi — chart-data barları (tam OHLC, artifact-kontrollü). */
  async function loadRegimeSeries(datasetId: string) {
    const expectedArtifact = datasets.find((entry) => entry.dataset_id === datasetId)?.artifact?.sha256 ?? null;
    if (expectedArtifact === null) {
      setRegimeSeriesError("Dataset artifact yok — katalogdan doğrulayın.");
      return;
    }
    regimeSeriesController.current?.abort();
    const requestController = new AbortController();
    regimeSeriesController.current = requestController;
    setRegimeSeriesBusy(true);
    setRegimeSeriesError("");
    try {
      const response = await fetch(`/api/datasets/${encodeURIComponent(datasetId)}/chart-data`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as HistoricalChartData & DatasetApiError;
      if (!response.ok || body.model_id !== "historical_ohlcv_v1" || body.dataset_id !== datasetId || body.artifact_sha256 !== expectedArtifact || !Array.isArray(body.bars)) {
        setRegimeSeriesError("Seri yüklenemedi (kapsam-dışı ya da artifact-uyumsuz olabilir).");
        return;
      }
      const shaped = body.bars.every((bar) => typeof bar.high === "string" && typeof bar.low === "string" && typeof bar.close === "string");
      if (!shaped) {
        setRegimeSeriesError("Seri bar-şekli bozuk (high/low/close string olmalı).");
        return;
      }
      setRegimeBars(body.bars);
      setRegimeLabel(datasetId);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setRegimeSeriesError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setRegimeSeriesBusy(false);
    }
  }

  /* Faz 17 AA.8: rejim kapısı — salt-okunur değerlendirme. */
  async function runRegimeGate(payload: RegimeGatePayload) {
    regimeGateController.current?.abort();
    const requestController = new AbortController();
    regimeGateController.current = requestController;
    setRegimeBusy(true);
    setRegimeError("");
    setRegimeResult(null);
    try {
      const response = await fetch("/api/risk/regime", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bars: payload.bars,
          adx_window: payload.adx_window,
          bb_window: payload.bb_window,
          bb_num_std: payload.bb_num_std,
          trend_threshold: payload.trend_threshold,
          range_threshold: payload.range_threshold,
          squeeze_threshold: payload.squeeze_threshold,
        }),
        signal: requestController.signal,
      });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isRegimeGateResponse(body)) {
        setRegimeError("Rejim değerlendirilemedi (bar/pencere/eşik reddi olabilir).");
        return;
      }
      setRegimeResult(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setRegimeError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setRegimeBusy(false);
    }
  }

  /* Faz 17 AA.8b: kayıt defteri — salt-okunur liste. */
  async function fetchIndicatorRegistry() {
    registryController.current?.abort();
    const requestController = new AbortController();
    registryController.current = requestController;
    setRegistryBusy(true);
    setRegistryError("");
    try {
      const response = await fetch("/api/indicators/registry", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isIndicatorRegistryResponse(body)) {
        setRegistryError("Kayıt defteri okunamadı.");
        return;
      }
      setRegistryNames(body.data.indicators);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setRegistryError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setRegistryBusy(false);
    }
  }

  /* Faz 17 AA.12: sistem-sağlığı — salt-okunur yoklama. */
  async function fetchSystemStatus() {
    systemController.current?.abort();
    const requestController = new AbortController();
    systemController.current = requestController;
    setSystemBusy(true);
    setSystemError("");
    try {
      const response = await fetch("/api/system/status", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isSystemStatusResponse(body)) {
        setSystemError("Sistem durumu okunamadı.");
        return;
      }
      setSystemStatus(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSystemError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setSystemBusy(false);
    }
  }

  /* Faz 17 AA.14: order-book derinliği — salt-okunur public veri. */
  async function loadDepth(symbol: string, limit: number) {
    depthController.current?.abort();
    const requestController = new AbortController();
    depthController.current = requestController;
    setDepthBusy(true);
    setDepthError("");
    try {
      const response = await fetch(`/api/public/depth?symbol=${encodeURIComponent(symbol)}&limit=${encodeURIComponent(String(limit))}`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isDepthBookResponse(body)) {
        setDepthError("Derinlik okunamadı (sembol/limit reddi ya da venue-hatası olabilir).");
        return;
      }
      setDepthBook(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setDepthError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setDepthBusy(false);
    }
  }

  async function loadPortfolio() {
    portfolioController.current?.abort();
    const requestController = new AbortController();
    portfolioController.current = requestController;
    setPortfolioBusy(true);
    setPortfolioError("");
    try {
      const response = await fetch("/api/portfolio/dca-performance", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isPortfolioDcaPerformanceResponse(body)) {
        setPortfolioError("Portföy okunamadı.");
        return;
      }
      setPortfolioData(body.data);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setPortfolioError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setPortfolioBusy(false);
    }
  }

  /* Faz 17 AA.1: capabilities — statik mod-bildirimi, açılışta bir kez. */
  async function fetchCapabilities() {
    capabilitiesController.current?.abort();
    const requestController = new AbortController();
    capabilitiesController.current = requestController;
    setCapabilitiesBusy(true);
    setCapabilitiesError("");
    try {
      const response = await fetch("/api/capabilities", { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as unknown;
      if (!response.ok || !isCapabilitiesView(body)) {
        setCapabilitiesError("Yetenekler okunamadı.");
        return;
      }
      setCapabilities(body);
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCapabilitiesError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCapabilitiesBusy(false);
    }
  }

  async function fetchCanary() {
    canaryController.current?.abort();
    const requestController = new AbortController();
    canaryController.current = requestController;
    setCanaryBusy(true);
    setCanaryError("");
    try {
      const response = await fetch("/api/risk/canary", { signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setCanaryError(parsed.error?.message ?? "Canary durumu alınamadı.");
        return;
      }
      if (isCanaryStatusView(parsed.data)) setCanary(parsed.data);
      else setCanaryError("Canary yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCanaryError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCanaryBusy(false);
    }
  }

  async function fetchLiquidation(symbol: string) {
    liquidationController.current?.abort();
    const requestController = new AbortController();
    liquidationController.current = requestController;
    liquidationSymbolRef.current = symbol;
    setLiquidation(null);
    setLiquidationBusy(true);
    setLiquidationError("");
    try {
      const response = await fetch(`/api/risk/liquidation-status/${encodeURIComponent(symbol)}`, { signal: requestController.signal });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setLiquidationError(parsed.error?.message ?? "Pozisyon riski alınamadı.");
        return;
      }
      if (isLiquidationStatusView(parsed.data)) setLiquidation(parsed.data);
      else setLiquidationError("Pozisyon riski yanıtı doğrulanamadı.");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setLiquidationError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setLiquidationBusy(false);
    }
  }

  async function setKillSwitch(engaged: boolean, reason: string) {
    canaryController.current?.abort();
    const requestController = new AbortController();
    canaryController.current = requestController;
    setCanaryBusy(true);
    setCanaryError("");
    try {
      const response = await fetch("/api/risk/kill-switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(engaged ? { engaged, reason } : { engaged }),
        signal: requestController.signal,
      });
      const parsed = (await response.json()) as { data?: unknown } & ApiError;
      if (!response.ok) {
        setCanaryError(parsed.error?.message ?? "Anahtar değiştirilemedi.");
        return;
      }
      await fetchCanary();
    } catch (error) {
      if (requestController.signal.aborted) return;
      setCanaryError("API yanıt vermedi. Local API'nin çalıştığını kontrol edin.");
    } finally {
      setCanaryBusy(false);
    }
  }

  async function assessExitBreakeven() {
    const parsed = await exitRequest("/api/exits/breakeven", {
      plan: {
        side: "LONG",
        anchor_price: "100",
        base_amount: "10",
        base_sizing: "QUOTE_NOTIONAL",
        safety_amount: "2",
        safety_sizing: "QUOTE_NOTIONAL",
        safety_count: 2,
        deviation: "0.01",
        step_multiplier: "2",
        volume_multiplier: "2",
        price_tick: "0.001",
        quantity_step: "0.0001",
      },
      fills: [
        { execution_id: "base", level_index: 0, quantity: "0.1", price: "100" },
        { execution_id: "s1", level_index: 1, quantity: "0.02", price: "97" },
      ],
      fee_profile: {
        settlement_asset: "USDT",
        fee_asset: "USDT",
        entry_fee_rate: "0.01",
        exit_fee_rate: "0",
        funding_cashflow: "0",
        profile_revision: "ui-sample-v1",
      },
    });
    if (parsed) {
      if (isBreakevenView(parsed.data)) setExitBreakeven(parsed.data);
      else setExitError("Çıkış yanıtı doğrulanamadı.");
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

  function loadHeroChart() {
    if (!activeDatasetId || !datasetPreflight || datasetPreflight.dataset_id !== activeDatasetId || datasetPreflightStatus !== "ready") return;
    void loadHistoricalChartData(activeDatasetId, datasetPreflight.artifact.sha256, datasetPreflight.bar_count);
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

  function selectSection(id: AppSectionId) {
    window.location.hash = buildSectionHash(id);
    setActiveSection(id);
    if (id === "create") setSavedRunsState("savedRunView", "studio");
    else if (id === "backtest") openSavedRuns();
  }

  /* Faz AB.1: hash → durum. Derin bağlar detay açar; bilinmeyen overview'a düşer.
   * Aynı değerin yeniden yazımı no-op'tur (hashchange tetiklenmez) — döngü yok. */
  function applyHashRoute(hash: string) {
    const route = parseHashRoute(hash);
    if (route.detail?.kind === "bot") {
      openBotDetail(route.detail.id);
      return;
    }
    if (route.detail?.kind === "deal") {
      openDealDetail(route.detail.id);
      return;
    }
    if (detailView !== null) closeDetail();
    selectSection(route.section);
  }

  useEffect(() => {
    applyHashRoute(window.location.hash);
    function onHashChange() {
      applyHashRoute(window.location.hash);
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  /* Faz 17 AA.11: marjin-projeksiyonu derin-bağlantısı (botlar + kaydırma).
   * scrollIntoView jsdom'da yok — `?.` zinciriyle korunur. */
  function openMarginProjection() {
    selectSection("lab");

    window.setTimeout(() => {
      document.getElementById("futures-margin-projection")?.scrollIntoView?.();
    }, 80);
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

  async function exportSavedRun(runId: string, format: "json" | "csv") {
    savedRunsController.current?.abort();
    const requestController = new AbortController();
    savedRunsController.current = requestController;
    setSavedRunsState("savedRunExportError", "");
    setSavedRunsState("savedRunExportStatus", "loading");
    try {
      const response = await fetch(`/api/historical-runs/${encodeURIComponent(runId)}/export?format=${format}`, { cache: "no-store", signal: requestController.signal });
      const body = (await response.json()) as { format?: string; filename?: string; content?: string } & SavedRunApiError;
      if (!response.ok || typeof body.content !== "string" || typeof body.filename !== "string") {
        setSavedRunsState("savedRunExportError", body.detail ?? body.title ?? "Export hazırlanamadı.");
        setSavedRunsState("savedRunExportStatus", "error");
        return;
      }
      const blob = new Blob([body.content], { type: format === "csv" ? "text/csv" : "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = body.filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setSavedRunsState("savedRunExportStatus", "ready");
    } catch (error) {
      if (requestController.signal.aborted) return;
      setSavedRunsState("savedRunExportError", "Export API'sine bağlanılamadı. Local API'nin çalıştığını kontrol edin.");
      setSavedRunsState("savedRunExportStatus", "error");
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
      noticeStore.push(body.created ? "Koşu kaydedildi." : "Koşu zaten kayıtlıydı.", "success");
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
    startPollTransition(() => {
      void poll();
    });
    return () => {
      requestController.abort();
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [downloadJob?.job_id]);

  // AA.1: Genel Bakış ilk açıldığında özeti otomatik oku (salt okunur GET),
  // böylece Durum & Veri Kaynağı kartı gerçek API durumunu gösterir.
  const dashboardAutoLoadedRef = useRef(false);
  useEffect(() => {
    if (activeSection !== "overview" || dashboardAutoLoadedRef.current) return;
    dashboardAutoLoadedRef.current = true;
    if (dashboard === null && dashboardError === "" && !dashboardBusy) void refreshDashboard();
  }, [activeSection]);

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

  const heroPreflightReady = activeDatasetId !== null && datasetPreflight !== null && datasetPreflight.dataset_id === activeDatasetId && datasetPreflightStatus === "ready";
  const heroCanLoad = heroPreflightReady && (historicalChartStatus === "idle" || historicalChartStatus === "error");
  const heroLivePrice = paperPrints.length > 0 ? paperPrints[paperPrints.length - 1].price : null;
  const heroSymbol = datasetPreflight?.instrument ?? preview?.symbol ?? "—";
  const botDetailId = detailView?.kind === "bot" ? detailView.botId : null;
  const dealDetailId = detailView?.kind === "deal" ? detailView.dealId : null;
  // D.2: bot detayı açılıp profilin ilk pair'i belli olunca venue
  // pozisyon riskini bir kez oku (sembol değişmedikçe tekrar etme).
  const liquidationSymbol = botDetailId !== null && botProfile?.bot_id === botDetailId && botProfile.pairs.length > 0 ? botProfile.pairs[0] : null;
  useEffect(() => {
    if (liquidationSymbol === null || liquidationSymbolRef.current === liquidationSymbol) return;
    void fetchLiquidation(liquidationSymbol);
  }, [botDetailId, botProfile]);
  useEffect(() => {
    if (activeSection === "lab") void loadPortfolio();
  }, [activeSection]);
  const createOverlayLines = (createView === "DCA" || botDetailId !== null) && createPreview !== null
    ? previewToPriceLines(createPreview.anchor ?? null, createPreview.levels)
    : [];
  const heroDataRange = heroPreflightReady && datasetPreflight !== null ? `${datasetPreflight.period_start} → ${datasetPreflight.period_end}` : null;

  function submit(event: FormEvent) {
    event.preventDefault();
    void calculate(form);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Ana menü">
        <div className="brand"><span>DCA</span>BOT</div>
        <SectionNav active={activeSection} onSelect={selectSection} />
        <div className="sidebar-footer"><span className="nav-icon">⚙</span>Uygulama ayarları</div>
      </aside>

      <main className="main-content" id={`section-${activeSection}`}>
        <header className="topbar">
          <h1>{sectionById(activeSection)?.heading ?? "DCABOT"}</h1>
          <div className="topbar-meta">
            <GlobalSymbolSelect symbols={venueSymbols} count={venueSymbolsCount} status={venueSymbolsStatus} error={venueSymbolsError} selectedSymbol={selectedVenueSymbol} lastPrice={venueLastPrice} priceStatus={venueLastPriceStatus} onSelect={selectVenueSymbol} onRetry={() => void loadVenueSymbols()} />
            <div className="status-strip" role="status" aria-label="Durum şeridi">
              <p className="strip-eyebrow">Piyasa</p>
              <span className="dschip">{selectedVenueSymbol ?? ""} · {venueLastPrice !== null && venueLastPrice.symbol === selectedVenueSymbol ? venueLastPrice.price : ""}</span>
            <span className="mode-chip"><span className="mode-dot" /> OFFLINE DEMO</span>
            <span className="data-status"><span className="online-dot" />Public veri</span>
            </div>
            <NotificationCenter store={noticeStore} />
            <button type="button" className="theme-toggle" aria-pressed={theme === "light"} title={t("shell.theme.label")} onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? "☾ Koyu" : "☀ Açık"}</button> <button type="button" className="theme-toggle" aria-pressed={lang === "en"} title={t("shell.language.label")} onClick={() => setLang(lang === "tr" ? "en" : "tr")}>{lang === "tr" ? "TR" : "EN"}</button>
          </div>
        </header>
        {centerError !== "" && <Banner tone="critical">Olay akışı alınamıyor: {centerError}</Banner>}
        <KillSwitchBanner canary={canary} busy={canaryBusy} onRefresh={() => void fetchCanary()} />

        {activeSection === "system" && <div className="workspace">
          <EventPanel events={centerEvents} busy={centerBusy} error={centerError} onRefresh={() => void refreshCenterEvents()} />
          <BackupPanel backups={backupList} verdict={backupVerdict} busy={backupBusy} error={backupError} onTake={(store) => void takeBackup(store)} onVerify={(backupFile) => void verifyBackupFile(backupFile)} onRefresh={() => void refreshBackups()} />
          <SystemStatusPanel status={systemStatus} busy={systemBusy} error={systemError} onRefresh={() => void fetchSystemStatus()} />
        </div>}
        {activeSection === "bots" && detailView === null && <div className="workspace">


          <BotContextHeader profile={botProfile} sessionCount={Object.keys(botSessions).length} />
          <BotTable rows={botIds.map((id) => (botProfile?.bot_id === id ? { botId: id, name: botProfile.name, sessionCount: Object.keys(botSessions).length, activeDeals: botDealCounts[id] ?? null, selected: selectedBotId === id } : { botId: id, name: null, sessionCount: null, activeDeals: botDealCounts[id] ?? null, selected: false }))} busy={botBusy} onSelect={(botId) => openBotDetail(botId)} onCreate={() => { setCreateView("DCA"); selectSection("create"); }} onOpenHistory={() => selectSection("backtest")} />

        </div>}
        {activeSection === "create" && createView === null && <div className="workspace">
          <button className="primary-button create-open-button" type="button" onClick={() => setCreateView("DCA")}>{t("create.open.label")}</button>
          <section className="panel builder-panel" aria-labelledby="builder-title">
            <div className="panel-heading"><div><p className="eyebrow">CONFIGURATION</p><h2 id="builder-title">Bot stüdyosu</h2></div><span className="revision">r{preview?.revision ?? "—"}</span></div>
            <form onSubmit={submit} noValidate>
              <NumericParameter label={t("dca.baseOrder.label")} name="anchor" value={form.anchor} suffix="USDT" error={errors.anchor} onChange={(value) => update("anchor", value)} />
              <NumericParameter label={t("dca.safetyOrder.label")} name="safety_qty" value={form.safety_qty} suffix="BTC" error={errors.safety_qty} onChange={(value) => update("safety_qty", value)} />
              <NumericParameter integer label={t("dca.safetyCount.label")} name="safety_count" value={form.safety_count} suffix="seviye" error={errors.safety_count} onChange={(value) => update("safety_count", value)} min="0" max="50" />
              <NumericParameter label={t("dca.deviation.label")} name="deviation" value={form.deviation} suffix="oran" error={errors.deviation} onChange={(value) => update("deviation", value)} />
              <NumericParameter label={t("futuresdca.leverage.label")} name="leverage" value={form.leverage} suffix="x" error={errors.leverage ?? studioLeverageIssue(form.leverage)} onChange={(value) => update("leverage", value)} />
              <SegmentedControl label={t("exit.side.label")} name="direction" value={form.direction} options={[{ value: "LONG", label: "LONG" }, { value: "SHORT", label: "SHORT" }]} onChange={(value) => update("direction", value)} />
              <SegmentedControl label={t("marginMode.label")} name="margin_mode" value={form.margin_mode} options={[{ value: "ISOLATED", label: t("marginMode.isolated.label") }, { value: "CROSS", label: t("marginMode.cross.label") }]} onChange={(value) => update("margin_mode", value)} />
              {isFuturesStyleConfig(form) && <p className="liq-fastmove" role="note">Kaldıraçlı/futures-tarzı config — likidasyon fiyatı BU EKRANDA GÖSTERİLMEZ (bilinçli karar; venue hesaplar). Paper modda testnet-emri verilmez.</p>}
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

          <FullPreviewPanel preview={fullPreview} status={fullPreviewStatus} error={fullPreviewError} baseReady={paperConfig !== null} launchBusy={dcaSessionCreateBusy} launchError={dcaSessionCreateError} launchedId={dcaSessionCreatedId} onLaunchPaper={() => launchPaperFromStudio()} />
        </div>}
        {activeSection === "bots" && detailView === null && <div className="workspace">
          <BotPanel botIds={botIds} profile={botProfile} sessions={botSessions} check={botCheck} busy={botBusy} error={botError} onRegister={(payload) => void registerBot(payload)} onSelect={(botId) => void selectBot(botId)} onUpdateLists={(payload) => void updateBotLists(payload)} onBind={(payload) => void bindBotSession(payload)} onCheck={(symbol) => void checkBotPair(symbol)} onRefresh={() => void refreshBots()} />
        </div>}
        {activeSection === "deals" && dealDetailId === null && <div className="workspace">
          <DealPanel dealId={dealId} lifecycle={dealLifecycle} history={dealHistory} bulkResults={dealBulkResults} busy={dealBusy} error={dealError} replayVerified={dealReplayVerified} onCreate={(payload) => void createDeal(payload)} onAppend={(payload) => void appendDealEvent(payload)} onReplay={() => void refreshDeal(dealId)} onBulk={(actions) => setNoticeUiState("pendingBulk", actions)} onOpenDetail={() => openDealDetail()} />
          <DcaSessionCreateForm defaultSymbol={selectedVenueSymbol ?? DEFAULT_VENUE_SYMBOL} baseReady={paperConfig !== null} busy={dcaSessionCreateBusy} error={dcaSessionCreateError} createdId={dcaSessionCreatedId} onCreate={(fields) => void createDcaSession(fields)} />
          <DcaSessionsPanel sessions={dcaSessions} busy={dcaSessionsBusy} error={dcaSessionsError} selectedId={dcaSelectedId} onRefresh={() => void loadDcaSessions()} onSelect={(sessionId) => selectDcaSession(sessionId)} />
          {dcaSelectedId !== null && (
            <DcaSessionDetailPanel
              sessionId={dcaSelectedId}
              detail={dcaDetail}
              decision={dcaDecision}
              decisionLoaded={dcaDecisionLoaded}
              busy={dcaDetailBusy}
              error={dcaDetailError}
              syncBusyRole={dcaSyncBusyRole}
              syncError={dcaSyncError}
              syncNotice={dcaSyncNotice}
              placeBusy={dcaPlaceBusy}
              placeError={dcaPlaceError}
              placeNotice={dcaPlaceNotice}
              paperFillBusy={paperFillBusy}
              paperFillError={paperFillError}
              paperFillNotice={paperFillNotice}
              onClose={() => closeDcaSessionDetail()}
              onRefresh={() => void loadDcaSessionDetail(dcaSelectedId)}
              onSync={(role) => void syncDcaSessionRole(role)}
              onPlace={() => openDcaPlaceDialog()}
              onPaperFill={() => void paperFillDcaSession()}
            />
          )}
          {dcaSelectedId !== null && dcaPlaceDraft !== null && dcaDetail !== null && (
            <DcaPlaceConfirmDialog
              sessionId={dcaSelectedId}
              symbol={dcaDetail.symbol}
              draft={dcaPlaceDraft}
              busy={dcaPlaceBusy}
              error={dcaPlaceDialogError}
              onConfirm={() => void confirmDcaPlaceOrder()}
              onCancel={() => closeDcaPlaceDialog()}
            />
          )}
          <ExitPanel binding={exitBinding} percent={exitPercent} breakeven={exitBreakeven} busy={exitBusy} error={exitError} onBind={(payload) => void bindExitCandidate(payload)} onPercentArm={(payload) => void armExitPercent(payload)} onPercentObserve={(payload) => void observeExitPercent(payload)} onBreakeven={() => void assessExitBreakeven()} />
        </div>}


        {activeSection === "lab" && <LabPanel />}
          {activeSection === "lab" && <div className="workspace"><RebalancePanel valuation={rebalanceValuation} status={rebalanceStatus} error={rebalanceError} holdingsText={rebalanceHoldingsText} pricesText={rebalancePricesText} onHoldingsChange={setRebalanceHoldingsText} onPricesChange={setRebalancePricesText} onCalculate={() => void calculateRebalance()} />
          <TemplatePanel templates={templateMetas} detail={templateDetail} bindResult={templateBindResult} diffRows={templateDiffRows} busy={templateBusy} error={templateError} onImport={(payload) => void importTemplate(payload)} onSelect={(templateId) => void selectTemplate(templateId)} onBind={(templateId, payload) => void bindTemplate(templateId, payload)} onDiff={(firstId, secondId) => void diffTemplates(firstId, secondId)} />
          <RebalancePlanPanel plan={rebalancePlan} disclosure={rebalanceDisclosure} candidates={rebalanceCandidates} busy={rebalancePlanBusy} error={rebalancePlanError} onPlan={(payload) => void submitRebalancePlan(payload)} onDisclose={(payload) => void submitRebalanceDisclose(payload)} />
          <SignalPanel payloadHash={signalHash} readiness={signalReadiness} candidate={signalCandidate} busy={signalBusy} error={signalError} onHash={(payload) => void hashSignalPayload(payload)} onAssess={(payload) => void assessSignal(payload)} onBind={(payload) => void bindSignal(payload)} />
          <FuturesPanel grid={futuresGrid} pnl={futuresPnl} trailing={futuresTrailing} funding={futuresFunding} busy={futuresBusy} error={futuresError} onGrid={(payload) => void submitFuturesGrid(payload)} onPnl={(payload) => void submitFuturesPnl(payload)} onTrailingArm={(payload) => void submitTrailingArm(payload)} onTrailingObserve={(payload) => void submitTrailingObserve(payload)} onFunding={(payload) => void submitFuturesFunding(payload)} />
        </div>}

          {activeSection === "deals" && dealDetailId === null && <div className="workspace"><RecurringPanel schedule={recurring} busy={recurringBusy} error={recurringError} onProject={(payload) => void projectRecurring(payload)} />
        </div>}
        {activeSection === "risk" && <div className="workspace">
          <RiskPanel explanation={riskExplain} busy={riskBusy} error={riskError} onExplain={(payload) => void explainRisk(payload)} canary={canary} canaryBusy={canaryBusy} canaryError={canaryError} onRefreshCanary={() => void fetchCanary()} onSetKillSwitch={(engaged, reason) => void setKillSwitch(engaged, reason)} />
          <CorrelationPanel datasets={datasets} closesX={corrClosesX} closesY={corrClosesY} labelX={corrLabelX} labelY={corrLabelY} seriesBusy={corrSeriesBusy} seriesError={corrSeriesError} busy={corrBusy} error={corrError} result={corrResult} onSelectSeries={(slot, datasetId) => void loadCorrelationSeries(slot, datasetId)} onRun={(payload) => void runCorrelationGate(payload)} />
          <RegimePanel datasets={datasets} bars={regimeBars} label={regimeLabel} seriesBusy={regimeSeriesBusy} seriesError={regimeSeriesError} busy={regimeBusy} error={regimeError} result={regimeResult} onSelectSeries={(datasetId) => void loadRegimeSeries(datasetId)} onRun={(payload) => void runRegimeGate(payload)} />
        </div>}
        {activeSection === "system" && <div className="workspace">
          <IndicatorRegistryPanel names={registryNames} busy={registryBusy} error={registryError} onRefresh={() => void fetchIndicatorRegistry()} />
        </div>}

        {activeSection === "bots" && botDetailId !== null && <div className="create-view-wrap">
          <BotDetailView
            botId={botDetailId}
            profile={botProfile}
            botIds={botIds}
            sessionCount={Object.keys(botSessions).length}
            draftParams={readDraftPreviewParams(botDetailId)}
            loading={botBusy}
            renderChart={() => <HeroChartPanel bars={historicalChartData?.bars ?? []} status={historicalChartStatus} error={historicalChartError} livePrice={heroLivePrice} symbolLabel={heroSymbol} canLoad={heroCanLoad} loadBusy={historicalChartStatus === "loading"} onLoad={loadHeroChart} overlayLines={createOverlayLines} />}
            overlayNote={createPreviewNote !== "" ? createPreviewNote : null}
            onBack={closeDetail}
            liquidation={botDetailId !== null && botProfile?.bot_id === botDetailId ? liquidation : null}
            liquidationBusy={liquidationBusy}
            liquidationError={liquidationError}
            onRefreshLiquidation={() => { if (liquidationSymbol !== null) { liquidationSymbolRef.current = null; void fetchLiquidation(liquidationSymbol); } }}
            dcaPerformance={botProfile?.bot_id === botDetailId ? botDcaPerf : null}
            dcaActiveDeals={botProfile?.bot_id === botDetailId ? botDcaActive : null}
            dcaBusy={botDcaBusy}
            dcaError={botProfile?.bot_id === botDetailId ? botDcaError : ""}
            onRefreshDca={() => { if (botDetailId !== null) void loadBotDcaStats(botDetailId); }}
            onSelectBot={(botId) => openBotDetail(botId)}
          />
        </div>}
        {activeSection === "deals" && dealDetailId !== null && <div className="create-view-wrap">
          <DealDetailView
            dealId={dealDetailId}
            lifecycle={dealLifecycle}
            history={dealHistory}
            replayVerified={dealReplayVerified}
            busy={dealBusy}
            error={dealError}
            onBack={closeDetail}
            onReplay={() => void refreshDeal(dealDetailId)}
          />
        </div>}
        {activeSection === "create" && createView !== null && <div className="create-view-wrap">
          <BotCreateView
            botType={createView ?? "DCA"}
            onBotTypeChange={setCreateView}
            onBack={() => { setCreateView(null); setCreatePreview(null); setCreatePreviewNote(""); }}
            onOpenBacktest={() => selectSection("backtest")}
            bars={historicalChartData?.bars ?? []}
            chartStatus={historicalChartStatus}
            chartError={historicalChartError}
            livePrice={heroLivePrice}
            symbolLabel={heroSymbol}
            canLoadChart={heroCanLoad}
            chartLoading={historicalChartStatus === "loading"}
            onLoadChart={loadHeroChart}
            dataRange={heroDataRange}
            backtestReady={heroPreflightReady}
            overlayLines={createOverlayLines}
            overlayNote={createPreviewNote !== "" ? createPreviewNote : null}
            aiRecommenderReady={createView === "DCA" && (datasetRunPlan?.dataset?.dataset_id ?? "") !== "" && (selectedHistoricalProfileId ?? "") !== ""}
            renderForm={(type) => type === "DCA" ? (
              <BotWizard busy={botBusy} error={botError} onRegister={(payload) => void registerBot(payload)} onParamsChange={(params) => void calculateCreate(params)} onOpenBacktest={() => selectSection("backtest")} chartBars={historicalChartData?.bars} botType={type} optimizeDatasetId={datasetRunPlan?.dataset.dataset_id} optimizeProfileId={selectedHistoricalProfileId ?? undefined} externalFill={sweepFill} />
            ) : type === "SIGNAL" ? (
              <SignalPanel payloadHash={signalHash} readiness={signalReadiness} candidate={signalCandidate} busy={signalBusy} error={signalError} onHash={(payload) => void hashSignalPayload(payload)} onAssess={(payload) => void assessSignal(payload)} onBind={(payload) => void bindSignal(payload)} />
            ) : type === "FUTURES" ? (
              <FuturesDcaForm grid={futuresGrid} busy={futuresBusy} error={futuresError} onGrid={(payload) => void submitFuturesGrid(payload)} />
            ) : (
              <FuturesPanel grid={futuresGrid} pnl={futuresPnl} trailing={futuresTrailing} funding={futuresFunding} busy={futuresBusy} error={futuresError} onGrid={(payload) => void submitFuturesGrid(payload)} onPnl={(payload) => void submitFuturesPnl(payload)} onTrailingArm={(payload) => void submitTrailingArm(payload)} onTrailingObserve={(payload) => void submitTrailingObserve(payload)} onFunding={(payload) => void submitFuturesFunding(payload)} />
            )}
          />
        </div>}
        {activeSection === "market" && <div className="workspace">
          <HeroChartPanel bars={historicalChartData?.bars ?? []} status={historicalChartStatus} error={historicalChartError} livePrice={heroLivePrice} symbolLabel={heroSymbol} canLoad={heroCanLoad} loadBusy={historicalChartStatus === "loading"} onLoad={loadHeroChart} />
        </div>}
        {activeSection === "deals" && dealDetailId === null && <div className="workspace">
          <TimelinePanel frame={timelineFrame} busy={timelineBusy} error={timelineError} onSeek={(step) => void seekTimeline(step)} />

        </div>}
        {activeSection === "deals" && dealDetailId === null && <div className="workspace">
          <PaperPanel snapshot={paperSnapshot} prints={paperPrints} busy={paperBusy} error={paperError} orderDraft={paperOrderDraft} onActivate={() => void activatePaper()} onRefresh={() => void refreshPaperMarket()} onOrderDraftChange={setPaperOrderDraft} onPlace={() => void placePaperOrder()} onFill={(clientOrderId, eventId) => void fillPaperOrder(clientOrderId, eventId)} />
        </div>}
        {activeSection === "market" && <div className="workspace">
          <BinancePublicSnapshotPanel snapshot={binancePublicSnapshot} status={binancePublicSnapshotStatus} error={binancePublicSnapshotError} onRetry={() => void loadBinancePublicSnapshot(selectedVenueSymbol ?? DEFAULT_VENUE_SYMBOL)} />
          <DepthPanel book={depthBook} initialSymbol={selectedVenueSymbol ?? DEFAULT_VENUE_SYMBOL} busy={depthBusy} error={depthError} onLoad={(symbol, limit) => void loadDepth(symbol, limit)} />
        </div>}
        {activeSection === "backtest" && <div className="workspace">
          <Suspense fallback={<div className="empty-state" role="status">Katalog yükleniyor…</div>}>
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

          </Suspense>
        </div>}
        {activeSection === "market" && <div className="workspace">

          <DatastorePanel datasets={datasets} status={datasetCatalogStatus} error={datasetCatalogError} activeJob={downloadJob} />
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
        {activeSection === "backtest" && <div className="workspace">
          <SweepOptimizePanel datasetId={selectedDatasetId} profileId={selectedHistoricalProfileId} busy={sweepBusy} error={sweepError} result={sweepResult} onRun={(payload) => void runSweepOptimize(payload)} onFillWizard={(overrides) => fillSweepWizard(overrides)} />
          <OverfittingPanel datasetId={selectedDatasetId} profileId={selectedHistoricalProfileId} busy={overfitBusy} error={overfitError} result={overfitResult} onRun={(payload) => void runOverfitting(payload)} />
        </div>}
        {activeSection === "backtest" && <div className="saved-runs-workspace"><Suspense fallback={<div className="empty-state" role="status">Koşular yükleniyor…</div>}><SavedRunsPanel view={savedRunView === "studio" ? "list" : savedRunView} runs={savedRuns} listStatus={savedRunsStatus} listError={savedRunsError} detail={savedRunDetail} detailStatus={savedRunDetailStatus} detailError={savedRunDetailError} onOpenDetail={(runId) => void openSavedRunDetail(runId)} onBackToList={openSavedRuns} compareSelection={savedRunCompareSelection} onToggleCompareSelection={toggleCompareSelection} onOpenCompare={() => void openSavedRunCompare()} compareDetails={savedRunCompareDetails} compareStatus={savedRunCompareStatus} compareError={savedRunCompareError} onExportRun={(runId, format) => void exportSavedRun(runId, format)} exportStatus={savedRunExportStatus} exportError={savedRunExportError} /></Suspense></div>}
        {activeSection === "overview" && <div className="workspace">
          <div className="tile-grid" role="group" aria-label="Özet göstergeler">
            <StatTile label="Botlar" value={dashboard ? String(dashboard.bots.bots) : ""} />
            <StatTile label="Deal'ler" value={dashboard ? String(dashboard.deals.deals) : ""} />
            <StatTile label="Paper nakit" value={dashboard ? dashboard.paper.total_cash : ""} />
            <StatTile label="Açık emirler" value={dashboard ? String(dashboard.paper.open_orders) : ""} />
          </div>
          <HeroChartPanel bars={historicalChartData?.bars ?? []} status={historicalChartStatus} error={historicalChartError} livePrice={heroLivePrice} symbolLabel={heroSymbol} canLoad={heroCanLoad} loadBusy={historicalChartStatus === "loading"} onLoad={loadHeroChart} />
          <SystemStatusCard apiStatus={dashboardError ? "error" : dashboard ? "ready" : dashboardBusy ? "loading" : "unknown"} apiError={dashboardError} datasets={datasets} datasetCatalogReady={datasetCatalogStatus === "ready"} selectedDatasetId={selectedDatasetId} canary={canary} canaryBusy={canaryBusy} canaryError={canaryError} onRefreshCanary={() => void fetchCanary()} dashboard={dashboard} dashboardBusy={dashboardBusy} dashboardError={dashboardError} capabilities={capabilities} capabilitiesBusy={capabilitiesBusy} capabilitiesError={capabilitiesError} />
          <DashboardPanel dashboard={dashboard} busy={dashboardBusy} error={dashboardError} onRefresh={() => void refreshDashboard()} />
          <AssistantPanel
            dashboard={dashboard}
            dashboardError={dashboardError}
            events={centerEvents}
            eventsError={centerError}
            canary={canary}
            canaryError={canaryError}
            busy={dashboardBusy || centerBusy || canaryBusy}
            onRefresh={() => {
              void refreshDashboard();
              void refreshCenterEvents();
              void fetchCanary();
            }}
          />
          <MarketTickerPanel ticker={venueTicker24h} symbol={selectedVenueSymbol ?? DEFAULT_VENUE_SYMBOL} status={venueTicker24hStatus} error={venueTicker24hError} onRetry={() => void loadVenueTicker24h(selectedVenueSymbol ?? DEFAULT_VENUE_SYMBOL)} />
          <IndicatorPanel kind={indicatorKind} series={indicatorSeries} status={indicatorStatus} error={indicatorError} barCount={(historicalChartData?.bars ?? []).length} onSelect={setIndicatorKind} onRetry={() => {
            const bars = historicalChartData?.bars ?? [];
            if (bars.length >= 2) void loadIndicator(indicatorKind, bars.map((bar) => bar.close).slice(-5000));
          }} />
          <GridSkeletonCard onOpenMargin={() => openMarginProjection()} />
        </div>}
        {activeSection === "system" && <div className="workspace">
          <BinanceAccountPanel account={binanceAccount} orders={binanceOpenOrders} status={binanceAccountStatus} error={binanceAccountError} onRetry={() => void loadBinanceAccount()} />
        </div>}
        {activeSection === "system" && <div className="workspace">
        <details className="dev-tools">
          <summary>Geliştirici araçları</summary>
          <TwoLegPanel sessionId={twoLegSession} projection={twoLegProjection} busy={twoLegBusy} error={twoLegError} onStart={(sessionId) => void startTwoLegSession(sessionId)} onFill={(payload) => void acceptTwoLegFill(payload)} onRecovery={() => void markTwoLegRecovery()} onTimeout={() => void markTwoLegTimeout()} onReplay={() => void replayTwoLegSession()} />
        </details>
        </div>}
        {activeSection === "lab" && <div className="workspace">
          <PresetComparePanel datasetId={selectedDatasetId} artifactSha256={datasets.find((entry) => entry.dataset_id === selectedDatasetId)?.artifact?.sha256 ?? null} templates={templateMetas} busy={compareBusy} error={compareError} result={compareResult} onRun={(payload) => void runPresetCompare(payload)} />
          <PortfolioPanel data={portfolioData} busy={portfolioBusy} error={portfolioError} onRefresh={() => void loadPortfolio()} />
        </div>}
        <ToastStack store={noticeStore} />
        {pendingBulk !== null && <ConfirmDialog title="Toplu gönderim onayı" summary={`${pendingBulk.length} deal işlemine event gönderilecek. Her deal sonucu ayrı değerlendirilir; atomik değildir.`} confirmLabel="Gönder" busy={dealBusy} onConfirm={() => { const actions = pendingBulk; setNoticeUiState("pendingBulk", null); void bulkDealEvents(actions); }} onCancel={() => setNoticeUiState("pendingBulk", null)} />}
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


function Metric({ label, value, unit }: { label: string; value: string; unit: string }) {
  return <div className="metric"><span className="metric-label">{label}</span><strong>{value}</strong><span className="metric-unit">{unit}</span></div>;
}

export default App;
