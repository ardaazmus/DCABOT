import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { isFavorite, useFavorites } from "./favorites";

describe("favori deposu", () => {
  beforeEach(() => {
    localStorage.clear();
    useFavorites.setState({ symbols: [] });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("ekler ve çıkarır, localStorage'a yazar", () => {
    useFavorites.getState().toggle("BTCUSDT");
    expect(useFavorites.getState().symbols).toEqual(["BTCUSDT"]);
    expect(isFavorite(useFavorites.getState().symbols, "BTCUSDT")).toBe(true);
    expect(localStorage.getItem("dcabot.favorites.v1")).toBe('["BTCUSDT"]');
    useFavorites.getState().toggle("BTCUSDT");
    expect(useFavorites.getState().symbols).toEqual([]);
  });

  it("localStorage yazamazsa bellek içinde çalışmaya devam eder", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => useFavorites.getState().toggle("ETHUSDT")).not.toThrow();
    expect(useFavorites.getState().symbols).toEqual(["ETHUSDT"]);
  });

  it("bozuk kayıt okumayı kırmaz", async () => {
    vi.spyOn(Storage.prototype, "getItem").mockReturnValue("bozuk{json");
    vi.resetModules();
    const fresh = await import("./favorites");
    expect(fresh.useFavorites.getState().symbols).toEqual([]);
  });
});
