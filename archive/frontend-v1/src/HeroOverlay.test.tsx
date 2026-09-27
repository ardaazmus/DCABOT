import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { TradingChartProps } from "./TradingChart";

const captured = vi.hoisted(() => ({ current: null as TradingChartProps | null }));

vi.mock("./TradingChart", () => ({
  TradingChart: (props: TradingChartProps) => {
    captured.current = props;
    return <div role="img" aria-label="mock trading chart" />;
  },
}));

// eslint-disable-next-line import/first
import type { HistoricalChartBar } from "./datasetCatalog";
// eslint-disable-next-line import/first
import { HeroChartPanel } from "./HeroChartPanel";
// eslint-disable-next-line import/first
import type { ChartPriceLine } from "./TradingChart";

const BARS: HistoricalChartBar[] = [
  { bar_index: 1, open_time_us: 1_700_000_000_000_000, close_time_us: 1_700_000_003_600_000_000, open: "100", high: "105", low: "99", close: "104", base_volume: "10" },
];

const OVERLAY: ChartPriceLine[] = [
  { id: "entry", price: "104", color: "#94a3b8", title: "GİRİŞ", lineStyle: "solid" },
  { id: "so-1", price: "102", color: "rgba(251,191,36,.85)", title: "SO#1", lineStyle: "dashed" },
];

function renderHero(overlayLines: ChartPriceLine[] | undefined, livePrice: string | null) {
  captured.current = null;
  render(
    <HeroChartPanel
      bars={BARS}
      status="ready"
      error=""
      livePrice={livePrice}
      symbolLabel="BTCUSDT"
      canLoad={false}
      loadBusy={false}
      onLoad={() => {}}
      overlayLines={overlayLines}
    />,
  );
}

describe("HeroChartPanel overlay birleşimi (Faz 17 A.3)", () => {
  it("overlay çizgilerini canlı çizginin önüne ekler", async () => {
    renderHero(OVERLAY, "103.5");
    await screen.findByRole("img", { name: "mock trading chart" });
    expect(captured.current?.priceLines).toEqual([
      ...OVERLAY,
      { id: "live", price: "103.5", color: "#fbbf24", title: "Canlı", lineStyle: "dashed" },
    ]);
  });

  it("canlı fiyat yoksa yalnız overlay çizilir", async () => {
    renderHero(OVERLAY, null);
    await screen.findByRole("img", { name: "mock trading chart" });
    expect(captured.current?.priceLines).toEqual(OVERLAY);
  });

  it("overlay verilmezse davranış değişmez (yalnız canlı)", async () => {
    renderHero(undefined, "103.5");
    await screen.findByRole("img", { name: "mock trading chart" });
    expect(captured.current?.priceLines).toEqual([
      { id: "live", price: "103.5", color: "#fbbf24", title: "Canlı", lineStyle: "dashed" },
    ]);
  });
});
