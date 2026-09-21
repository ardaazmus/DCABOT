import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Badge } from "./Badge";

describe("Badge (15.5)", () => {
  it("etiketi ton sınıfıyla gösterir", () => {
    render(<Badge tone="ok" label="Replay Doğrulandı ✓" />);
    expect(screen.getByText("Replay Doğrulandı ✓").className).toMatch(/badge-ok/);
  });

  it("tooltip başlığını taşır", () => {
    render(<Badge tone="neutral" label="Exact ✓" title="Kesirli aritmetik, yuvarlama kaybı yok" />);
    expect(screen.getByText("Exact ✓")).toHaveAttribute("title", "Kesirli aritmetik, yuvarlama kaybı yok");
  });

  it("uyarı tonu sarı rozet olur", () => {
    render(<Badge tone="warn" label="UNKNOWN — inceleniyor" />);
    expect(screen.getByText("UNKNOWN — inceleniyor").className).toMatch(/badge-warn/);
  });
});
