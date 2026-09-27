import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  CorrelationPanel,
  isCorrelationGateResponse,
  type CorrelationGateResult,
} from "./CorrelationPanel";
import type { DatasetSummary } from "./datasetCatalog";

const DATASETS: DatasetSummary[] = [
  { dataset_id: "ds-x", dataset_type: "kline_csv_zip", instrument: "BTCUSDT", interval: "1h", period_start: "a", period_end: "b", status: "VERIFIED", artifact: { sha256: "x".repeat(64), byte_size: 10 } },
  { dataset_id: "ds-y", dataset_type: "kline_csv_zip", instrument: "ETHUSDT", interval: "1h", period_start: "a", period_end: "b", status: "VERIFIED", artifact: { sha256: "y".repeat(64), byte_size: 10 } },
];

const RESULT: CorrelationGateResult = { decision: "DENY", reason: "BREACH", worst_window: 20 };

function baseProps(overrides: Record<string, unknown> = {}) {
  return {
    datasets: DATASETS,
    closesX: ["100", "101", "102", "103"],
    closesY: ["50", "51", "52", "53"],
    labelX: "ds-x",
    labelY: "ds-y",
    seriesBusy: false,
    seriesError: "",
    busy: false,
    error: "",
    result: null as CorrelationGateResult | null,
    onSelectSeries: vi.fn(),
    onRun: vi.fn(),
    ...overrides,
  };
}

describe("CorrelationPanel", () => {
  it("AA.10b: dataset-seçimi seri-yüklemeyi tetikler", () => {
    const onSelectSeries = vi.fn();
    render(<CorrelationPanel {...baseProps({ closesX: [], closesY: [], labelX: "", labelY: "", onSelectSeries })} />);
    expect(screen.getAllByText("seri yüklenmedi")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Kapıyı değerlendir" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("X serisi dataseti"), { target: { value: "ds-x" } });
    expect(onSelectSeries).toHaveBeenCalledWith("x", "ds-x");
  });

  it("AA.10b: form-doğrulama (bar-sayısı, yetersiz-seri, pencere, eşik)", () => {
    const onRun = vi.fn();
    render(<CorrelationPanel {...baseProps({ onRun })} />);
    fireEvent.change(screen.getByLabelText("Bar sayısı — sondan (2-5000)"), { target: { value: "9" } });
    fireEvent.click(screen.getByRole("button", { name: "Kapıyı değerlendir" }));
    expect(screen.getByRole("alert")).toHaveTextContent("9 bar yok");
    fireEvent.change(screen.getByLabelText("Bar sayısı — sondan (2-5000)"), { target: { value: "4" } });
    fireEvent.change(screen.getByLabelText("Pencereler (virgüllü, ≥2)"), { target: { value: "1,20" } });
    fireEvent.click(screen.getByRole("button", { name: "Kapıyı değerlendir" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Pencereler");
    fireEvent.change(screen.getByLabelText("Pencereler (virgüllü, ≥2)"), { target: { value: "20,60" } });
    fireEvent.change(screen.getByLabelText("Eşik payda"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Kapıyı değerlendir" }));
    expect(screen.getByRole("alert")).toHaveTextContent("pozitif tamsayı");
    expect(onRun).not.toHaveBeenCalled();
  });

  it("AA.10b: geçerli form son-N gövdeyi kurar", () => {
    const onRun = vi.fn();
    render(<CorrelationPanel {...baseProps({ onRun })} />);
    fireEvent.change(screen.getByLabelText("Bar sayısı — sondan (2-5000)"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Kapıyı değerlendir" }));
    expect(onRun).toHaveBeenCalledTimes(1);
    expect(onRun).toHaveBeenCalledWith({
      prices_x: [101, 102, 103],
      prices_y: [51, 52, 53],
      windows: [20, 60],
      threshold_numerator: 8,
      threshold_denominator: 10,
      scale: 1000000,
    });
  });

  it("AA.10b: sonuç kararı + gerekçeyi dizer", () => {
    render(<CorrelationPanel {...baseProps({ result: RESULT })} />);
    expect(screen.getAllByText("DENY")).toHaveLength(2);
    expect(screen.getByText("BREACH")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  it("AA.10b: meşgul + hata durumları", () => {
    const { unmount } = render(<CorrelationPanel {...baseProps({ busy: true })} />);
    expect(screen.getByRole("button", { name: "Değerlendiriliyor…" })).toBeDisabled();
    unmount();
    render(<CorrelationPanel {...baseProps({ error: "uç reddetti", seriesError: "seri yok" })} />);
    expect(screen.getAllByRole("alert").length).toBe(2);
  });

  it("AA.10b: guard sözleşmesi", () => {
    expect(isCorrelationGateResponse({ data: RESULT })).toBe(true);
    expect(isCorrelationGateResponse({ data: { ...RESULT, worst_window: null } })).toBe(true);
    expect(isCorrelationGateResponse({ data: { ...RESULT, decision: 7 } })).toBe(false);
    expect(isCorrelationGateResponse({ data: { ...RESULT, worst_window: "20" } })).toBe(false);
    expect(isCorrelationGateResponse({})).toBe(false);
  });
});
