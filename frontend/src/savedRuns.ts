export type SavedRunRecordHealth = "OK" | "CORRUPT";
export type SavedRunExecutionStatus = "COMPLETED" | "INDETERMINATE";

export type SavedRunListItem = {
  run_id: string;
  created_at: string;
  execution_status: SavedRunExecutionStatus;
  record_health: SavedRunRecordHealth;
  symbol: string;
  interval: string;
  period_start: string;
  period_end: string;
  processed_bar_count: number;
  position_status: "CLOSED" | "OPEN_AT_END";
};

export type SavedRunListResponse = {
  runs: SavedRunListItem[];
  count: number;
};

export type SavedRunDetail = {
  run_id: string;
  created_at: string;
  storage_state: "STORED";
  execution_status: SavedRunExecutionStatus;
  dataset: Record<string, unknown>;
  input_snapshot: Record<string, unknown>;
  config: Record<string, unknown>;
  instrument_risk: Record<string, unknown>;
  execution: Record<string, unknown>;
  result_snapshot: Record<string, unknown>;
  result_sha256: string;
  record_sha256: string;
};

export type SavedRunSaveResponse = {
  run_id: string;
  created: boolean;
  record_health: "OK";
  execution_status: SavedRunExecutionStatus;
  created_at: string;
  dataset_id: string;
  symbol: string;
  interval: string;
  period_start: string;
  period_end: string;
  processed_bar_count: number;
  position_status: "CLOSED" | "OPEN_AT_END";
};

export type SavedRunApiError = {
  code?: string;
  detail?: string;
  title?: string;
};
