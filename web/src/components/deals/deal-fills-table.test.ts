import { describe, expect, it } from "vitest";

import closedDetail from "../../../tests/fixtures/api/v2-deal-detail-closed.json";
import { dealDetailEnvelopeSchema } from "@/lib/api/schemas";

import { fillsFromEvents } from "./deal-fills-table";

describe("dolum satırları (gerçek fixture)", () => {
  it("base + manuel + satışı sırayla çıkarır", () => {
    const detail = dealDetailEnvelopeSchema.parse(closedDetail).data;
    const rows = fillsFromEvents(detail.events);
    expect(rows.map((row) => row.side)).toEqual(["base", "manual", "sell"]);
    expect(rows[1]).toMatchObject({ index: 1, price: "84158.74", qty: "0.00029" });
    expect(rows[2]).toMatchObject({ price: "84158.75", qty: "0.00058" });
  });

  it("iptal kapanışına satış satırı koymaz", () => {
    const rows = fillsFromEvents([
      { time_us: 1, kind: "DEAL_STARTED", detail: { deal: 1, price: "1", qty: "1", fee: "0" } },
      { time_us: 2, kind: "DEAL_CLOSED", detail: { deal: 1, reason: "CANCELLED", profit: "0" } },
    ]);
    expect(rows.map((row) => row.side)).toEqual(["base"]);
  });
});
