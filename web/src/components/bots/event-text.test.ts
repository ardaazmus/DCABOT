import { describe, expect, it } from "vitest";

import { CLOSE_REASON_KEY, describeBotEvent, detailChips } from "./event-text";

describe("olay metin eşlemesi", () => {
  it("bilinen türleri anahtarlar", () => {
    expect(describeBotEvent({ time_us: 1, kind: "DEAL_STARTED", detail: {} })).toEqual({
      key: "eventDealStarted",
      tone: "open",
    });
    expect(describeBotEvent({ time_us: 1, kind: "SAFETY_ORDER_FILLED", detail: {} })).toEqual({
      key: "eventSafetyFilled",
      tone: "fill",
    });
    expect(describeBotEvent({ time_us: 1, kind: "DEAL_CLOSED", detail: {} })).toEqual({
      key: "eventDealClosed",
      tone: "close",
    });
    expect(describeBotEvent({ time_us: 1, kind: "NOTE", detail: {} }).tone).toBe("note");
    expect(describeBotEvent({ time_us: 1, kind: "AMBIGUOUS_BAR_SAFETY_FIRST", detail: {} })).toEqual({
      key: "eventAmbiguous",
      tone: "note",
    });
    expect(describeBotEvent({ time_us: 1, kind: "MANUAL_ORDER_FILLED", detail: {} })).toEqual({
      key: "eventManualFilled",
      tone: "fill",
    });
  });

  it("dört kapanış nedenini anahtarlar", () => {
    expect(CLOSE_REASON_KEY).toEqual({
      TAKE_PROFIT: "closeTakeProfit",
      STOP_LOSS: "closeStopLoss",
      MANUAL_CLOSE: "closeManual",
      CANCELLED: "closeCancelled",
    });
  });

  it("bilinmeyen türü ham geçirir", () => {
    expect(describeBotEvent({ time_us: 1, kind: "SOMETHING_NEW", detail: {} })).toEqual({
      key: "eventUnknown",
      tone: "note",
    });
  });

  it("detayları çiplere çevirir, null tire olur", () => {
    expect(
      detailChips({ deal: 1, price: "84340.01", nil: null }),
    ).toEqual([
      { label: "deal", value: "1" },
      { label: "price", value: "84340.01" },
      { label: "nil", value: "—" },
    ]);
  });
});
