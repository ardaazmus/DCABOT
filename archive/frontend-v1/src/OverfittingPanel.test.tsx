import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  isOverfittingResponse,
  OverfittingPanel,
  type OverfittingResult,
} from "./OverfittingPanel";

const result: OverfittingResult = {
  sampler: "grid",
  seed: 0,
  suggested_count: 4,
  trial_count: 4,
  succeeded_count: 3,
  skipped_count: 1,
  skipped: [{ recipe_id: "r4", code: "INVALID" }],
  return_series_length: 60,
  block_count: 4,
  pbo: "0.31",
  dsr_by_trial: { r1: "1.1", r2: null, r3: "0.4" },
  dataset_id: "d1",
  profile_id: "p1",
};

function renderPanel(resultValue: OverfittingResult | null, onRun: (payload: never) => void = () => {}) {
  return render(
    <OverfittingPanel datasetId="d1" profileId="p1" busy={false} error="" result={resultValue} onRun={onRun as never} />,
  );
}

describe("AA.7c overfitting sekmesi", () => {
  it("guard sözleşmesi", () => {
    expect(isOverfittingResponse({ data: result })).toBe(true);
    expect(isOverfittingResponse({ data: { ...result, pbo: 0.3 } })).toBe(false);
    expect(isOverfittingResponse({ data: { ...result, dsr_by_trial: { r1: 1 } } })).toBe(false);
    expect(isOverfittingResponse({ data: { ...result, skipped: [{ recipe_id: "r4" }] } })).toBe(false);
    expect(isOverfittingResponse({})).toBe(false);
  });

  it("sonuç verbatim dizilir, null tire olur", () => {
    renderPanel(result);
    expect(screen.getByText("0.31")).toBeInTheDocument();
    expect(screen.getByText("1.1")).toBeInTheDocument();
    expect(screen.getByText("r4 (INVALID)")).toBeInTheDocument();
    expect(screen.getByText("4 / 4 / 3 / 1")).toBeInTheDocument();
  });

  it("kanonik form block_count ile aynen POST'lar", () => {
    const onRun = vi.fn();
    renderPanel(null, onRun);
    fireEvent.change(screen.getByLabelText("TP min"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("TP max"), { target: { value: "0.05" } });
    fireEvent.click(screen.getByRole("button", { name: "Overfitting değerlendirmesi başlat" }));
    expect(onRun).toHaveBeenCalledTimes(1);
    expect(onRun).toHaveBeenCalledWith({
      space: { take_profit: { kind: "float", low: 0.01, high: 0.05 } },
      sampler: "grid",
      max_trials: 4,
      seed: 0,
      block_count: 4,
    });
  });

  it("tek blok sayısı POST'lamaz", () => {
    const onRun = vi.fn();
    renderPanel(null, onRun);
    fireEvent.change(screen.getByLabelText("TP min"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("TP max"), { target: { value: "0.05" } });
    fireEvent.change(screen.getByLabelText("Blok sayısı (çift, ≥2)"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Overfitting değerlendirmesi başlat" }));
    expect(onRun).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("çift");
  });
});
