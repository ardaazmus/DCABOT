import { describe, expect, it } from "vitest";

import { filterCommands, type CommandItem } from "./command-filter";

const ITEMS: CommandItem[] = [
  { id: "page:dashboard", label: "Kontrol merkezi", hint: "/" },
  { id: "page:market", label: "Piyasa", hint: "/market" },
  { id: "symbol:BTCUSDT", label: "BTCUSDT", hint: "TRADING" },
  { id: "symbol:ETHUSDT", label: "ETHUSDT", hint: "TRADING" },
  { id: "symbol:NEOBTC", label: "NEOBTC", hint: "BREAK" },
];

describe("komut paleti filtreleme", () => {
  it("boş sorgu ilk öğeleri döndürür", () => {
    expect(filterCommands(ITEMS, "", 2)).toEqual(ITEMS.slice(0, 2));
  });

  it("parite koduyla eşleşir (büyük/küçük harf duyarsız)", () => {
    const results = filterCommands(ITEMS, "btc");
    expect(results.map((item) => item.id)).toEqual([
      "symbol:BTCUSDT",
      "symbol:NEOBTC",
    ]);
  });

  it("Türkçe başlıkla eşleşir", () => {
    expect(filterCommands(ITEMS, "piyasa").map((item) => item.id)).toEqual([
      "page:market",
    ]);
    // Büyük İ ile yazım da aynı sonucu verir.
    expect(filterCommands(ITEMS, "PİYASA").map((item) => item.id)).toEqual([
      "page:market",
    ]);
  });

  it("ipucu alanında da arar", () => {
    expect(filterCommands(ITEMS, "break").map((item) => item.id)).toEqual([
      "symbol:NEOBTC",
    ]);
  });

  it("eşleşme yoksa boş liste döner", () => {
    expect(filterCommands(ITEMS, "zzz")).toEqual([]);
  });

  it("sonuç sayısı limitle sınırlanır", () => {
    expect(filterCommands(ITEMS, "USDT", 1)).toHaveLength(1);
  });
});
