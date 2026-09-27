import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AdvancedTools } from "./AdvancedTools";

describe("AdvancedTools", () => {
  it("varsayılan kapalı gelir, içeriği DOM'da tutar", () => {
    render(
      <AdvancedTools title="Gelişmiş Araçlar">
        <p>araç içeriği</p>
      </AdvancedTools>,
    );
    const details = document.querySelector("details.advanced-tools") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    expect(screen.getByText("araç içeriği")).toBeInTheDocument();
    expect(screen.getByText("Gelişmiş Araçlar", { selector: "summary" })).toBeInTheDocument();
  });
});
