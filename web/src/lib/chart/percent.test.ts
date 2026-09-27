import { describe, expect, it } from "vitest";

import { parseDecimal } from "@/lib/decimal";
import { percentToWidth, ratioToWidth } from "./percent";

describe("yüzde genişliği", () => {
  it("yüzde metnini genişliğe çevirir", () => {
    expect(percentToWidth(parseDecimal("62"))).toBe("62%");
    expect(percentToWidth(parseDecimal("18.5"))).toBe("18.5%");
  });

  it("aralık dışı değerleri kırpar", () => {
    expect(percentToWidth(parseDecimal("150"))).toBe("100%");
    expect(percentToWidth(parseDecimal("-5"))).toBe("0%");
    expect(percentToWidth(parseDecimal("0"))).toBe("0%");
  });

  it("sayaç oranını genişliğe çevirir", () => {
    expect(ratioToWidth(1, 2)).toBe("50%");
    expect(ratioToWidth(0, 6)).toBe("0%");
    expect(ratioToWidth(3, 0)).toBe("0%");
  });
});
