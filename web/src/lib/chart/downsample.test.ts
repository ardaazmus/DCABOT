import type { Time } from "lightweight-charts";
import { describe, expect, it } from "vitest";

import { downsampleMinMax, textCurveToSamples, type SamplePoint } from "./downsample";

function series(values: number[]): SamplePoint[] {
  return values.map((value, index) => ({ time: index as unknown as Time, value }));
}

describe("min/maks koruyan seyreltme", () => {
  it("kısa seri aynen döner", () => {
    const points = series([1, 2, 3]);
    expect(downsampleMinMax(points, 100)).toEqual(points);
  });

  it("ilk ve son nokta korunur", () => {
    const points = series(Array.from({ length: 5000 }, (_, i) => i));
    const out = downsampleMinMax(points, 200);
    expect(out[0]).toEqual(points[0]);
    expect(out.at(-1)).toEqual(points.at(-1));
    expect(out.length).toBeLessThanOrEqual(201);
  });

  it("tepe ve dip kaybolmaz", () => {
    const values = Array.from({ length: 1000 }, (_, i) => i);
    values[500] = 99999;
    values[700] = -99999;
    const out = downsampleMinMax(series(values), 100);
    const kept = out.map((point) => point.value);
    expect(kept).toContain(99999);
    expect(kept).toContain(-99999);
  });

  it("metin eğri sonlu noktalara çevrilir, bozuk atlanır", () => {
    const rows = [
      { time_us: 1_000_000_000_000, equity: "100" },
      { time_us: 1_000_001_000_000, equity: "bozuk" },
      { time_us: 1_000_002_000_000, equity: null },
      { time_us: 1_000_003_000_000, equity: "99.5" },
    ];
    const out = textCurveToSamples(rows, (r) => r.time_us, (r) => r.equity);
    expect(out.map((p) => p.value)).toEqual([100, 99.5]);
    expect(out[0]?.time).toBe(1_000_000);
  });

  it("negate çizim yönünü çevirir", () => {
    const rows = [{ time_us: 1_000_000_000_000, drawdown_percent: "0.5" }];
    const out = textCurveToSamples(rows, (r) => r.time_us, (r) => r.drawdown_percent, {
      negate: true,
    });
    expect(out[0]?.value).toBe(-0.5);
  });

  it("sabit seride tekilleştirir", () => {
    const out = downsampleMinMax(series(new Array(500).fill(7)), 50);
    expect(out.length).toBeLessThanOrEqual(50);
    expect(out.every((point) => point.value === 7)).toBe(true);
  });
});
