import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ActionTable, PreflightCard } from "./DatasetCatalogPanel";
import type { DatasetPreflight, DatasetRunPlan, HistoricalProfile, HistoricalSimulationResult } from "./datasetCatalog";
import { WHAT_IF_AUTO_RUN_DELAY_MS } from "./useWhatIfAutoRun";

const actions: HistoricalSimulationResult["actions"] = [
  {
    bar_index: 1,
    open_time_us: 1,
    role: "BASE",
    raw_reference: "bar-1",
    fill_price: "100",
    quantity: "1",
    fee: "0",
  },
  {
    bar_index: 2,
    open_time_us: 3,
    role: "SAFETY",
    raw_reference: "bar-2",
    fill_price: "101",
    quantity: "2",
    fee: "0",
  },
];

describe("ActionTable keyboard selection", () => {
  it("Enter tuşu satır seçimini bildirir", () => {
    const onSelectBarIndex = vi.fn();
    render(<ActionTable actions={actions} fixedSlice={false} onSelectBarIndex={onSelectBarIndex} />);

    fireEvent.keyDown(screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" }), { key: "Enter" });

    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });

  it("Space tuşu satır seçimini bildirir, ilgisiz tuş bildirmez", () => {
    const onSelectBarIndex = vi.fn();
    render(<ActionTable actions={actions} fixedSlice={false} onSelectBarIndex={onSelectBarIndex} />);

    const row = screen.getByRole("button", { name: "Bar 2 aksiyonunu seç" });
    fireEvent.keyDown(row, { key: "a" });
    expect(onSelectBarIndex).not.toHaveBeenCalled();

    fireEvent.keyDown(row, { key: " " });
    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(2);
  });

  it("seçim handler'ı yoksa satır klavyeyle odaklanamaz", () => {
    render(<ActionTable actions={actions} fixedSlice={false} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".historical-action-row-interactive")).toHaveLength(0);
  });

  it("satır içindeki Kopyala butonuna tıklamak veya orada Enter'a basmak satırı seçmez", () => {
    const onSelectBarIndex = vi.fn();
    render(<ActionTable actions={actions} fixedSlice={true} onSelectBarIndex={onSelectBarIndex} />);

    const copyButton = screen.getAllByRole("button", { name: "Kopyala" })[0];
    fireEvent.click(copyButton);
    fireEvent.keyDown(copyButton, { key: "Enter" });

    expect(onSelectBarIndex).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" }));
    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });
});

const whatIfPreflight: DatasetPreflight = {
  dataset_id: "ds-1",
  artifact_status: "VERIFIED",
  preflight_status: "READY",
  instrument: "BTCUSDT",
  interval: "1h",
  period_start: "2026-01-01",
  period_end: "2026-01-31",
  bar_count: 100,
  timestamp_unit: "microseconds",
  timezone: "UTC",
  data_quality_status: "UNKNOWN",
  data_quality_message: "Kalite bilgisi yok.",
  artifact: { sha256: "a".repeat(64), byte_size: 1024 },
  read_only: true,
};

const whatIfProfile: HistoricalProfile = {
  profile_id: "prof-1",
  profile_version: "1",
  label: "Test profili",
  expected_dataset_id: null,
  venue_filter_provenance: "project_fixture",
  historical_filter_claim: false,
  anchor_source: "explicit",
  simulation_model: "historical_ohlcv_v1",
};

const whatIfFixedSliceProfile: HistoricalProfile = {
  ...whatIfProfile,
  profile_id: "prof-fixed",
  simulation_model: "historical_ohlcv_partial_fixed_v1",
};

function whatIfRunPlan(profile: HistoricalProfile): DatasetRunPlan {
  return {
    dataset: whatIfPreflight,
    config: {
      schema_version: 1,
      config_hash: "c".repeat(64),
      mode: "offline",
      symbol: "BTCUSDT",
      base_asset: "BTC",
      quote_asset: "USDT",
      base_qty: "0.001",
      safety_qty: "0.001",
      safety_count: 3,
      deviation: "0.02",
      target_mode: "GROSS_PRICE_RETURN",
      fee_rate: "0.001",
      slippage: "0.0005",
    },
    profile,
    execution_mode: "SIMULATED",
    run_status: "NOT_STARTED",
    read_only: true,
  };
}

