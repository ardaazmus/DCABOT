import type { Time } from "lightweight-charts";
import { describe, expect, it } from "vitest";

import klinesFixture from "../../../tests/fixtures/api/klines-btcusdt-1h-300.json";
import smaFixture from "../../../tests/fixtures/api/indicators-sma-20.json";
import { klinesSchema, seriesIndicatorSchema } from "@/lib/api/schemas";
import { microsToTimestamp } from "./klines";
import { levelToSegments, pointsToHistogram, pointsToSegments } from "./indicators";

const COLORS = { up: "up", down: "down", neutral: "none" };

describe("indikatör → grafik dönüşümü (gerçek fixture)", () => {
  const bars = klinesSchema.parse(klinesFixture).data.bars;
  const times: Time[] = bars.map((bar) => microsToTimestamp(bar.open_time_us));
  const points = seriesIndicatorSchema.parse(smaFixture).data.points;

  it("ısınma null'ları atlanır, 0 uydurulmaz", () => {
    const segments = pointsToSegments(points, (p) => p.value, times);
    // SMA 20: ilk 19 nokta null, tek parça kalır.
    expect(segments).toHaveLength(1);
    expect(segments[0]).toHaveLength(300 - 19);
    expect(segments[0]?.[0]?.time).toBe(times[19]);
    for (const segment of segments) {
      for (const point of segment) {
        expect(Number.isFinite(point.value)).toBe(true);
      }
    }
  });

  it("ortadaki null parçayı böler (boşluk)", () => {
    const gapped = points.map((p, i) => (i === 100 ? { ...p, value: null } : p));
    const segments = pointsToSegments(gapped, (p) => p.value, times);
    expect(segments).toHaveLength(2);
    expect(segments[0]?.at(-1)?.time).toBe(times[99]);
    expect(segments[1]?.[0]?.time).toBe(times[101]);
  });

  it("seviye çizgisi tüm mumlara aynı değeri yazar", () => {
    const segments = levelToSegments("83468", times);
    expect(segments).toHaveLength(1);
    expect(segments[0]).toHaveLength(times.length);
    expect(segments[0]?.[0]).toEqual({ time: times[0], value: 83468 });
    expect(segments[0]?.at(-1)).toEqual({ time: times.at(-1), value: 83468 });
  });

  it("boş/geçersiz seviye çizilmez", () => {
    expect(levelToSegments(null, times)).toEqual([]);
    expect(levelToSegments(undefined, times)).toEqual([]);
    expect(levelToSegments("geçersiz", times)).toEqual([]);
    expect(levelToSegments("100", [])).toEqual([]);
  });

  it("histogram rengi metnin işaretinden gelir, null atlanır", () => {
    const sample = [
      { index: 0, value: "1.5" },
      { index: 1, value: "-2.5" },
      { index: 2, value: "0" },
      { index: 3, value: null },
    ];
    const barsOut = pointsToHistogram(sample, (p) => p.value, times, COLORS);
    expect(barsOut).toHaveLength(3);
    expect(barsOut[0]).toMatchObject({ value: 1.5, color: "up" });
    expect(barsOut[1]).toMatchObject({ value: -2.5, color: "down" });
    expect(barsOut[2]).toMatchObject({ value: 0, color: "none" });
  });
});
