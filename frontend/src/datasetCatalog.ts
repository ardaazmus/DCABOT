export type DatasetStatus = "MISSING" | "CORRUPT" | "VERIFIED";

export type DatasetArtifact = {
  sha256: string;
  byte_size: number;
};

export type DatasetPreflight = {
  dataset_id: string;
  artifact_status: "VERIFIED";
  preflight_status: "READY";
  instrument: string;
  interval: string;
  period_start: string;
  period_end: string;
  bar_count: number;
  timestamp_unit: "microseconds";
  timezone: "UTC";
  data_quality_status: "UNKNOWN";
  data_quality_message: string;
  artifact: DatasetArtifact;
  read_only: boolean;
};

export type DatasetRunPlanConfig = {
  schema_version: 1;
  config_hash: string;
  mode: "offline";
  symbol: string;
  base_asset: string;
  quote_asset: "USDT";
  base_qty: string;
  safety_qty: string;
  safety_count: number;
  deviation: string;
  target_mode: "GROSS_PRICE_RETURN" | "NET_QUOTE";
  fee_rate: string;
  slippage: string;
  simulation_model?: "historical_ohlcv_v1" | "historical_ohlcv_partial_fixed_v1";
  slice_qty?: string | null;
};

export type HistoricalProfile = {
  profile_id: string;
  profile_version: string;
  label: string;
  expected_dataset_id: string | null;
  venue_filter_provenance: "historical_verified" | "current_observation" | "project_fixture" | "unknown";
  historical_filter_claim: boolean;
  anchor_source: "explicit" | "dataset_first_bar_open";
  simulation_model?: "historical_ohlcv_v1" | "historical_ohlcv_partial_fixed_v1";
  slice_qty?: string | null;
};

export type DatasetRunPlan = {
  dataset: DatasetPreflight;
  config: DatasetRunPlanConfig;
  profile: HistoricalProfile;
  execution_mode: "SIMULATED";
  run_status: "NOT_STARTED";
  read_only: boolean;
};

export type ReadOnlyExplanation = {
  code: string;
  severity: "INFO" | "WARNING" | "ERROR";
  title: string;
  message: string;
  source: string;
  context: Record<string, string | number>;
};

export type HistoricalSimulationResult = {
  execution_id: string | null;
  complete_execution?: boolean;
  execution_status: "COMPLETED" | "INDETERMINATE";
  application_code: "AMBIGUOUS_OHLC_PATH" | null;
  persisted: false;
  dataset: {
    dataset_id: string;
    artifact_sha256: string;
    period_start: string;
    period_end: string;
    processed_bar_count: number;
  };
  config: {
    schema_version: 1;
    config_hash: string;
    slice_qty?: string;
    quantity_unit?: "BASE_ASSET";
  };
  profile: HistoricalProfile;
  assumptions: {
    model: "historical_ohlcv_v1" | "historical_ohlcv_partial_fixed_v1";
    bar_visibility: "CLOSED_ONLY";
    intrabar_path: "NOT_INFERRED";
    max_actions_per_bar: 1;
    fee_model: string;
    slippage_model: string;
    funding: "NOT_MODELED";
    exchange_mark: "NOT_AVAILABLE";
    force_close_at_end: boolean;
    fill_policy?: string;
    synthetic_cancel_at_eof?: boolean;
    persistence?: string;
  };
  action_authority?: {
    mode: "FULL_RUN" | "COMMITTED_PREFIX" | "NONE";
    economic_state_commit_scope: "FULL_RUN" | "PREFIX_ONLY" | "NONE";
    committed_through_bar_index: number | null;
    committed_through_open_time_us: number | null;
    ambiguity_bar_index: number | null;
    contains_ambiguity_bar_actions: false;
    contains_post_ambiguity_actions: false;
    complete_history: boolean;
    economic_state_committed: boolean;
    committed_through_event_sequence: number | null;
    action_count: number;
  };
  marker_authority?: "FULL" | "PREFIX_BOUNDARY_ONLY" | "NONE";
  marker_kind?: "TRADE_EXECUTION" | "INCOMPLETE_BOUNDARY" | "NONE";
  actions: Array<{
    event_sequence?: number;
    bar_index: number;
    open_time_us: number;
    role: string;
    raw_reference: string;
    fill_price: string;
    quantity: string;
    fee: string;
    action_type?: "PARTIAL_FILL" | "FULL_FILL";
    order_id?: string;
    execution_id?: string | null;
    fee_asset?: string;
    order_status_after?: "PARTIALLY_FILLED" | "FILLED";
    original_qty?: string;
    cumulative_filled_qty?: string;
    leaves_qty?: string;
    canceled_qty?: string;
    fill_provenance?: string;
  }>;
  summary?: {
    symbol: string;
    qty: string;
    cost: string;
    realized_gross: string;
    fees: string;
    funding: string;
    realized_net_after_all_costs: string;
    unrealized: string | null;
    equity: string;
    anchor: string | null;
    take_profit_price: string | null;
    entry_notional: string;
    position_status: "CLOSED" | "OPEN_AT_END";
    funding_status: "NOT_MODELED";
    mark_status: "NOT_AVAILABLE";
  };
  final_economic_summary?: {
    symbol: string;
    qty: string;
    cost: string;
    realized_gross: string;
    fees: string;
    funding: string;
    realized_net_after_all_costs: string;
    unrealized: string | null;
    equity: string;
    anchor: string | null;
    take_profit_price: string | null;
    entry_notional: string;
    position_status: "CLOSED" | "OPEN_AT_END";
    funding_status: "NOT_MODELED";
    mark_status: "NOT_AVAILABLE";
  } | null;
  ambiguity: { bar_index: number; open_time_us?: number; code: "AMBIGUOUS_OHLC_PATH" } | null;
  explanations: ReadOnlyExplanation[];
};

