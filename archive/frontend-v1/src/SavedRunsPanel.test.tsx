import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { SavedRunDetail } from "./savedRuns";
import { SavedRunsPanel } from "./SavedRunsPanel";

function makeDetail(overrides: Partial<SavedRunDetail> = {}): SavedRunDetail {
  return {
    run_id: "11111111-1111-1111-1111-111111111111",
    created_at: "2026-09-01T00:00:00+00:00",
    storage_state: "STORED",
    execution_status: "COMPLETED",
    dataset: { dataset_id: "ds-1", artifact_sha256: "a".repeat(64) },
    input_snapshot: {},
    config: { config_hash: "c".repeat(64) },
    instrument_risk: {},
    execution: {},
    result_snapshot: { summary: { realized_net_after_all_costs: "12.5" } },
    result_sha256: "r".repeat(64),
    record_sha256: "s".repeat(64),
    ...overrides,
  };
}

const PERFORMANCE_SUMMARY = {
  realized_net_after_all_costs: "12.5",
  win_count: 3,
  win_rate: "0.75",
  profit_factor: "2.5",
  roi: "0.125",
  safety_order_fill_count: 4,
  safety_order_fill_rate: "0.5",
  deal_pnls: ["5", "-1", "8.5"],
};

function renderDetail(detail: SavedRunDetail) {
  return render(
    <SavedRunsPanel
      view="detail"
      runs={[]}
      listStatus="ready"
      listError=""
      detail={detail}
      detailStatus="ready"
      detailError=""
      onOpenDetail={vi.fn()}
      onBackToList={vi.fn()}
      compareSelection={[]}
      onToggleCompareSelection={vi.fn()}
      onOpenCompare={vi.fn()}
      compareDetails={null}
      compareStatus="idle"
      compareError=""
      onExportRun={vi.fn()}
      exportStatus="idle"
      exportError=""
    />,
  );
}

function renderCompare(first: SavedRunDetail, second: SavedRunDetail) {
  render(
    <SavedRunsPanel
      view="compare"
      runs={[]}
      listStatus="ready"
      listError=""
      detail={null}
      detailStatus="idle"
      detailError=""
      onOpenDetail={vi.fn()}
      onBackToList={vi.fn()}
      compareSelection={[]}
      onToggleCompareSelection={vi.fn()}
      onOpenCompare={vi.fn()}
      compareDetails={[first, second]}
      compareStatus="ready"
      compareError=""
      onExportRun={vi.fn()}
      exportStatus="idle"
      exportError=""
    />,
  );
}

describe("SavedRunsPanel karşılaştırma güvenlikleri (B.4)", () => {
  it("aynı dataset + config hash satırlarını gösterir, uyarı çıkarmaz", () => {
    const first = makeDetail();
    const second = makeDetail({
      run_id: "22222222-2222-2222-2222-222222222222",
      config: { config_hash: "d".repeat(64) },
      result_sha256: "q".repeat(64),
    });
    renderCompare(first, second);
    expect(screen.getAllByText("ds-1 · aaaaaaaa…")).toHaveLength(2);
    expect(screen.getByText("cccccccc…")).toBeInTheDocument();
    expect(screen.getByText("dddddddd…")).toBeInTheDocument();
    expect(screen.queryByText("! Farklı dataset")).not.toBeInTheDocument();
    expect(screen.queryByText("! Dataset bilinmiyor")).not.toBeInTheDocument();
  });

  it("farklı datasette yanıltıcılık uyarısı çıkar", () => {
    const first = makeDetail();
    const second = makeDetail({
      run_id: "22222222-2222-2222-2222-222222222222",
      dataset: { dataset_id: "ds-2", artifact_sha256: "b".repeat(64) },
      result_sha256: "q".repeat(64),
    });
    renderCompare(first, second);
    expect(screen.getByText("! Farklı dataset")).toBeInTheDocument();
    expect(screen.getByText("ds-2 · bbbbbbbb…")).toBeInTheDocument();
  });

  it("dataset kimliği okunamazsa dürüst not çıkar", () => {
    const first = makeDetail();
    const second = makeDetail({ run_id: "22222222-2222-2222-2222-222222222222", dataset: {}, result_sha256: "q".repeat(64) });
    renderCompare(first, second);
    expect(screen.getByText("! Dataset bilinmiyor")).toBeInTheDocument();
  });
});

