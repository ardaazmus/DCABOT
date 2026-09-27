import { describe, expect, it } from "vitest";

import activeFixture from "../../../tests/fixtures/api/v2-deals-active.json";
import closedFixture from "../../../tests/fixtures/api/v2-deals-closed.json";
import closedDetailFixture from "../../../tests/fixtures/api/v2-deal-detail-closed.json";
import openDetailFixture from "../../../tests/fixtures/api/v2-deal-detail-open.json";
import { dealDetailEnvelopeSchema, dealsEnvelopeSchema } from "./schemas";

describe("deal şemaları (gerçek fixture)", () => {
  it("birleşik aktif listeyi doğrular", () => {
    const result = dealsEnvelopeSchema.parse(activeFixture).data;
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]?.closed_at_us).toBeNull();
    expect(result[0]?.bot_name).toBe("W-F6 fixture");
    expect(result[0]?.manual_orders_filled).toBe(0);
  });

  it("birleşik geçmiş listeyi doğrular (manuel kapatma)", () => {
    const result = dealsEnvelopeSchema.parse(closedFixture).data;
    expect(result.length).toBeGreaterThan(0);
    expect(result[0]?.close_reason).toBe("MANUAL_CLOSE");
    expect(result[0]?.manual_orders_filled).toBe(1);
    expect(result[0]?.profit).toBe("-0.09762125");
  });

  it("açık deal detayını doğrular (canlı ekonomi)", () => {
    const result = dealDetailEnvelopeSchema.parse(openDetailFixture).data;
    expect(result.qty).toBe("0.00029");
    expect(result.average_price).toBe("84158.75");
    expect(result.unrealized_percent).toBe("0");
    expect(result.take_profit_price).toBe("85841.93");
    expect(result.next_safety_order_price).toBe("82896.36");
    expect(result.duration_us).toBeNull();
    expect(result.cumulative_profit).toBeNull();
    expect(result.fees).toBe("0.02440604");
    expect(result.gross_profit).toBeNull();
    expect(result.events.map((event) => event.kind)).toEqual(["DEAL_STARTED"]);
  });

  it("kapalı deal detayını doğrular (dolum tekrarı + manuel)", () => {
    const result = dealDetailEnvelopeSchema.parse(closedDetailFixture).data;
    expect(result.qty).toBe("0.00058");
    expect(result.cost).toBe("48.8120721");
    expect(result.average_price).toBe("84158.745");
    expect(result.duration_us).toBe(74366804);
    expect(result.cumulative_profit).toBe("-0.09762125");
    expect(result.fees).toBe("0.09762415");
    expect(result.gross_profit).toBe("0.0000029");
    expect(result.mark_price).toBeNull();
    expect(result.events.map((event) => event.kind)).toEqual([
      "DEAL_STARTED",
      "MANUAL_ORDER_FILLED",
      "DEAL_CLOSED",
    ]);
  });
});
