import { describe, expect, it } from "vitest";

import klinesFixture from "../../../tests/fixtures/api/klines-btcusdt-1h-300.json";
import { klinesSchema } from "@/lib/api/schemas";
import { barsToCandles, microsToTimestamp } from "./klines";

describe("klines → grafik dönüşümü (gerçek fixture)", () => {
  const bars = klinesSchema.parse(klinesFixture).data.bars;

  it("300 mumu sayıya çevirir, hepsi sonludur", () => {
    const candles = barsToCandles(bars);
    expect(candles).toHaveLength(300);
    for (const candle of candles) {
      expect(Number.isFinite(candle.open)).toBe(true);
      expect(Number.isFinite(candle.high)).toBe(true);
      expect(Number.isFinite(candle.low)).toBe(true);
      expect(Number.isFinite(candle.close)).toBe(true);
    }
  });

  it("zamanlar artan sıradadır ve mikrosaniyeden saniyeye iner", () => {
    const candles = barsToCandles(bars);
    const times = candles.map((candle) => candle.time as number);
    expect(times[0]).toBe(Math.floor(bars[0]!.open_time_us / 1_000_000));
    for (let i = 1; i < times.length; i++) {
      expect(times[i]).toBeGreaterThan(times[i - 1] as number);
    }
    // 1h aralık: ardışık mumlar 3600 sn arayla.
    expect((times[1] as number) - (times[0] as number)).toBe(3600);
  });

  it("bozuk mumu atlar, uydurmaz", () => {
    const candles = barsToCandles([
      { ...bars[0]!, close: "yalan" },
      bars[1]!,
    ]);
    expect(candles).toHaveLength(1);
  });

  it("mikrosaniye → saniye", () => {
    expect(microsToTimestamp(1790226000000000)).toBe(1790226000);
  });
});
