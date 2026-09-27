import { describe, expect, it } from "vitest";

import activeFixture from "../../../tests/fixtures/api/v2-bot-stats-active.json";
import dealsFixture from "../../../tests/fixtures/api/v2-bot-deals.json";
import emptyFixture from "../../../tests/fixtures/api/v2-bot-stats-empty.json";
import eventsFixture from "../../../tests/fixtures/api/v2-bot-events.json";
import closedDealsFixture from "../../../tests/fixtures/api/v2-bot-deals-closed.json";
import closedEventsFixture from "../../../tests/fixtures/api/v2-bot-events-closed.json";
import closedStatsFixture from "../../../tests/fixtures/api/v2-bot-stats-closed.json";
import {
  botDealsEnvelopeSchema,
  botEventSchema,
  botEventsEnvelopeSchema,
  botStatsEnvelopeSchema,
} from "./schemas";

describe("çalışan bot şemaları (gerçek fixture)", () => {
  it("boş istatistiği doğrular (sıfırlar + null)", () => {
    const result = botStatsEnvelopeSchema.parse(emptyFixture).data;
    expect(result.total_profit).toBe("0");
    expect(result.deals_completed).toBe(0);
    expect(result.win_rate_percent).toBeNull();
    expect(result.average_deal_profit).toBeNull();
    expect(result.average_deal_duration_us).toBeNull();
    expect(result.active_deal).toBeNull();
  });

  it("aktif deal içeren istatistiği doğrular", () => {
    const result = botStatsEnvelopeSchema.parse(activeFixture).data;
    expect(result.active_deal).not.toBeNull();
    expect(result.active_deal?.deal).toBe(1);
    expect(result.active_deal?.qty).toBe("0.00029");
    expect(result.active_deal?.unrealized_profit).toBe("-0.0945284");
    expect(result.active_deal?.unrealized_percent).toBe("-0.3865");
    expect(result.last_bar_open_us).not.toBeNull();
  });

  it("deal listesini doğrular (açık deal null kapanış)", () => {
    const result = botDealsEnvelopeSchema.parse(dealsFixture).data;
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]?.deal).toBe(1);
    expect(result[0]?.closed_at_us).toBeNull();
    expect(result[0]?.profit).toBeNull();
    expect(result[0]?.close_reason).toBeNull();
    expect(result[0]?.cumulative_profit).toBeNull();
  });

  it("kapanmış deal içeren yanıtı doğrular", () => {
    const stats = botStatsEnvelopeSchema.parse(closedStatsFixture).data;
    expect(stats.deals_completed).toBeGreaterThan(0);
    expect(stats.win_rate_percent).not.toBeNull();
    const deals = botDealsEnvelopeSchema.parse(closedDealsFixture).data;
    const closed = deals.find((deal) => deal.closed_at_us !== null);
    expect(closed?.close_reason).toBe("TAKE_PROFIT");
    expect(closed?.profit).toBe("-0.02449554");
    expect(closed?.cumulative_profit).toBe("-0.02449554");
    const events = botEventsEnvelopeSchema.parse(closedEventsFixture).data;
    expect(events.map((event) => event.kind)).toContain("DEAL_CLOSED");
  });

  it("olay listesini doğrular (bilinmeyen anahtar düşmez)", () => {
    const result = botEventsEnvelopeSchema.parse(eventsFixture).data;
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]?.kind).toBe("DEAL_STARTED");
    expect(result[0]?.detail).toMatchObject({ deal: 1, price: "84340.01" });
    const exotic = botEventSchema.parse({
      time_us: 1,
      kind: "SOMETHING_NEW",
      detail: { deal: 1, future_key: "x", n: 3, nil: null },
    });
    expect(exotic.kind).toBe("SOMETHING_NEW");
    expect(exotic.detail).toMatchObject({ future_key: "x" });
  });
});
