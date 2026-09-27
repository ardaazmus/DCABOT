import { describe, expect, it } from "vitest";

import { previewToPriceLines } from "./previewOverlay";

describe("previewToPriceLines (Faz 17 A.3)", () => {
  it("giriş + SO merdivenini qwen renkleriyle çizer", () => {
    const lines = previewToPriceLines("104.5", [
      { index: 1, price: "102.41" },
      { index: 2, price: "100.32" },
      { index: 3, price: "98.23" },
    ]);
    expect(lines).toHaveLength(4);
    expect(lines[0]).toEqual({ id: "entry", price: "104.5", color: "#94a3b8", title: "GİRİŞ", lineStyle: "solid" });
    expect(lines[1]).toEqual({ id: "so-1", price: "102.41", color: "rgba(251,191,36,.85)", title: "SO#1", lineStyle: "dashed" });
    expect(lines[2]).toEqual({ id: "so-2", price: "100.32", color: "rgba(251,191,36,.85)", title: "", lineStyle: "dashed" });
    expect(lines[3]).toEqual({ id: "so-3", price: "98.23", color: "rgba(251,191,36,.85)", title: "SO#3", lineStyle: "dashed" });
  });

  it("çift numaralı son SO da etiketlenir", () => {
    const lines = previewToPriceLines("100", [
      { index: 1, price: "99" },
      { index: 2, price: "98" },
    ]);
    expect(lines.map((line) => line.title)).toEqual(["GİRİŞ", "SO#1", "SO#2"]);
  });

  it("backend fiyat metnini aynen korur (yuvarlama/yeniden biçim yok)", () => {
    const lines = previewToPriceLines("104.500", [{ index: 1, price: "102.41000" }]);
    expect(lines[0].price).toBe("104.500");
    expect(lines[1].price).toBe("102.41000");
  });

  it("anchor yoksa yalnız SO'lar, seviyeler yoksa yalnız giriş çizilir", () => {
    expect(previewToPriceLines(null, [{ index: 1, price: "99" }]).map((line) => line.id)).toEqual(["so-1"]);
    expect(previewToPriceLines("100", null).map((line) => line.id)).toEqual(["entry"]);
    expect(previewToPriceLines(null, null)).toEqual([]);
    expect(previewToPriceLines("  ", [])).toEqual([]);
  });

  it("bozuk satırları atlar, son-etiketi geçerli maksimuma göre verir", () => {
    const lines = previewToPriceLines("100", [
      { index: 0, price: "101" },
      { index: 1, price: "99" },
      { index: 2, price: "" },
      { index: 1.5, price: "97" },
      { index: 3, price: "95" },
    ]);
    expect(lines.map((line) => line.id)).toEqual(["entry", "so-1", "so-3"]);
    expect(lines.map((line) => line.title)).toEqual(["GİRİŞ", "SO#1", "SO#3"]);
  });
});
