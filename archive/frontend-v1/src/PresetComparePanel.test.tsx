import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  PresetComparePanel,
  isPresetCompareResponse,
  type PresetCompareResult,
  type PresetCompareSide,
} from "./PresetComparePanel";
import type { TemplateMeta } from "./TemplatePanel";

const TEMPLATES: TemplateMeta[] = [
  { template_id: "tpl-a", payload_sha256: "a".repeat(64), declared_capabilities: ["dca", "spot"] },
  { template_id: "tpl-b", payload_sha256: "b".repeat(64), declared_capabilities: ["dca"] },
];

const SIDE_A: PresetCompareSide = {
  binding_id: "bind-a",
  profile_id: "paper",
  config_hash: "c".repeat(64),
  execution_status: "COMPLETED",
  position_status: "CLOSED",
  realized_net_after_all_costs: "12.5",
  peak_equity: "1012",
  max_drawdown: "30",
  deal_count: 5,
  completed_deal_count: 5,
  deal_pnls: ["5", "-1"],
  win_count: 4,
  win_rate: "0.8",
  profit_factor: "3.1",
  roi: "0.125",
  safety_order_fill_count: 6,
  safety_order_fill_rate: "0.6",
};

const RESULT: PresetCompareResult = {
  dataset_id: "ds-1",
  a: SIDE_A,
  b: { ...SIDE_A, binding_id: "bind-b", realized_net_after_all_costs: "-2", win_rate: null, deal_pnls: [] },
};

describe("PresetComparePanel", () => {
  it("AA.13a: seçim-yoksa dürüst-boş, düğme kapalı", () => {
    render(
      <PresetComparePanel datasetId={null} artifactSha256={null} templates={TEMPLATES} busy={false} error="" result={null} onRun={vi.fn()} />,
    );
    expect(screen.getByText("Dataset seçilmeden karşılaştırma koşulamaz — katalogdan seçin.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Karşılaştır" })).toBeDisabled();
  });

  it("AA.13a: form-doğrulama (şablon-şart, aynı-taraf, profil-şart)", () => {
    const onRun = vi.fn();
    render(
      <PresetComparePanel datasetId="ds-1" artifactSha256={"d".repeat(64)} templates={TEMPLATES} busy={false} error="" result={null} onRun={onRun} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Karşılaştır" }));
    expect(screen.getByRole("alert")).toHaveTextContent("İki taraf için de şablon seçin");
    fireEvent.change(screen.getByLabelText("A tarafı şablon"), { target: { value: "tpl-a" } });
    fireEvent.change(screen.getByLabelText("B tarafı şablon"), { target: { value: "tpl-a" } });
    fireEvent.click(screen.getByRole("button", { name: "Karşılaştır" }));
    expect(screen.getByRole("alert")).toHaveTextContent("aynı şablon+profil");
    fireEvent.change(screen.getByLabelText("B tarafı profil"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("B tarafı şablon"), { target: { value: "tpl-b" } });
    fireEvent.click(screen.getByRole("button", { name: "Karşılaştır" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Profil kimliği boş olamaz");
    expect(onRun).not.toHaveBeenCalled();
  });

  it("AA.13a: geçerli form gövdeyi kurar (caps-otomatik, onay-ayrı)", () => {
    const onRun = vi.fn();
    render(
      <PresetComparePanel datasetId="ds-1" artifactSha256={"d".repeat(64)} templates={TEMPLATES} busy={false} error="" result={null} onRun={onRun} />,
    );
    fireEvent.change(screen.getByLabelText("A tarafı şablon"), { target: { value: "tpl-a" } });
    fireEvent.change(screen.getByLabelText("B tarafı şablon"), { target: { value: "tpl-b" } });
    fireEvent.click(screen.getByLabelText("A tarafı bağlamayı onaylıyorum"));
    fireEvent.click(screen.getByRole("button", { name: "Karşılaştır" }));
    expect(onRun).toHaveBeenCalledTimes(1);
    expect(onRun).toHaveBeenCalledWith({
      a: { template_id: "tpl-a", profile_id: "paper", allowed_capabilities: ["dca", "spot"], approval: "APPROVED" },
      b: { template_id: "tpl-b", profile_id: "paper", allowed_capabilities: ["dca"], approval: "PENDING" },
    });
  });

  it("AA.13a: sonuçlar yan-yana dizilir, fark-hesabı yok", () => {
    render(
      <PresetComparePanel datasetId="ds-1" artifactSha256={"d".repeat(64)} templates={TEMPLATES} busy={false} error="" result={RESULT} onRun={vi.fn()} />,
    );
    const tables = screen.getAllByRole("table");
    const metricTable = tables[0];
    expect(within(metricTable).getByText("Win rate")).toBeInTheDocument();
    expect(within(metricTable).getByText("12.5")).toBeInTheDocument();
    expect(within(metricTable).getByText("-2")).toBeInTheDocument();
    expect(within(metricTable).getByText("0.8")).toBeInTheDocument();
    expect(screen.getByText("B: tamamlanan deal yok.")).toBeInTheDocument();
    expect(within(metricTable).queryByText(/fark/i)).not.toBeInTheDocument();
  });

  it("AA.13a: meşgul + hata durumları", () => {
    const { unmount } = render(
      <PresetComparePanel datasetId="ds-1" artifactSha256={"d".repeat(64)} templates={TEMPLATES} busy={true} error="" result={null} onRun={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: "Karşılaştırılıyor…" })).toBeDisabled();
    unmount();
    render(
      <PresetComparePanel datasetId="ds-1" artifactSha256={"d".repeat(64)} templates={TEMPLATES} busy={false} error="uç reddetti" result={null} onRun={vi.fn()} />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("uç reddetti");
  });

  it("AA.13a: guard sözleşmesi", () => {
    expect(isPresetCompareResponse({ data: RESULT })).toBe(true);
    expect(isPresetCompareResponse({ data: { ...RESULT, b: { ...SIDE_A, win_rate: 0.8 } } })).toBe(false);
    expect(isPresetCompareResponse({ data: { ...RESULT, a: { ...SIDE_A, deal_pnls: ["1", 2] } } })).toBe(false);
    expect(isPresetCompareResponse({ data: { ...RESULT, dataset_id: 7 } })).toBe(false);
    expect(isPresetCompareResponse({})).toBe(false);
  });
});
