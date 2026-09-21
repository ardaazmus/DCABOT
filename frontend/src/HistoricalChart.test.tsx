import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { HistoricalChart } from "./HistoricalChart";
import type {
  HistoricalChartData,
  HistoricalProfile,
  HistoricalSimulationResult,
} from "./datasetCatalog";

const profile: HistoricalProfile = {
  profile_id: "profile-1",
  profile_version: "1",
  label: "Demo",
  expected_dataset_id: "dataset-1",
  venue_filter_provenance: "historical_verified",
  historical_filter_claim: true,
  anchor_source: "explicit",
  simulation_model: "historical_ohlcv_v1",
};

const chartData: HistoricalChartData = {
  dataset_id: "dataset-1",
  artifact_sha256: "a".repeat(64),
  model_id: "historical_ohlcv_v1",
  period_start: "2025-01-01T00:00:00Z",
  period_end: "2025-01-01T02:00:00Z",
  processed_bar_count: 2,
  bars: [
    { bar_index: 1, open_time_us: 1, close_time_us: 2, open: "100", high: "102", low: "99", close: "101", base_volume: "10" },
    { bar_index: 2, open_time_us: 3, close_time_us: 4, open: "101", high: "103", low: "100", close: "102", base_volume: "20" },
  ],
};

function simulation(overrides: Partial<HistoricalSimulationResult> = {}): HistoricalSimulationResult {
  return {
    execution_id: "run-1",
    complete_execution: true,
    execution_status: "COMPLETED",
    application_code: null,
    persisted: false,
    dataset: {
      dataset_id: "dataset-1",
      artifact_sha256: "a".repeat(64),
      period_start: "2025-01-01T00:00:00Z",
      period_end: "2025-01-01T02:00:00Z",
      processed_bar_count: 2,
    },
    config: { schema_version: 1, config_hash: "b".repeat(64) },
    profile,
    assumptions: {
      model: "historical_ohlcv_v1",
      bar_visibility: "CLOSED_ONLY",
      intrabar_path: "NOT_INFERRED",
      max_actions_per_bar: 1,
      fee_model: "NONE",
      slippage_model: "NONE",
      funding: "NOT_MODELED",
      exchange_mark: "NOT_AVAILABLE",
      force_close_at_end: false,
    },
    actions: [],
    ambiguity: null,
    explanations: [],
    ...overrides,
  };
}

const action = {
  bar_index: 1,
  open_time_us: 1,
  role: "BASE",
  raw_reference: "bar-1",
  fill_price: "100",
  quantity: "1",
  fee: "0",
};

const secondAction = {
  ...action,
  bar_index: 2,
  open_time_us: 3,
  raw_reference: "bar-2",
};

function renderReady(simulationResult: HistoricalSimulationResult | null = null, data = chartData) {
  return render(
    <HistoricalChart status="ready" data={data} error="" simulation={simulationResult} />,
  );
}

