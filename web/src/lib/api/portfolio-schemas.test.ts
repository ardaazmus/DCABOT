import { describe, expect, it } from "vitest";

import byBot from "../../../tests/fixtures/api/v2-portfolio-by-bot.json";
import byPair from "../../../tests/fixtures/api/v2-portfolio-by-pair.json";
import daily from "../../../tests/fixtures/api/v2-portfolio-daily.json";
import equity from "../../../tests/fixtures/api/v2-portfolio-equity.json";
import summary from "../../../tests/fixtures/api/v2-portfolio-summary.json";
import {
  byBotEnvelopeSchema,
  byPairEnvelopeSchema,
  dailyProfitEnvelopeSchema,
  equityEnvelopeSchema,
  portfolioSummaryEnvelopeSchema,
} from "./schemas";

describe("portföy şemaları (gerçek fixture)", () => {
  it("özet yanıtını doğrular", () => {
    const parsed = portfolioSummaryEnvelopeSchema.parse(summary).data;
    expect(parsed.active_bots).toBe(1);
    expect(parsed.deployed_capital).toBe("1000");
    expect(parsed.total_value).toBe("4998.51547241");
    expect(parsed.today_profit).toBe("0");
  });

  it("equity serisini doğrular", () => {
    const rows = equityEnvelopeSchema.parse(equity).data;
    expect(rows.length).toBeGreaterThan(0);
    for (const row of rows) {
      expect(row.time_us).toBeGreaterThan(0);
      expect(row.equity).toMatch(/^-?\d+(\.\d+)?$/);
    }
  });

  it("günlük kâr serisini doğrular", () => {
    const rows = dailyProfitEnvelopeSchema.parse(daily).data;
    expect(rows).toHaveLength(30);
    expect(rows[0]?.day_start_us).toBeLessThan(rows[29]?.day_start_us ?? 0);
  });

  it("bot/parite kırılımlarını doğrular", () => {
    const bots = byBotEnvelopeSchema.parse(byBot).data;
    expect(bots.length).toBeGreaterThan(0);
    expect(bots[0]).toHaveProperty("bot_name");
    const pairs = byPairEnvelopeSchema.parse(byPair).data;
    expect(pairs.length).toBeGreaterThan(0);
    expect(pairs[0]?.symbol).toBe("BTCUSDT");
  });
});
