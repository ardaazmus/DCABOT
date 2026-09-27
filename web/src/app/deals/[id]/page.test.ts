import { describe, expect, it, vi } from "vitest";

import { parseDealId } from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("deal kimliği", () => {
  it("botId:sıra biçemini çözer", () => {
    expect(parseDealId("bot_abc123:4")).toEqual({ botId: "bot_abc123", seq: 4 });
    expect(parseDealId("bot_abc123%3A4")).toEqual({ botId: "bot_abc123", seq: 4 });
  });

  it("bozuk kimlikleri reddeder", () => {
    expect(parseDealId("bot_abc123")).toBeNull();
    expect(parseDealId(":3")).toBeNull();
    expect(parseDealId("bot_abc123:0")).toBeNull();
    expect(parseDealId("bot_abc123:x")).toBeNull();
  });
});
