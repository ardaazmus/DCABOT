import { describe, expect, it } from "vitest";

import { formatDealDuration } from "./format-duration";

describe("deal süresi biçimi", () => {
  it("iki birim gösterir", () => {
    // 7 sa 56 dk.
    expect(formatDealDuration(28_560_000_000, "tr")).toBe("7s 56dk");
    expect(formatDealDuration(28_560_000_000, "en")).toBe("7h 56m");
  });

  it("34 saat 1 gün 10 saattir", () => {
    expect(formatDealDuration(122_400_000_000, "tr")).toBe("1g 10s");
  });

  it("tek birim ve sıfır", () => {
    expect(formatDealDuration(300_000_000, "tr")).toBe("5dk");
    expect(formatDealDuration(45_000_000, "tr")).toBe("45sn");
    expect(formatDealDuration(0, "tr")).toBe("0dk");
    expect(formatDealDuration(0, "en")).toBe("0m");
  });

  it("negatif ve kesirli mikrosaniye alta yuvarlanır", () => {
    expect(formatDealDuration(-5, "tr")).toBe("0dk");
    expect(formatDealDuration(1_500_000, "tr")).toBe("1sn");
  });
});
