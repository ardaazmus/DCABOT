import { describe, expect, it } from "vitest";

import { durationParts, formatDayLabel, formatMonthLabel } from "./format-time";

describe("ay etiketi", () => {
  it("yerele göre kısaltır", () => {
    expect(formatMonthLabel("2026-08", "tr")).toBe("Ağu 2026");
    expect(formatMonthLabel("2026-09", "tr")).toBe("Eyl 2026");
    expect(formatMonthLabel("2026-08", "en")).toBe("Aug 2026");
  });

  it("biçim dışı metni aynen döndürür", () => {
    expect(formatMonthLabel("2026-13", "tr")).toBe("2026-13");
    expect(formatMonthLabel("ağustos", "tr")).toBe("ağustos");
    expect(formatMonthLabel("", "tr")).toBe("");
  });
});

describe("süre parçaları", () => {
  it("3 sa 12 dk üretir", () => {
    expect(durationParts((3 * 3600 + 12 * 60) * 1_000_000)).toEqual({
      hours: 3,
      minutes: 12,
      seconds: 0,
    });
  });

  it("negatifi sıfırlar", () => {
    expect(durationParts(-5)).toEqual({ hours: 0, minutes: 0, seconds: 0 });
  });
});

describe("gün etiketi", () => {
  it("gün + kısa ay yazar", () => {
    expect(formatDayLabel(Date.UTC(2026, 8, 12) * 1000, "tr")).toBe("12 Eyl");
    expect(formatDayLabel(Date.UTC(2026, 8, 12) * 1000, "en")).toBe("Sep 12");
  });
});
