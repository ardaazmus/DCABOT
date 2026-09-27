import { describe, expect, it } from "vitest";

import dateFixture from "../../../tests/fixtures/api/backtest-422-date.json";
import rangeFixture from "../../../tests/fixtures/api/backtest-422-range.json";
import sectorFixture from "../../../tests/fixtures/api/backtest-422-sector.json";
import tooLargeFixture from "../../../tests/fixtures/api/backtest-422-too-large.json";
import successFixture from "../../../tests/fixtures/api/backtest-btcusdt-1h-14d.json";
import { backtestEnvelopeSchema, problemSchema } from "./schemas";

describe("backtest şemaları (gerçek fixture)", () => {
  it("başarılı yanıtı doğrular", () => {
    const result = backtestEnvelopeSchema.parse(successFixture).data;
    expect(result.symbol).toBe("BTCUSDT");
    expect(result.interval).toBe("1h");
    expect(result.status).toBe("COMPLETED");
    expect(result.bar_count).toBe(336);
    expect(result.summary.deals_completed).toBe(2);
    expect(result.deals).toHaveLength(3);
    expect(result.deals[2]?.closed_at_us).toBeNull();
    expect(result.deals[2]?.profit).toBeNull();
    expect(result.open_deal).not.toBeNull();
    expect(result.equity_curve.length).toBeGreaterThan(0);
    expect(result.drawdown_curve.length).toBeGreaterThan(0);
    expect(result.monthly_returns).toHaveLength(1);
    expect(result.assumptions).toContain("FUNDING_NOT_MODELED");
  });

  it("her hata kodu field eşlemesiyle gelir", () => {
    const cases = [
      [dateFixture, "BACKTEST_DATE_INVALID", "start_date"],
      [rangeFixture, "BACKTEST_RANGE_INVALID", "end_date"],
      [tooLargeFixture, "BACKTEST_RANGE_TOO_LARGE", "start_date"],
      [sectorFixture, "SECTOR_BASE_ORDER_TOO_SMALL", "strategy.base_order"],
    ] as const;
    for (const [fixture, code, field] of cases) {
      const problem = problemSchema.parse(fixture);
      expect(problem.code).toBe(code);
      expect(problem.errors).toEqual([{ field, code }]);
      expect(problem.detail).not.toBe("");
    }
  });
});