export type HistoricalChartBar = {
  bar_index: number;
  open_time_us: number;
  close_time_us: number;
  open: string;
  high: string;
  low: string;
  close: string;
  base_volume: string;
};

export type HistoricalChartData = {
  dataset_id: string;
  artifact_sha256: string;
  model_id: "historical_ohlcv_v1";
  period_start: string;
  period_end: string;
  processed_bar_count: number;
  bars: HistoricalChartBar[];
};

export type DatasetSummary = {
  dataset_id: string;
  dataset_type: "kline_csv_zip";
  instrument: string;
  interval: string;
  period_start: string;
  period_end: string;
  status: DatasetStatus;
  artifact: DatasetArtifact | null;
};

export type DatasetFilter = "ALL" | DatasetStatus;
export type DatasetCatalogStatus = "idle" | "pending" | "ready" | "error";
export type DatasetSelectionStatus = "idle" | "pending" | "ready" | "error";
export type DownloadJobStatus = "QUEUED" | "RUNNING" | "RETRYING" | "SUCCEEDED" | "FAILED" | "CANCELLED";
export type DownloadJobUiStatus = "idle" | "starting" | "polling" | "canceling" | "error";

export type DatasetDownloadJob = {
  job_id: string;
  dataset_id: string;
  status: DownloadJobStatus;
  attempt: number;
  max_attempts: number;
  bytes_downloaded: number;
  total_bytes: number | null;
  cache_hit: boolean | null;
  error_code: string | null;
  error_message: string | null;
};

export const DATASET_STATUS_ORDER: DatasetStatus[] = ["VERIFIED", "MISSING", "CORRUPT"];

export const DATASET_STATUS_META: Record<DatasetStatus, { icon: string; label: string; description: string }> = {
  VERIFIED: { icon: "✓", label: "Doğrulandı", description: "Yerel artifact bütünlük kontrolünden geçti." },
  MISSING: { icon: "–", label: "Yerel kopya yok", description: "Katalog tanımı var; doğrulanmış cache bulunamadı." },
  CORRUPT: { icon: "!", label: "Bütünlük hatası", description: "Yerel artifact doğrulamadan geçemedi." },
};

export function formatDatasetBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function shortSha256(sha256: string): string {
  return `${sha256.slice(0, 12)}…${sha256.slice(-8)}`;
}

export function isActiveDownloadJob(status: DownloadJobStatus): boolean {
  return status === "QUEUED" || status === "RUNNING" || status === "RETRYING";
}
