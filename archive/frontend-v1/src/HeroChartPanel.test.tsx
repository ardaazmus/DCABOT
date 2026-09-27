import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { HistoricalChartBar } from "./datasetCatalog";
import { HeroChartPanel } from "./HeroChartPanel";

const BARS: HistoricalChartBar[] = [
  { bar_index: 1, open_time_us: 1, close_time_us: 2, open: "100", high: "105", low: "99", close: "104", base_volume: "10" },
  { bar_index: 2, open_time_us: 3, close_time_us: 4, open: "104", high: "106", low: "102", close: "103", base_volume: "12" },
];

describe("HeroChartPanel (15.1)", () => {
  it("veri yokken yükleme düğmesi ve yönlendirme gösterir", () => {
    const onLoad = vi.fn();
    render(
      <HeroChartPanel bars={[]} status="idle" error="" livePrice={null} symbolLabel="BTCUSDT" canLoad={true} loadBusy={false} onLoad={onLoad} />,
    );
    expect(screen.getByRole("heading", { name: /Piyasa grafiği/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Grafiği yükle/ }));
    expect(onLoad).toHaveBeenCalledTimes(1);
  });

  it("önkoşul yokken düğme kapalıdır ve veri seçmeye yönlendirir", () => {
    render(
      <HeroChartPanel bars={[]} status="idle" error="" livePrice={null} symbolLabel="—" canLoad={false} loadBusy={false} onLoad={() => {}} />,
    );
    expect(screen.getByRole("button", { name: /Grafiği yükle/ })).toBeDisabled();
    expect(screen.getByText(/Piyasa & Veri/)).toBeInTheDocument();
  });

  it("hazır veriyi mum grafiği olarak gösterir", () => {
    render(
      <HeroChartPanel bars={BARS} status="ready" error="" livePrice={null} symbolLabel="BTCUSDT" canLoad={true} loadBusy={false} onLoad={() => {}} />,
    );
    expect(screen.getByRole("img", { name: /Mum grafiği/ })).toBeInTheDocument();
    expect(screen.getByText(/BTCUSDT/)).toBeInTheDocument();
  });

  it("canlı baskı fiyatını grafiğe işler", () => {
    render(
      <HeroChartPanel bars={BARS} status="ready" error="" livePrice="103.5" symbolLabel="BTCUSDT" canLoad={true} loadBusy={false} onLoad={() => {}} />,
    );
    expect(screen.getByText(/canlı: 103\.5/)).toBeInTheDocument();
  });

  it("hata durumunda alert gösterir", () => {
    render(
      <HeroChartPanel bars={[]} status="error" error="Grafik alınamadı." livePrice={null} symbolLabel="BTCUSDT" canLoad={true} loadBusy={false} onLoad={() => {}} />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Grafik alınamadı.");
  });
});
