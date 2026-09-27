import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

const FRAME = 'event: landmark\nid: 1\ndata: {"seq":1}\n\n: ping\n\n';

describe("SSE geçişi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("gövdeyi ve durumu aynen geçirir", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(FRAME, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const res = await GET(new NextRequest("http://test/api/stream"));
    expect(res.status).toBe(200);
    expect(res.headers.get("Content-Type")).toContain("text/event-stream");
    expect(res.headers.get("Cache-Control")).toBe("no-cache");
    expect(await res.text()).toBe(FRAME);
  });

  it("imleci ve Last-Event-ID başlığını iletir", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(FRAME, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const res = await GET(
      new NextRequest("http://test/api/stream?last_event_id=3", {
        headers: { "last-event-id": "3" },
      }),
    );
    expect(res.status).toBe(200);
    const [url, init] = fetchMock.mock.calls[0] as [string, { headers: Record<string, string> }];
    expect(url).toContain("/api/stream?last_event_id=3");
    expect(init.headers["last-event-id"]).toBe("3");
  });

  it("yukarı akış hatası aynen geçer", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response('{"error":"x"}', { status: 422 }));
    vi.stubGlobal("fetch", fetchMock);
    const res = await GET(new NextRequest("http://test/api/stream?last_event_id=abc"));
    expect(res.status).toBe(422);
    expect(await res.text()).toBe('{"error":"x"}');
  });
});
