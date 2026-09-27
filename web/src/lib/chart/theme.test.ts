import { TickMarkType, type UTCTimestamp } from "lightweight-charts";
import { describe, expect, it } from "vitest";

import { createDayTickFormatter, formatPriceAxis, labToRgb, withAlpha } from "./theme";

describe("lab → sRGB dönüşümü", () => {
  it("akromatik griyi eşit kanallı rgb yapar", () => {
    // Koyu tema --muted-foreground'un Chromium'daki hesaplanmış biçimi.
    const rgb = labToRgb("lab(66.128% -.0000298023 .0000119209)");
    const channels = rgb
      .replace(/^rgba?\(/, "")
      .replace(/\)$/, "")
      .split(",")
      .map(Number);
    expect(channels).toHaveLength(3);
    const [r, g, b] = channels as [number, number, number];
    for (const channel of [r, g, b]) {
      expect(channel).toBeGreaterThanOrEqual(155);
      expect(channel).toBeLessThanOrEqual(168);
    }
    expect(Math.abs(r! - g!)).toBeLessThanOrEqual(1);
    expect(Math.abs(g! - b!)).toBeLessThanOrEqual(1);
  });

  it("alfayı rgba olarak taşır", () => {
    expect(labToRgb("lab(100% 0 0 / 10%)")).toBe("rgba(255, 255, 255, 0.1)");
  });

  it("sRGB girdisini aynen geçirir", () => {
    expect(labToRgb("rgb(1, 2, 3)")).toBe("rgb(1, 2, 3)");
    expect(labToRgb("#ff0000")).toBe("#ff0000");
  });

  it("bozuk girdiyi aynen döndürür", () => {
    expect(labToRgb("lab(bogus)")).toBe("lab(bogus)");
  });
});

describe("opaklık uygulaması", () => {
  it("rgb renge alfa ekler", () => {
    expect(withAlpha("rgb(10, 20, 30)", 0.4)).toBe("rgba(10, 20, 30, 0.4)");
    expect(withAlpha("rgba(10, 20, 30, 1)", 0.4)).toBe("rgba(10, 20, 30, 0.4)");
  });

  it("bilinmeyen biçimi aynen döndürür", () => {
    expect(withAlpha("red", 0.4)).toBe("red");
  });
});

describe("gün etiketi bastırma", () => {
  it("aynı günün tekrarını boş döndürür", () => {
    const format = createDayTickFormatter();
    const stamp = (seconds: number) => seconds as UTCTimestamp;
    // 2026-09-14 00:00 ve 12:00 UTC.
    expect(format(stamp(1789344000), TickMarkType.DayOfMonth, "tr")).toBe("14");
    expect(format(stamp(1789387200), TickMarkType.DayOfMonth, "tr")).toBe("");
    expect(format(stamp(1789430400), TickMarkType.DayOfMonth, "tr")).toBe("15");
  });
});

describe("eksen fiyat etiketi", () => {
  it("Türkçe gruplar", () => {
    expect(formatPriceAxis(92000, "tr")).toBe("92.000,00");
    expect(formatPriceAxis(84396.04, "tr")).toBe("84.396,04");
    expect(formatPriceAxis(-12.5, "tr")).toBe("-12,50");
  });

  it("İngilizce gruplar", () => {
    expect(formatPriceAxis(92000, "en")).toBe("92,000.00");
  });

  it("sonlu olmayan değerde em-dash", () => {
    expect(formatPriceAxis(Number.NaN, "tr")).toBe("—");
  });
});
