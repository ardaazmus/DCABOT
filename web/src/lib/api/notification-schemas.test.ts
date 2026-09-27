import { describe, expect, it } from "vitest";

import stateFixture from "../../../tests/fixtures/api/notifications-state.json";
import readFixture from "../../../tests/fixtures/api/notifications-read.json";
import { notificationStateSchema } from "./schemas";

describe("bildirim okundu-durumu şeması", () => {
  it("gerçek state yanıtını doğrular", () => {
    expect(notificationStateSchema.parse(stateFixture)).toEqual({
      data: { last_seen_seq: 0, unread_count: 1 },
    });
  });

  it("gerçek read yanıtını doğrular", () => {
    expect(notificationStateSchema.parse(readFixture)).toEqual({
      data: { last_seen_seq: 1, unread_count: 0 },
    });
  });

  it("eksik alanı reddeder", () => {
    expect(() => notificationStateSchema.parse({ data: {} })).toThrow();
  });
});
