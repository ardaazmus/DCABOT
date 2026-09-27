import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BotCreateView, type BotCreateType } from "./BotCreateView";
import type { HistoricalChartBar } from "./datasetCatalog";

const BARS: HistoricalChartBar[] = [
  { bar_index: 1, open_time_us: 1, close_time_us: 2, open: "100", high: "105", low: "99", close: "104", base_volume: "10" },
];

function renderView(overrides: Partial<Parameters<typeof BotCreateView>[0]> = {}) {
  const props = {
    botType: "DCA" as BotCreateType,
    onBotTypeChange: vi.fn(),
    onBack: vi.fn(),
    onOpenBacktest: vi.fn(),
    bars: [],
    chartStatus: "idle" as const,
    chartError: "",
    livePrice: null,
    symbolLabel: "BTCUSDT",
    canLoadChart: false,
    chartLoading: false,
    onLoadChart: vi.fn(),
    dataRange: null,
    backtestReady: false,
    renderForm: (type: BotCreateType) => <p>{`${type}-form`}</p>,
    ...overrides,
  };
  const result = render(<BotCreateView {...props} />);
  return { ...props, ...result };
}

describe("BotCreateView (15.3)", () => {
  it("başlık + geri düğmesi + tip seçici gösterir", () => {
    const props = renderView();
    expect(screen.getByRole("heading", { name: "Bot Oluştur" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Kapat" }));
    expect(props.onBack).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("radiogroup", { name: "Bot tipi" })).toBeInTheDocument();
    expect(screen.getByText("DCA-form")).toBeInTheDocument();
  });

  it("tip değişimi formu değiştirir", () => {
    const props = renderView();
    fireEvent.click(screen.getByRole("radio", { name: "Grid Bot" }));
    expect(props.onBotTypeChange).toHaveBeenCalledWith("GRID");
  });

  it("grafik her zaman görünür (hero yeniden kullanımı)", () => {
    renderView({ bars: BARS, chartStatus: "ready" });
    expect(screen.getByRole("img", { name: /Mum grafiği/ })).toBeInTheDocument();
  });

  it("alt bar veri aralığı + hazır rozeti + backtest düğmesi gösterir", () => {
    const props = renderView({ dataRange: "2025-01-01 → 2025-01-02", backtestReady: true });
    expect(screen.getByText(/2025-01-01 → 2025-01-02/)).toBeInTheDocument();
    expect(screen.getByText("Çalışmaya hazır")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Geriye Dönük Test" }));
    expect(props.onOpenBacktest).toHaveBeenCalledTimes(1);
  });

  it("veri yokken hazır rozeti yerine beklenti gösterir", () => {
    const { container } = renderView({ dataRange: null, backtestReady: false });
    expect(container.querySelector(".bot-create-footer .state-label")).toHaveTextContent("Veri bekleniyor");
  });
});
