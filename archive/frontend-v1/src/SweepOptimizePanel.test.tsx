import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  SweepOptimizePanel,
  isSweepOptimizeResponse,
  type SweepOptimizeResult,
} from "./SweepOptimizePanel";

const result: SweepOptimizeResult = {
  sampler: "grid",
  seed: 0,
  suggested_count: 4,
  trial_count: 2,
  trials: [
    {
      recipe_id: "trial-1",
      overrides: { take_profit: "0.05", deviation: "0.2" },
      execution_status: "COMPLETED",
      realized_net_after_all_costs: "12.5",
      config_hash: "a".repeat(64),
      win_rate: "0.8",
      profit_factor: "3.1",
      roi: "0.125",
      safety_order_fill_rate: "0.5",
    },
    {
      recipe_id: "trial-2",
      overrides: { take_profit: "0.01", deviation: "0.05", safety_count: 3 },
      execution_status: "COMPLETED",
      realized_net_after_all_costs: "3.25",
      config_hash: "b".repeat(64),
      win_rate: null,
      profit_factor: null,
      roi: "0.03",
      safety_order_fill_rate: null,
    },
  ],
  skipped_count: 1,
  skipped: [{ recipe_id: "trial-3", overrides: { deviation: "1.5" }, code: "SWEEP_TASK_FAILED" }],
  best_recipe_id: "trial-1",
  best_overrides: { take_profit: "0.05", deviation: "0.2" },
  best_metric: "12.5",
  dataset_id: "ds-1",
  profile_id: "pf-1",
};

