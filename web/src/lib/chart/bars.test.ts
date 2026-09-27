import { describe, expect, it } from "vitest";

import { countBars, divergingBars } from "./bars";

describe("çubuk yerleşimi (yalnız piksel)", () => {
  it("aylık getiri en büyüğe oranlanır", () => {
    const bars = divergingBars(["2", "-4", null, "geçersiz"]);
    expect(bars[0]).toEqual({ heightPct: 50, positive: true });
    expect(bars[1]).toEqual({ heightPct: 100, positive: false });
    expect(bars[2]).toBeNull();
    expect(bars[3]).toBeNull();
  });

  it("tümü sıfırsa çubuk çizilmez", () => {
    expect(divergingBars(["0", "0"])).toEqual([null, null]);
    expect(divergingBars([])).toEqual([]);
  });

  it("sayımlar en büyüğe oranlanır", () => {
    const bars = countBars([1, 3, 0]);
    expect(bars[0]).toBeCloseTo(100 / 3, 10);
    expect(bars[1]).toBe(100);
    expect(bars[2]).toBe(0);
    expect(countBars([])).toEqual([]);
    expect(countBars([0, 0])).toEqual([0, 0]);
  });
});
