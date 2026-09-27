import type { Time } from "lightweight-charts";
import { describe, expect, it } from "vitest";

import closedDetail from "../../../tests/fixtures/api/v2-deal-detail-closed.json";
import { dealDetailEnvelopeSchema, type BotEvent } from "@/lib/api/schemas";

import { backtestDealMarkers, dealMarkers } from "./deal-markers";
import { microsToTimestamp } from "./klines";

const QUARTER_HOUR_US = 15 * 60 * 1_000_000;
const PALETTE = { profit: "#0f0", loss: "#f00" };

function candleSet(events: readonly BotEvent[]): Set<Time> {
  return new Set(events.map((event) => microsToTimestamp(Math.floor(event.time_us / QUARTER_HOUR_US) * QUARTER_HOUR_US)));
}

describe("deal işaretleri (gerçek fixture)", () => {
  it("alışları alta, satışı üste koyar", () => {
    const detail = dealDetailEnvelopeSchema.parse(closedDetail).data;
    const markers = dealMarkers(detail.events, QUARTER_HOUR_US, candleSet(detail.events), PALETTE);
    expect(markers).toHaveLength(3);
    expect(markers[0]).toMatchObject({ position: "belowBar", shape: "arrowUp" });
    expect(markers[1]).toMatchObject({ position: "belowBar", shape: "arrowUp" });
    expect(markers[2]).toMatchObject({ position: "aboveBar", shape: "arrowDown" });
  });

  it("backtest: giriş alta yeşil, kârlı çıkış üste yeşil, zarar kırmızı", () => {
    const hour = 3_600_000_000;
    const candles = new Set<Time>([0, 1, 2, 3].map((i) => microsToTimestamp(i * hour)));
    const markers = backtestDealMarkers(
      [
        { started_at_us: 0, closed_at_us: hour, profit: "12.5" },
        { started_at_us: 2 * hour, closed_at_us: 3 * hour, profit: "-3" },
        { started_at_us: 4 * hour, closed_at_us: null, profit: null },
      ],
      candles,
      PALETTE,
    );
    // Eğride karşılığı olmayan açık deal girişi atılır.
    expect(markers).toHaveLength(4);
    expect(markers[0]).toMatchObject({ position: "belowBar", color: "#0f0" });
    expect(markers[1]).toMatchObject({ position: "aboveBar", color: "#0f0" });
    expect(markers[2]).toMatchObject({ position: "belowBar", color: "#0f0" });
    expect(markers[3]).toMatchObject({ position: "aboveBar", color: "#f00" });
    const times = markers.map((m) => m.time as number);
    expect([...times].sort((a, b) => a - b)).toEqual(times);
  });

  it("iptal satışını çizmez, mum dışı zamanı atar", () => {
    const events: BotEvent[] = [
      { time_us: 1000, kind: "DEAL_CLOSED", detail: { deal: 1, reason: "CANCELLED", profit: "0" } },
      { time_us: 2000, kind: "DEAL_STARTED", detail: { deal: 1, price: "1", qty: "1", fee: "0" } },
    ];
    expect(dealMarkers(events, QUARTER_HOUR_US, new Set(), PALETTE)).toEqual([]);
    const withCandle = new Set<Time>([microsToTimestamp(0)]);
    const markers = dealMarkers(events, QUARTER_HOUR_US, withCandle, PALETTE);
    expect(markers).toHaveLength(1);
    expect(markers[0]).toMatchObject({ position: "belowBar" });
  });
});
