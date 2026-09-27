import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import { EquityChart } from "./equity-chart";

vi.mock("@/components/backtest/time-area-chart", () => ({
  TimeAreaChart: ({ testId }: { testId: string }) => <div data-testid={testId} />,
}));

function renderChart(points: { time_us: number; equity: string }[] = []) {
  return render(
    <NextIntlClientProvider locale="tr" messages={tr}>
      <EquityChart
        points={points.map((point) => ({ ...point, realized: "0", unrealized: "0" }))}
        range="30d"
        onRange={() => {}}
        baseline="1500"
      />
    </NextIntlClientProvider>,
  );
}

describe("özsermaye grafiği", () => {
  it("aralık çipleri ve grafik başlığı sunar", () => {
    renderChart([{ time_us: 1_000_000, equity: "1500" }]);
    expect(screen.getByText("Özsermaye")).toBeDefined();
    expect(screen.getByRole("button", { name: "7G" })).toBeDefined();
    expect(screen.getByRole("button", { name: "30G" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Tümü" })).toBeDefined();
    expect(screen.getByTestId("dashboard-equity")).toBeDefined();
  });

  it("nokta yoksa boş metin gösterir", () => {
    renderChart();
    expect(screen.getByText("İlk anlık görüntü saat başında düşer")).toBeDefined();
    expect(screen.queryByTestId("dashboard-equity")).toBeNull();
  });
});