function renderPreflightCard(overrides: { runPlan?: DatasetRunPlan; profile?: HistoricalProfile; simulationStatus?: "idle" | "error"; onStartHistoricalSimulation?: () => void } = {}) {
  const profile = overrides.profile ?? whatIfProfile;
  const onStartHistoricalSimulation = overrides.onStartHistoricalSimulation ?? vi.fn();
  render(
    <PreflightCard
      preflight={whatIfPreflight}
      status="ready"
      error=""
      historicalProfiles={[profile]}
      historicalProfilesStatus="ready"
      historicalProfilesError=""
      selectedHistoricalProfileId={profile.profile_id}
      onHistoricalProfileChange={() => {}}
      onRetryHistoricalProfiles={() => {}}
      runPlan={overrides.runPlan ?? whatIfRunPlan(profile)}
      runPlanStatus="ready"
      runPlanError=""
      simulation={null}
      simulationStatus={overrides.simulationStatus ?? "idle"}
      simulationError=""
      chartData={null}
      chartStatus="idle"
      chartError=""
      onStartHistoricalSimulation={onStartHistoricalSimulation}
      historicalSaveStatus="idle"
      historicalSaveError=""
      onSaveHistoricalRun={() => {}}
      onOpenSavedRuns={() => {}}
    />,
  );
  return { onStartHistoricalSimulation: onStartHistoricalSimulation as ReturnType<typeof vi.fn> };
}

describe("PreflightCard What-If otomatik çalıştırma (B.5)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("anahtar varsayılan olarak kapalıdır ve plan hazır olsa bile otomatik çalıştırmaz", () => {
    const { onStartHistoricalSimulation } = renderPreflightCard();

    const toggle = screen.getByRole("checkbox", { name: "What-If: plan değişince simülasyonu otomatik çalıştır" });
    expect(toggle).not.toBeChecked();
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS + 1000);
    });
    expect(onStartHistoricalSimulation).not.toHaveBeenCalled();
  });

  it("anahtar açılınca debounce sonunda simülasyonu onay sorulmadan bir kez başlatır", () => {
    const { onStartHistoricalSimulation } = renderPreflightCard();

    fireEvent.click(screen.getByRole("checkbox", { name: "What-If: plan değişince simülasyonu otomatik çalıştır" }));
    expect(screen.getByText("Otomatik çalıştırma bekleniyor…")).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS);
    });

    expect(onStartHistoricalSimulation).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Simülasyonu başlat?")).not.toBeInTheDocument();
  });

  it("fixed-slice profilinde model onayı işaretlenmeden otomatik çalıştırmaz", () => {
    const { onStartHistoricalSimulation } = renderPreflightCard({ profile: whatIfFixedSliceProfile });

    fireEvent.click(screen.getByRole("checkbox", { name: "What-If: plan değişince simülasyonu otomatik çalıştır" }));
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS + 1000);
    });

    expect(onStartHistoricalSimulation).not.toHaveBeenCalled();
  });

  it("fixed-slice onayı işaretlenince otomatik çalıştırma devreye girer", () => {
    const { onStartHistoricalSimulation } = renderPreflightCard({ profile: whatIfFixedSliceProfile });

    fireEvent.click(screen.getByRole("checkbox", { name: "Bu fixed-slice tarihsel modelini anlıyorum ve çalıştırmayı onaylıyorum." }));
    fireEvent.click(screen.getByRole("checkbox", { name: "What-If: plan değişince simülasyonu otomatik çalıştır" }));
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS);
    });

    expect(onStartHistoricalSimulation).toHaveBeenCalledTimes(1);
  });
});

