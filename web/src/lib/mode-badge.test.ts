import { describe, expect, it } from "vitest";

import { modeBadge } from "./mode-badge";

describe("mod rozeti eşlemesi", () => {
  it("SIMULATED Paper rozetidir", () => {
    expect(modeBadge("SIMULATED")).toEqual({ label: "Paper", variant: "paper" });
  });

  it("bilinmeyen değer olduğu gibi warn rozetiyle gösterilir", () => {
    expect(modeBadge("TESTNET")).toEqual({ label: "TESTNET", variant: "warn" });
    expect(modeBadge("YARIN")).toEqual({ label: "YARIN", variant: "warn" });
  });
});
