import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { DatasetSummary } from "./datasetCatalog";
import type { DashboardView } from "./DashboardPanel";
import type { CanaryStatusView } from "./RiskPanel";
import { isCapabilitiesView, SystemStatusCard, type CapabilitiesView, type SystemApiStatus } from "./SystemStatusCard";

const datasets: DatasetSummary[] = [
  { dataset_id: "ds-1", dataset_type: "kline_csv_zip", instrument: "BTCUSDT", interval: "1h", period_start: "2026-01-01", period_end: "2026-01-31", status: "VERIFIED", artifact: { sha256: "a", byte_size: 10 } },
  { dataset_id: "ds-2", dataset_type: "kline_csv_zip", instrument: "ETHUSDT", interval: "1h", period_start: "2026-01-01", period_end: "2026-01-31", status: "VERIFIED", artifact: { sha256: "b", byte_size: 10 } },
  { dataset_id: "ds-3", dataset_type: "kline_csv_zip", instrument: "SOLUSDT", interval: "1h", period_start: "2026-01-01", period_end: "2026-01-31", status: "MISSING", artifact: null },
];

const canary: CanaryStatusView = {
  verdict: "CANARY_NOGO",
  reasons: ["SPEC_NOT_ACTIVE"],
  kill_switch_engaged: false,
  approval_present: false,
  spec_status: "MISSING",
  paper_fill_count: 0,
  observed_at: "2026-09-22T00:00:00Z",
};

function cardProps(overrides: {
  apiStatus?: SystemApiStatus;
  apiError?: string;
  datasets?: DatasetSummary[];
  datasetCatalogReady?: boolean;
  selectedDatasetId?: string | null;
  canary?: CanaryStatusView | null;
  canaryBusy?: boolean;
  canaryError?: string;
  onRefreshCanary?: () => void;
  dashboard?: DashboardView | null;
  dashboardBusy?: boolean;
  dashboardError?: string;
  capabilities?: CapabilitiesView | null;
  capabilitiesBusy?: boolean;
  capabilitiesError?: string;
} = {}) {
  return {
    apiStatus: "ready" as SystemApiStatus,
    apiError: "",
    datasets,
    datasetCatalogReady: true,
    selectedDatasetId: "ds-1",
    canary,
    canaryBusy: false,
    canaryError: "",
    onRefreshCanary: vi.fn(),
    dashboard: null,
    dashboardBusy: false,
    dashboardError: "",
    capabilities: null,
    capabilitiesBusy: false,
    capabilitiesError: "",
    ...overrides,
  };
}

const dashboard = {
  paper: { sessions: 2, total_cash: "1000", positions: 1, open_orders: 0 },
  bots: { bots: 3, bound_sessions: 2 },
  deals: { deals: 5, by_status: { EMPTY: 5 } },
  backups: { backups: 1 },
};

const capabilities: CapabilitiesView = {
  mode: "offline",
  data_mode: "HISTORY_LOCAL",
  execution_mode: "SIMULATED",
  trading_enabled: false,
  features: { preview: true, historical_import: false, testnet: false },
};

describe("SystemStatusCard (AA.1)", () => {
  it("üç mini-kartı gerçek değerlerle gösterir", () => {
    render(<SystemStatusCard {...cardProps()} />);

    expect(screen.getByRole("heading", { name: "Durum & Veri Kaynağı" })).toBeInTheDocument();
    expect(screen.getByText("✓ Bağlı")).toBeInTheDocument();
    expect(screen.getByText("3 dataset · 2 doğrulandı")).toBeInTheDocument();
    expect(screen.getByText("Seçili: ds-1")).toBeInTheDocument();
    expect(screen.getByText("Kill-switch: kapalı")).toBeInTheDocument();
    expect(screen.getByText("CANARY_NOGO")).toBeInTheDocument();
  });

  it("API hatasını ve katalog beklemesini dürüst gösterir", () => {
    render(<SystemStatusCard {...cardProps({ apiStatus: "error", apiError: "Özet isteği başarısız.", datasetCatalogReady: false, datasets: [] })} />);

    expect(screen.getByText("! Bağlantı yok")).toBeInTheDocument();
    expect(screen.getByText("Özet isteği başarısız.")).toBeInTheDocument();
    expect(screen.getByText("○ Katalog bekleniyor")).toBeInTheDocument();
  });

  it("seçili dataset yoksa bunu yazar, uydurmaz", () => {
    render(<SystemStatusCard {...cardProps({ selectedDatasetId: null })} />);

    expect(screen.getByText("Seçili dataset yok.")).toBeInTheDocument();
  });

  it("canary okunmadıysa Yenile düğmesi handler çağırır", () => {
    const onRefreshCanary = vi.fn();
    render(<SystemStatusCard {...cardProps({ canary: null, onRefreshCanary })} />);

    expect(screen.getByText("○ Durum henüz okunmadı")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yenile" }));
    expect(onRefreshCanary).toHaveBeenCalledTimes(1);
  });

  it("kill-switch açıksa devrede rozeti gösterir", () => {
    render(<SystemStatusCard {...cardProps({ canary: { ...canary, kill_switch_engaged: true, reasons: ["KILL_SWITCH_ENGAGED"] } })} />);

    expect(screen.getByText("Kill-switch: AÇIK (devrede)")).toBeInTheDocument();
  });

  it("canary hatasını gösterir ve yeniden denemeye izin verir", () => {
    const onRefreshCanary = vi.fn();
    render(<SystemStatusCard {...cardProps({ canary: null, canaryError: "Canary durumu alınamadı.", onRefreshCanary })} />);

    expect(screen.getByText("! Okunamadı")).toBeInTheDocument();
    expect(screen.getByText("Canary durumu alınamadı.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yenile" }));
    expect(onRefreshCanary).toHaveBeenCalledTimes(1);
  });

  it("capabilities guard sözleşmesi", () => {
    expect(isCapabilitiesView(capabilities)).toBe(true);
    expect(isCapabilitiesView({ ...capabilities, trading_enabled: "no" })).toBe(false);
    expect(isCapabilitiesView({ ...capabilities, features: { preview: true } })).toBe(false);
    expect(isCapabilitiesView(null)).toBe(false);
  });

  it("bot/deal sayaçları + bağlantı modunu verbatim dizer", () => {
    render(<SystemStatusCard {...cardProps({ dashboard, capabilities })} />);

    expect(screen.getByText("3 bot · 2 bağlı oturum")).toBeInTheDocument();
    expect(screen.getByText("5 deal · 2 paper-oturum · 1 yedek")).toBeInTheDocument();
    expect(screen.getByText("offline · trade kapalı")).toBeInTheDocument();
    expect(screen.getByText("HISTORY_LOCAL")).toBeInTheDocument();
    expect(screen.getByText("SIMULATED")).toBeInTheDocument();
  });

  it("sayaç/mod yoksa dürüst-boş düşürür", () => {
    render(<SystemStatusCard {...cardProps()} />);

    expect(screen.getByText("○ Sayaçlar henüz okunmadı")).toBeInTheDocument();
    expect(screen.getByText("○ Mod henüz okunmadı")).toBeInTheDocument();
  });
});