const completedSummary = {
  symbol: "BTCUSDT",
  qty: "0.002",
  cost: "195",
  realized_gross: "14",
  fees: "1.2",
  funding: "0",
  realized_net_after_all_costs: "12.8",
  unrealized: null,
  equity: "1012.8",
  anchor: "97000",
  take_profit_price: "99450",
  entry_notional: "195",
  position_status: "CLOSED",
  funding_status: "NOT_MODELED",
  mark_status: "NOT_AVAILABLE",
  win_count: 3,
  win_rate: "0.75",
  profit_factor: null,
  roi: "0.125",
  safety_order_fill_count: 4,
  safety_order_fill_rate: "0.5",
} as const;

function completedSimulation(): HistoricalSimulationResult {
  return {
    execution_id: "exec-1",
    execution_status: "COMPLETED",
    application_code: null,
    persisted: false,
    dataset: {
      dataset_id: "ds-1",
      artifact_sha256: "a".repeat(64),
      period_start: "2026-01-01",
      period_end: "2026-01-31",
      processed_bar_count: 100,
    },
    config: { schema_version: 1, config_hash: "c".repeat(64) },
    profile: whatIfProfile,
    assumptions: {
      model: "historical_ohlcv_v1",
      bar_visibility: "CLOSED_ONLY",
      intrabar_path: "NOT_INFERRED",
      max_actions_per_bar: 1,
      fee_model: "CONFIGURED_RATE_ON_EACH_FILL",
      slippage_model: "CONFIGURED_DETERMINISTIC_ON_EACH_FILL",
      funding: "NOT_MODELED",
      exchange_mark: "NOT_AVAILABLE",
      force_close_at_end: false,
    },
    actions,
    summary: { ...completedSummary },
    ambiguity: null,
    explanations: [],
  };
}

function renderCompletedCard(simulation: HistoricalSimulationResult) {
  const profile = whatIfProfile;
  render(
    <PreflightCard
      preflight={whatIfPreflight}
      status="ready"
      error=""
      historicalProfiles={[profile]}
      historicalProfilesStatus="ready"
      historicalProfilesError=""
      selectedHistoricalProfileId={profile.profile_id}
      onHistoricalProfileChange={() => {}}
      onRetryHistoricalProfiles={() => {}}
      runPlan={whatIfRunPlan(profile)}
      runPlanStatus="ready"
      runPlanError=""
      simulation={simulation}
      simulationStatus="completed"
      simulationError=""
      chartData={null}
      chartStatus="idle"
      chartError=""
      onStartHistoricalSimulation={() => {}}
      historicalSaveStatus="idle"
      historicalSaveError=""
      onSaveHistoricalRun={() => {}}
      onOpenSavedRuns={() => {}}
    />,
  );
}

describe("PreflightCard canlı-sonuç metrikleri (AA.7a-v1)", () => {
  it("6 türetilmiş metriği aynen dizer, null — olur", () => {
    renderCompletedCard(completedSimulation());
    expect(screen.getByText("SONUÇ ÖZETİ")).toBeInTheDocument();
    expect(screen.getByText("Win rate")).toBeInTheDocument();
    expect(screen.getByText("0.75")).toBeInTheDocument();
    expect(screen.getByText("0.125")).toBeInTheDocument();
    expect(screen.getByText("Kazanan deal")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(1);
  });

  it("metriksiz özet (fixed-slice) tüm metrikleri — düşürür", () => {
    const simulation = completedSimulation();
    const { win_count, win_rate, profit_factor, roi, safety_order_fill_count, safety_order_fill_rate, ...bare } = simulation.summary as NonNullable<typeof simulation.summary>;
    void win_count;
    void win_rate;
    void profit_factor;
    void roi;
    void safety_order_fill_count;
    void safety_order_fill_rate;
    renderCompletedCard({ ...simulation, summary: bare });
    expect(screen.getByText("Win rate")).toBeInTheDocument();
    expect(screen.queryByText("0.75")).not.toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(6);
  });
});
