import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TradingChart } from "./TradingChart";
import type { HistoricalChartBar } from "./datasetCatalog";

const bars: HistoricalChartBar[] = [
  { bar_index: 0, open_time_us: 1_700_000_000_000_000, close_time_us: 1_700_000_003_600_000_000, open: "100", high: "110", low: "95", close: "105", base_volume: "10" },
  { bar_index: 1, open_time_us: 1_700_000_003_600_000_000, close_time_us: 1_700_000_007_200_000_000, open: "105", high: "112", low: "100", close: "108", base_volume: "12" },
];

describe("TradingChart (Faz 16.1 -- gerçek lightweight-charts entegrasyonu)", () => {
  it("veri seçilmediğinde boş durum mesajı gösterir", () => {
    render(<TradingChart bars={[]} status="idle" error="" />);
    expect(screen.getByText("Grafik için veri seçilmedi.")).toBeInTheDocument();
  });

  it("hata durumunda hata mesajı gösterir", () => {
    render(<TradingChart bars={[]} status="error" error="beklenmedik hata" />);
    expect(screen.getByText("beklenmedik hata")).toBeInTheDocument();
  });

  it("hazır durumda gerçek chart konteynerini render eder (canvas atmadan)", () => {
    render(<TradingChart bars={bars} status="ready" error="" />);
    expect(screen.getByRole("img", { name: /TradingView grafiği: 2 bar/ })).toBeInTheDocument();
  });

  it("fiyat çizgileri (SO/TP/ortalama) prop olarak verildiğinde atmadan render eder", () => {
    render(
      <TradingChart
        bars={bars}
        status="ready"
        error=""
        priceLines={[
          { id: "avg", price: "104.5", color: "#67e8f9", title: "ORT. MALİYET" },
          { id: "tp", price: "110", color: "#2ecc9a", title: "Kâr Al" },
        ]}
        markers={[{ barIndex: 0, kind: "buy", label: "BAZ" }]}
      />,
    );
    expect(screen.getByRole("img", { name: /TradingView grafiği/ })).toBeInTheDocument();
  });
});
