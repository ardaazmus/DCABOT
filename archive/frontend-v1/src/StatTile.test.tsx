import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatTile } from "./StatTile";

describe("StatTile (AB.1 görsel kit)", () => {
  it("sayısal dizeyi aynen yazar (dönüşüm/kısaltma yok)", () => {
    render(<StatTile label="Paper nakit" value="10999.50000000" sub="USDT" />);
    expect(screen.getByText("10999.50000000")).toBeInTheDocument();
    expect(screen.getByText("USDT")).toBeInTheDocument();
  });

  it("tanımsız değer boş yazılır, 0 uydurulmaz", () => {
    render(<StatTile label="Açık deal" value="" />);
    const group = screen.getByRole("group", { name: "Açık deal" });
    expect(group.querySelector(".stat-value")?.textContent).toBe("");
    expect(group.textContent).not.toMatch(/0/);
  });
});