describe("HistoricalChart", () => {
  it("idle durumunda grafik üretmez", () => {
    const { container } = render(<HistoricalChart status="idle" data={null} error="" simulation={null} />);

    expect(container.firstChild).toBeNull();
  });

  it("loading ve error durumlarını erişilebilir metinle gösterir", () => {
    const { rerender } = render(<HistoricalChart status="loading" data={null} error="" simulation={null} />);
    expect(screen.getByRole("status")).toHaveTextContent("Grafik verisi hazırlanıyor…");

    rerender(<HistoricalChart status="error" data={null} error="Grafik alınamadı" simulation={null} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Grafik alınamadı");
  });

  it("geçerli kapalı bar verisini grafik olarak gösterir", () => {
    renderReady();

    expect(screen.getByRole("img")).toBeInTheDocument();
    expect(screen.getAllByText(/2 kapalı bar/)).toHaveLength(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("bozuk OHLC verisini reddeder ve SVG çizmez", () => {
    renderReady(null, { ...chartData, bars: [{ ...chartData.bars[0], high: "98" }, chartData.bars[1]] });

    expect(screen.getByRole("alert")).toHaveTextContent("Tarihsel OHLC görünümü güvenli biçimde oluşturulamadı.");
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("dataset ile eşleşen tamamlanmış aksiyona marker ekler", () => {
    renderReady(simulation({ actions: [action] }));

    expect(document.querySelectorAll(".historical-chart-marker")).toHaveLength(1);
  });

  it("metadata uyuşmazlığında ekonomik marker üretmez", () => {
    renderReady(simulation({
      dataset: { ...simulation().dataset, dataset_id: "other-dataset" },
      actions: [action],
    }));

    expect(screen.getByRole("status")).toHaveTextContent("Aksiyon marker görünümü güvenli biçimde oluşturulamadı");
    expect(document.querySelectorAll(".historical-chart-marker")).toHaveLength(0);
  });

  it("belirsiz prefix sonucunda yalnızca doğrulanmış sınırı gösterir", () => {
    renderReady(simulation({
      complete_execution: false,
      execution_status: "INDETERMINATE",
      application_code: "AMBIGUOUS_OHLC_PATH",
      marker_authority: "PREFIX_BOUNDARY_ONLY",
      marker_kind: "INCOMPLETE_BOUNDARY",
      action_authority: {
        mode: "COMMITTED_PREFIX",
        economic_state_commit_scope: "PREFIX_ONLY",
        committed_through_bar_index: 1,
        committed_through_open_time_us: 2,
        ambiguity_bar_index: 2,
        contains_ambiguity_bar_actions: false,
        contains_post_ambiguity_actions: false,
        complete_history: false,
        economic_state_committed: true,
        committed_through_event_sequence: 1,
        action_count: 1,
      },
      ambiguity: { bar_index: 2, open_time_us: 3, code: "AMBIGUOUS_OHLC_PATH" },
      actions: [{ ...action, event_sequence: 1 }],
    }));

    expect(screen.getByText("INCOMPLETE · BAR 2")).toBeInTheDocument();
    expect(document.querySelectorAll(".historical-chart-marker")).toHaveLength(0);
  });

  it("marker tıklaması bar_index seçimini bildirir", () => {
    const onSelectBarIndex = vi.fn();
    render(
      <HistoricalChart status="ready" data={chartData} error="" simulation={simulation({ actions: [action] })} onSelectBarIndex={onSelectBarIndex} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" }));

    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });

  it("Enter tuşu marker seçimini bildirir", () => {
    const onSelectBarIndex = vi.fn();
    render(
      <HistoricalChart status="ready" data={chartData} error="" simulation={simulation({ actions: [action] })} onSelectBarIndex={onSelectBarIndex} />,
    );

    fireEvent.keyDown(screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" }), { key: "Enter" });

    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });

  it("Space tuşu marker seçimini bildirir, diğer tuşlar bildirmez", () => {
    const onSelectBarIndex = vi.fn();
    render(
      <HistoricalChart status="ready" data={chartData} error="" simulation={simulation({ actions: [action] })} onSelectBarIndex={onSelectBarIndex} />,
    );

    const marker = screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" });
    fireEvent.keyDown(marker, { key: "Tab" });
    expect(onSelectBarIndex).not.toHaveBeenCalled();

    fireEvent.keyDown(marker, { key: " " });
    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });

  it("selectedBarIndex prop'u yalnız eşleşen marker'ı vurgular", () => {
    const onSelectBarIndex = vi.fn();
    render(
      <HistoricalChart
        status="ready"
        data={chartData}
        error=""
        simulation={simulation({ actions: [action, secondAction] })}
        selectedBarIndex={2}
        onSelectBarIndex={onSelectBarIndex}
      />,
    );

    const markers = screen.getAllByRole("button");
    expect(markers).toHaveLength(2);
    expect(markers[0]).toHaveAttribute("aria-pressed", "false");
    expect(markers[0].classList.contains("historical-chart-marker-selected")).toBe(false);
    expect(markers[1]).toHaveAttribute("aria-pressed", "true");
    expect(markers[1].classList.contains("historical-chart-marker-selected")).toBe(true);
  });

  it("seçim handler'ı yoksa marker etkileşimli olmaz", () => {
    renderReady(simulation({ actions: [action] }));

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".historical-chart-marker")).toHaveLength(1);
  });

  it("taslak handler'ı yoksa taslak kontrolleri görünmez", () => {
    renderReady();

    expect(screen.queryByText("Taslak seviye")).not.toBeInTheDocument();
    expect(document.querySelector(".historical-chart-draft-line")).toBeNull();
  });

  it("taslak fiyat verilince seviye çizgisi ve klavye tutamacı görünür", () => {
    const onDraftPrice = vi.fn();
    render(
      <HistoricalChart status="ready" data={chartData} error="" simulation={null} draftPrice="101" draftVerdict="ACCEPTED: aralık içinde" onDraftPrice={onDraftPrice} />,
    );

    expect(document.querySelector(".historical-chart-draft-line")).not.toBeNull();
    expect(screen.getByRole("button", { name: /Taslak seviye 101/ })).toBeInTheDocument();
    expect(screen.getByText("ACCEPTED: aralık içinde")).toBeInTheDocument();
  });

  it("metin girişi kırpılmış değeri bildirir", () => {
    const onDraftPrice = vi.fn();
    render(
      <HistoricalChart status="ready" data={chartData} error="" simulation={null} onDraftPrice={onDraftPrice} />,
    );

    fireEvent.change(screen.getByPlaceholderText("örn. 30123.45"), { target: { value: "  101  " } });
    fireEvent.click(screen.getByRole("button", { name: "Değerlendir" }));

    expect(onDraftPrice).toHaveBeenCalledTimes(1);
    expect(onDraftPrice).toHaveBeenCalledWith("101");
  });

  it("tutamak ok tuşları yeni fiyatı bildirir", () => {
    const onDraftPrice = vi.fn();
    render(
      <HistoricalChart status="ready" data={chartData} error="" simulation={null} draftPrice="101" onDraftPrice={onDraftPrice} />,
    );

    fireEvent.keyDown(screen.getByRole("button", { name: /Taslak seviye 101/ }), { key: "ArrowUp" });

    expect(onDraftPrice).toHaveBeenCalledTimes(1);
    const next = onDraftPrice.mock.calls[0][0] as string;
    expect(next).not.toBe("101");
    expect(next).toMatch(/^\d+$/);
  });

  it("INCOMPLETE boundary çizgisi etkileşimli olmaz", () => {
    const onSelectBarIndex = vi.fn();
    render(
      <HistoricalChart
        status="ready"
        data={chartData}
        error=""
        simulation={simulation({
          complete_execution: false,
          execution_status: "INDETERMINATE",
          application_code: "AMBIGUOUS_OHLC_PATH",
          marker_authority: "PREFIX_BOUNDARY_ONLY",
          marker_kind: "INCOMPLETE_BOUNDARY",
          action_authority: {
            mode: "COMMITTED_PREFIX",
            economic_state_commit_scope: "PREFIX_ONLY",
            committed_through_bar_index: 1,
            committed_through_open_time_us: 2,
            ambiguity_bar_index: 2,
            contains_ambiguity_bar_actions: false,
            contains_post_ambiguity_actions: false,
            complete_history: false,
            economic_state_committed: true,
            committed_through_event_sequence: 1,
            action_count: 1,
          },
          ambiguity: { bar_index: 2, open_time_us: 3, code: "AMBIGUOUS_OHLC_PATH" },
          actions: [{ ...action, event_sequence: 1 }],
        })}
        onSelectBarIndex={onSelectBarIndex}
      />,
    );

    expect(screen.getByText("INCOMPLETE · BAR 2")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