describe("SavedRunsPanel performans metrikleri (AA.7a-v1)", () => {
  it("karşılaştırma 6 satırı iki sütunda da dizer, null/eski-kayıt — olur", () => {
    const first = makeDetail({ result_snapshot: { summary: PERFORMANCE_SUMMARY } });
    const second = makeDetail({
      run_id: "22222222-2222-2222-2222-222222222222",
      result_sha256: "q".repeat(64),
      result_snapshot: {
        summary: {
          realized_net_after_all_costs: "-2",
          win_count: 0,
          win_rate: null,
          profit_factor: null,
          roi: "-0.02",
        },
      },
    });
    renderCompare(first, second);
    expect(screen.getByText("Win rate")).toBeInTheDocument();
    expect(screen.getByText("Profit factor")).toBeInTheDocument();
    expect(screen.getByText("SO dolum oranı")).toBeInTheDocument();
    expect(screen.getByText("0.75")).toBeInTheDocument();
    expect(screen.getByText("2.5")).toBeInTheDocument();
    expect(screen.getByText("-0.02")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(4);
  });

  it("detay metrik kartı + EXACT rozeti + deal tablosunu dizer", () => {
    renderDetail(makeDetail({ result_snapshot: { summary: PERFORMANCE_SUMMARY } }));
    expect(screen.getByText("PERFORMANS METRİKLERİ")).toBeInTheDocument();
    expect(screen.getByText("EXACT")).toBeInTheDocument();
    expect(screen.getByText("Win rate (kazanan/tamamlanan)")).toBeInTheDocument();
    expect(screen.getByText("0.75")).toBeInTheDocument();
    expect(screen.getByText("DEAL PNL’LERİ (KAPANIŞ SIRASI)")).toBeInTheDocument();
    expect(screen.getByText("8.5")).toBeInTheDocument();
    expect(screen.queryByText(/deal gizli/)).not.toBeInTheDocument();
  });

  it("detay 60-deal sınırında kırpar, dejenere/bozuk durumlarda dürüst-not verir", () => {
    const many = Array.from({ length: 65 }, (_, index) => String(index + 1));
    const { unmount } = renderDetail(
      makeDetail({ result_snapshot: { summary: { ...PERFORMANCE_SUMMARY, deal_pnls: many } } }),
    );
    expect(screen.getByText("Önceki 5 deal gizli — son 60 gösteriliyor.")).toBeInTheDocument();
    expect(screen.getAllByText("65")).toHaveLength(2);
    expect(screen.queryByText("Tamamlanan deal yok — açık-kalan deal net’e girmez.")).not.toBeInTheDocument();
    unmount();
    renderDetail(makeDetail({ result_snapshot: { summary: { ...PERFORMANCE_SUMMARY, deal_pnls: [] } } }));
    expect(screen.getByText("Tamamlanan deal yok — açık-kalan deal net’e girmez.")).toBeInTheDocument();
  });

  it("detay özet/bozuk-liste yokluğunda bölümü dürüstçe düşürür", () => {
    const { unmount } = renderDetail(makeDetail({ result_snapshot: {} }));
    expect(screen.getByText("Kayıt özeti okunamadı — metrikler yok.")).toBeInTheDocument();
    expect(screen.queryByText("DEAL PNL’LERİ (KAPANIŞ SIRASI)")).not.toBeInTheDocument();
    unmount();
    renderDetail(makeDetail({ result_snapshot: { summary: { ...PERFORMANCE_SUMMARY, deal_pnls: [7] } } }));
    expect(screen.getByText("Deal listesi okunamadı — kayıt bozuk olabilir.")).toBeInTheDocument();
  });
});

describe("SavedRunsPanel equity eğrisi + Sharpe (AA.7)", () => {
  it("detay eğri-grafiği + Sharpe satırını dizer, yoksa dürüst-boş düşürür", () => {
    const { unmount } = renderDetail(
      makeDetail({ result_snapshot: { summary: { ...PERFORMANCE_SUMMARY, equity_curve: ["100", "101.5", "99"], sharpe_ratio: "1.2" } } }),
    );
    expect(screen.getByText("EQUITY EĞRİSİ")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Equity eğrisi/ })).toBeInTheDocument();
    expect(screen.getByText("Sharpe oranı")).toBeInTheDocument();
    expect(screen.getByText("1.2")).toBeInTheDocument();
    unmount();
    renderDetail(makeDetail({ result_snapshot: { summary: PERFORMANCE_SUMMARY } }));
    expect(screen.getByText("Equity eğrisi yok (eski kayıt).")).toBeInTheDocument();
  });
});
