import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EquityCurveChart } from "./EquityCurveChart";

describe("AA.7 equity eğrisi", () => {
  it("geçerli noktaları verbatim etiketli çizer", () => {
    render(<EquityCurveChart points={["100", "99.5", "101.25"]} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("aria-label", "Equity eğrisi: 3 nokta, aralık 99.5–101.25.");
    expect(document.querySelector("polyline")).not.toBeNull();
    expect(screen.getByText("99.5")).toBeInTheDocument();
    expect(screen.getByText("101.25")).toBeInTheDocument();
  });

  it("tek nokta çökmeksizin daire çizer", () => {
    render(<EquityCurveChart points={["42"]} />);
    expect(document.querySelector("circle")).not.toBeNull();
    expect(screen.getByRole("img")).toHaveAttribute("aria-label", "Equity eğrisi: 1 nokta, aralık 42–42.");
  });

  it("boş ve bozuk girdide dürüst durum gösterir", () => {
    const { unmount } = render(<EquityCurveChart points={[]} />);
    expect(screen.getByRole("status")).toHaveTextContent("Equity eğrisi yok.");
    unmount();
    render(<EquityCurveChart points={["100", "abc"]} />);
    expect(screen.getByRole("alert")).toHaveTextContent("equity metni bozuk");
  });
});
