import { describe, expect, it } from "vitest";

import { buildDetailHash, buildSectionHash, parseHashRoute } from "./hashRoute";

describe("hashRoute (AB.1)", () => {
  it("9 bölüm kökünü okur", () => {
    for (const section of ["overview", "bots", "create", "deals", "backtest", "lab", "risk", "market", "system"] as const) {
      expect(parseHashRoute(`#/${section}`)).toEqual({ section, detail: null });
    }
  });

  it("bot/deal derin bağlarını okur", () => {
    expect(parseHashRoute("#/bots/b-1")).toEqual({ section: "bots", detail: { kind: "bot", id: "b-1" } });
    expect(parseHashRoute("#/deals/d-9")).toEqual({ section: "deals", detail: { kind: "deal", id: "d-9" } });
  });

  it("bilinmeyen/bozuk/boş hash overview'a düşer", () => {
    expect(parseHashRoute("#/events")).toEqual({ section: "overview", detail: null });
    expect(parseHashRoute("#/settings")).toEqual({ section: "overview", detail: null });
    expect(parseHashRoute("#/bots/%E0%A4%A")).toEqual({ section: "bots", detail: null });
    expect(parseHashRoute("")).toEqual({ section: "overview", detail: null });
  });

  it("eski yalın hash'leri okur (#bots, #lab)", () => {
    expect(parseHashRoute("#bots")).toEqual({ section: "bots", detail: null });
    expect(parseHashRoute("#lab")).toEqual({ section: "lab", detail: null });
  });

  it("detay dışı kuyruğu yoksayar", () => {
    expect(parseHashRoute("#/risk/x")).toEqual({ section: "risk", detail: null });
  });

  it("kurucu/ayrıştırıcı turu bozmaz", () => {
    expect(parseHashRoute(buildSectionHash("backtest"))).toEqual({ section: "backtest", detail: null });
    expect(parseHashRoute(buildDetailHash("bot", "b 1/x"))).toEqual({ section: "bots", detail: { kind: "bot", id: "b 1/x" } });
  });
});
