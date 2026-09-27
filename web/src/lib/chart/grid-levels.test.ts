import { describe, expect, it } from "vitest";

import { decimalToNumber, gridLevelLayout } from "./grid-levels";

describe("grid seviye yerleşimi", () => {
  it("seviyeler üstten alta dizilir, bozuk değer atlanır", () => {
    const { rows, yFor } = gridLevelLayout(["80000", "bozuk", "82000"], 100);
    expect(rows.map((row) => row.level)).toEqual(["80000", "82000"]);
    expect(rows[0]?.index).toBe(0);
    expect(rows[1]?.index).toBe(2);
    expect(rows[0]?.y).toBeGreaterThan(rows[1]?.y ?? 0);
    expect(yFor(81000)).toBeGreaterThan(rows[1]?.y ?? 0);
    expect(yFor(81000)).toBeLessThan(rows[0]?.y ?? 0);
  });

  it("tek değer aralığı çökmez", () => {
    const { rows } = gridLevelLayout(["100"], 60);
    expect(rows).toHaveLength(1);
  });

  it("ondalık metin sonlu sayıya çevrilir", () => {
    expect(decimalToNumber("81200")).toBe(81200);
    expect(decimalToNumber(null)).toBeNull();
    expect(decimalToNumber("bozuk")).toBeNull();
  });
});
