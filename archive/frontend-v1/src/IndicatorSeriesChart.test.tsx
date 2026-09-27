import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IndicatorSeriesChart } from "./IndicatorSeriesChart";

describe("AA.2d indikatör seri-grafiği", () => {
  it("çok-çizgiyi verbatim lejantla çizer", () => {
    render(
      <IndicatorSeriesChart
        lines={[
          { id: "macd", label: "MACD", color: "#22d3ee", values: ["1", "2", "3"] },
          { id: "signal", label: "Sinyal", color: "#34d399", values: ["0.5", "1.5", "2.5"] },
        ]}
      />,
    );
    expect(screen.getByRole("img", { name: "İndikatör grafiği: 2 çizgi, 3 nokta." })).toBeInTheDocument();
    expect(document.querySelectorAll("polyline")).toHaveLength(2);
    expect(screen.getByText("MACD: 3")).toBeInTheDocument();
    expect(screen.getByText("Sinyal: 2.5")).toBeInTheDocument();
  });

  it("null boşlukları segment böler, birleştirmez", () => {
    render(
      <IndicatorSeriesChart lines={[{ id: "a", label: "A", color: "#22d3ee", values: ["1", null, "3"] }]} />,
    );
    expect(document.querySelectorAll("polyline")).toHaveLength(0);
    expect(document.querySelectorAll("circle")).toHaveLength(2);
  });

  it("boş ve bozuk girdide dürüst durum gösterir", () => {
    const { unmount } = render(<IndicatorSeriesChart lines={[]} />);
    expect(screen.getByRole("status")).toHaveTextContent("Grafik serisi yok.");
    unmount();
    const { unmount: unmount2 } = render(
      <IndicatorSeriesChart lines={[{ id: "a", label: "A", color: "#22d3ee", values: [null, null] }]} />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Grafik serisi yok.");
    unmount2();
    render(
      <IndicatorSeriesChart lines={[{ id: "a", label: "A", color: "#22d3ee", values: ["1", "abc"] }]} />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("seri metni bozuk");
  });
});
