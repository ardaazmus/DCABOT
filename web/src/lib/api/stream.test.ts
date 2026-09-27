import { describe, expect, it } from "vitest";

import streamFixture from "../../../tests/fixtures/api/stream-bot-created.txt?raw";
import { landmarkSchema } from "./schemas";
import { invalidationKeysFor, parseLandmarkEvent } from "./stream";

/** Backend'in yazdığı tüm landmark türleri (v1 + v2 + runner). */
const BACKEND_KINDS = [
  "BOT_CREATED",
  "BOT_STARTED",
  "BOT_PAUSED",
  "BOT_RESUMED",
  "BOT_STOPPED",
  "BOT_ARCHIVED",
  "BOT_REPLAYED",
  "BOT_STATUS",
  "BOT_REGISTERED",
  "BOT_BOUND",
  "DEAL_OPENED",
  "DEAL_CLOSED",
  "DEAL_CANCELLED",
  "DEAL_FUNDS_ADDED",
  "DEAL_CREATED",
  "DEAL_EVENT",
  "SAFETY_ORDER_FILLED",
  "PAPER_ACTIVATED",
  "PAPER_FILLED",
  "BACKUP_TAKEN",
  "BACKUP_VERIFIED",
  "GRID_STOPPED",
];

function framePayloads(text: string): string[] {
  return text
    .split(/\r?\n\r?\n/)
    .map((frame) => frame.trim())
    .filter((frame) => frame.length > 0)
    .map((frame) =>
      frame
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data: "))
        .map((line) => line.slice("data: ".length))
        .join("\n"),
    )
    .filter((payload) => payload.length > 0);
}

describe("SSE landmark akışı", () => {
  it("gerçek yanıt çerçeveleri şemadan geçer", () => {
    expect(streamFixture.startsWith(": connected")).toBe(true);
    const payloads = framePayloads(streamFixture).map(parseLandmarkEvent);
    expect(payloads.map((entry) => entry.kind)).toEqual(["BOT_CREATED"]);
    for (const entry of payloads) {
      expect(landmarkSchema.parse(entry)).toEqual(entry);
    }
  });

  it("bozuk veri hata fırlatır (hook yakalar, akış sürer)", () => {
    expect(() => parseLandmarkEvent("bozuk")).toThrow();
    expect(() => parseLandmarkEvent('{"seq":1}')).toThrow();
  });

  it("bot olayı bot + portföy + olay anahtarlarını geçersiz kılar", () => {
    expect(invalidationKeysFor("BOT_STARTED")).toEqual([
      ["v2-bots"],
      ["v2-bot"],
      ["v2-bot-stats"],
      ["v2-bot-deals"],
      ["v2-bot-events"],
      ["v2-portfolio"],
      ["events"],
    ]);
  });

  it("deal olayı deal + bot + portföy anahtarlarını geçersiz kılar", () => {
    expect(invalidationKeysFor("DEAL_CLOSED")).toEqual([
      ["v2-deals"],
      ["v2-deal"],
      ["v2-bot"],
      ["v2-bot-stats"],
      ["v2-bot-deals"],
      ["v2-portfolio"],
      ["events"],
    ]);
    expect(invalidationKeysFor("SAFETY_ORDER_FILLED")).toEqual(
      invalidationKeysFor("DEAL_CLOSED"),
    );
  });

  it("grid olayı grid durumu + bot + olay anahtarlarını geçersiz kılar", () => {
    expect(invalidationKeysFor("GRID_STOPPED")).toEqual([
      ["v2-grid-state"],
      ["v2-bot"],
      ["v2-bot-events"],
      ["events"],
    ]);
  });

  it("bilinmeyen tür yalnız olay listesini tazeler", () => {
    expect(invalidationKeysFor("SOME_FUTURE_KIND")).toEqual([["events"]]);
  });

  it("tüm backend türleri olay listesini de içerir", () => {
    for (const kind of BACKEND_KINDS) {
      expect(invalidationKeysFor(kind)).toContainEqual(["events"]);
    }
  });
});
