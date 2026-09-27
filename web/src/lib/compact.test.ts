import { describe, expect, it } from "vitest";

import { parseDecimal } from "@/lib/decimal";
import { formatCompactVolume } from "./compact";

describe("hacim kısaltması", () => {
  it("1 Mn altı tam sayıdır", () => {
    expect(formatCompactVolume(parseDecimal("999999"), "tr")).toBe("999.999");
    expect(formatCompactVolume(parseDecimal("0"), "tr")).toBe("0");
    expect(formatCompactVolume(undefined, "tr")).toBe("—");
  });

  it("milyon ve milyarı kısaltır (TR)", () => {
    expect(formatCompactVolume(parseDecimal("148883205.07346"), "tr")).toBe("148,88 Mn");
    expect(formatCompactVolume(parseDecimal("1820881137"), "tr")).toBe("1,82 Mr");
    expect(formatCompactVolume(parseDecimal("1000000"), "tr")).toBe("1 Mn");
    expect(formatCompactVolume(parseDecimal("1000000000"), "tr")).toBe("1 Mr");
  });

  it("görüntü yuvarlaması yapar", () => {
    // 1.749… → 1,75
    expect(formatCompactVolume(parseDecimal("1749584854.2716818"), "tr")).toBe("1,75 Mr");
    // Elde taşması: 999.995 Mn → 1 Mr
    expect(formatCompactVolume(parseDecimal("999995000"), "tr")).toBe("1 Mr");
  });

  it("İngilizce sonekleri kullanır", () => {
    expect(formatCompactVolume(parseDecimal("1820881137"), "en")).toBe("1.82 B");
    expect(formatCompactVolume(parseDecimal("148883205"), "en")).toBe("148.88 M");
  });

  it("trilyonu kısaltır", () => {
    expect(formatCompactVolume(parseDecimal("2500000000000"), "tr")).toBe("2,5 Tr");
  });
});