describe("SweepOptimizePanel", () => {
  it("AA.7b: seçim-yoksa dürüst-boş, düğme kapalı", () => {
    render(
      <SweepOptimizePanel datasetId={null} profileId="pf-1" busy={false} error="" result={null} onRun={vi.fn()} onFillWizard={vi.fn()} />,
    );
    expect(screen.getByText("Dataset + profil seçilmeden tarama koşulamaz — katalogdan seçin.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Optimizasyonu başlat" })).toBeDisabled();
  });

  it("AA.7b: aralık-doğrulama (boş-hepsi, bozuk-sayı, ters-aralık, deneme-sınırı)", () => {
    const onRun = vi.fn();
    render(
      <SweepOptimizePanel datasetId="ds-1" profileId="pf-1" busy={false} error="" result={null} onRun={onRun} onFillWizard={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Optimizasyonu başlat" }));
    expect(screen.getByRole("alert")).toHaveTextContent("En az bir parametre aralığı girin");
    expect(onRun).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("TP min"), { target: { value: "abc" } });
    fireEvent.change(screen.getByLabelText("TP max"), { target: { value: "0.05" } });
    fireEvent.click(screen.getByRole("button", { name: "Optimizasyonu başlat" }));
    expect(screen.getByRole("alert")).toHaveTextContent("sayı olmalıdır");
    fireEvent.change(screen.getByLabelText("TP min"), { target: { value: "0.05" } });
    fireEvent.change(screen.getByLabelText("TP max"), { target: { value: "0.01" } });
    fireEvent.click(screen.getByRole("button", { name: "Optimizasyonu başlat" }));
    expect(screen.getByRole("alert")).toHaveTextContent("min<max");
    fireEvent.change(screen.getByLabelText("TP min"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("TP max"), { target: { value: "0.05" } });
    fireEvent.change(screen.getByLabelText("Deneme sayısı (1-32)"), { target: { value: "99" } });
    fireEvent.click(screen.getByRole("button", { name: "Optimizasyonu başlat" }));
    expect(screen.getByRole("alert")).toHaveTextContent("1-32 arası");
    expect(onRun).not.toHaveBeenCalled();
  });

  it("AA.7b: geçerli form uzay-gövdesini kurar (boş-satır hariç, int-ayrımı)", () => {
    const onRun = vi.fn();
    render(
      <SweepOptimizePanel datasetId="ds-1" profileId="pf-1" busy={false} error="" result={null} onRun={onRun} onFillWizard={vi.fn()} />,
    );
    fireEvent.change(screen.getByLabelText("TP min"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("TP max"), { target: { value: "0.05" } });
    fireEvent.change(screen.getByLabelText("SO adedi min"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("SO adedi max"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Tarama tipi"), { target: { value: "random" } });
    fireEvent.change(screen.getByLabelText("Deneme sayısı (1-32)"), { target: { value: "12" } });
    fireEvent.change(screen.getByLabelText("Seed (rastgele için)"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "Optimizasyonu başlat" }));
    expect(onRun).toHaveBeenCalledTimes(1);
    expect(onRun).toHaveBeenCalledWith({
      space: {
        take_profit: { kind: "float", low: 0.01, high: 0.05 },
        safety_count: { kind: "int", low: 1, high: 3 },
      },
      sampler: "random",
      max_trials: 12,
      seed: 7,
    });
  });

  it("AA.7b: sonuç-tablosu + en-iyi + atlananlar + sihirbaza-doldur", () => {
    const onFillWizard = vi.fn();
    render(
      <SweepOptimizePanel datasetId="ds-1" profileId="pf-1" busy={false} error="" result={result} onRun={vi.fn()} onFillWizard={onFillWizard} />,
    );
    expect(screen.getByText("2 deneme")).toBeInTheDocument();
    expect(screen.getAllByText("take_profit=0.05, deviation=0.2")).toHaveLength(2);
    expect(screen.getByText("SWEEP_TASK_FAILED")).toBeInTheDocument();
    expect(screen.getByText("★1")).toBeInTheDocument();
    const tables = screen.getAllByRole("table");
    const trialTable = tables[1];
    expect(within(trialTable).getByText("12.5")).toBeInTheDocument();
    expect(within(trialTable).getByText("Win rate")).toBeInTheDocument();
    expect(within(trialTable).getByText("0.8")).toBeInTheDocument();
    expect(within(trialTable).getByText("3.1")).toBeInTheDocument();
    expect(within(trialTable).getAllByText("—").length).toBeGreaterThanOrEqual(3);
    fireEvent.click(screen.getByRole("button", { name: "En iyiyi sihirbaza doldur" }));
    expect(onFillWizard).toHaveBeenCalledWith({ take_profit: "0.05", deviation: "0.2" });
    const fillButtons = within(trialTable).getAllByRole("button", { name: "Doldur" });
    fireEvent.click(fillButtons[1]);
    expect(onFillWizard).toHaveBeenCalledWith({ take_profit: "0.01", deviation: "0.05", safety_count: 3 });
  });

  it("AA.7b: meşgul + hata durumları", () => {
    const { unmount } = render(
      <SweepOptimizePanel datasetId="ds-1" profileId="pf-1" busy={true} error="" result={null} onRun={vi.fn()} onFillWizard={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: "Taranıyor…" })).toBeDisabled();
    unmount();
    render(
      <SweepOptimizePanel datasetId="ds-1" profileId="pf-1" busy={false} error="sunucu reddetti" result={null} onRun={vi.fn()} onFillWizard={vi.fn()} />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("sunucu reddetti");
  });

  it("AA.7b: guard sözleşmesi", () => {
    expect(isSweepOptimizeResponse({ data: result })).toBe(true);
    expect(isSweepOptimizeResponse({ data: { ...result, trials: [{ ...result.trials[0], win_rate: 0.8 }] } })).toBe(false);
    expect(isSweepOptimizeResponse({ data: { ...result, trials: [{ ...result.trials[0], roi: undefined }] } })).toBe(false);
    expect(isSweepOptimizeResponse({ data: { ...result, trials: [{ ...result.trials[0], realized_net_after_all_costs: 12.5 }] } })).toBe(false);
    expect(isSweepOptimizeResponse({ data: { ...result, trials: [{ ...result.trials[0], overrides: { take_profit: 0.05 } }] } })).toBe(false);
    expect(isSweepOptimizeResponse({ data: { ...result, best_overrides: "yok" } })).toBe(false);
    expect(isSweepOptimizeResponse({ data: { ...result, seed: "0" } })).toBe(false);
    expect(isSweepOptimizeResponse({})).toBe(false);
  });
});
