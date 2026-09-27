import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { EventStreamLink, useStreamStatus } from "./useEventStream";

type Listener = (event: { data?: string }) => void;

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;
  listeners = new Map<string, Listener[]>();

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: Listener) {
    const list = this.listeners.get(type) ?? [];
    list.push(listener);
    this.listeners.set(type, list);
  }

  removeEventListener() {}

  emit(type: string, event: { data?: string }) {
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }

  close() {
    this.closed = true;
  }
}

function renderLink(queryClient: QueryClient) {
  return render(
    <QueryClientProvider client={queryClient}>
      <EventStreamLink />
    </QueryClientProvider>,
  );
}

describe("olay akışı bağlantısı", () => {
  beforeEach(() => {
    FakeEventSource.instances = [];
    vi.stubGlobal("EventSource", FakeEventSource);
    useStreamStatus.setState({ status: "connecting" });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("/api/stream adresine bağlanır, açılınca canlı olur", () => {
    const queryClient = new QueryClient();
    renderLink(queryClient);
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(FakeEventSource.instances[0]?.url).toBe("/api/stream");
    FakeEventSource.instances[0]?.onopen?.();
    expect(useStreamStatus.getState().status).toBe("live");
  });

  it("landmark ilgili sorguları geçersiz kılar", () => {
    const queryClient = new QueryClient();
    const spy = vi.spyOn(queryClient, "invalidateQueries");
    renderLink(queryClient);
    FakeEventSource.instances[0]?.emit("landmark", {
      data: JSON.stringify({ seq: 1, kind: "BOT_CREATED", ref: "b1", summary: "s", time_us: 1 }),
    });
    const keys = spy.mock.calls.map((call) => (call[0] as { queryKey: string[] }).queryKey);
    expect(keys).toContainEqual(["v2-bots"]);
    expect(keys).toContainEqual(["v2-portfolio"]);
    expect(keys).toContainEqual(["events"]);
    expect(keys).toContainEqual(["notifications-state"]);
  });

  it("bozuk yük yutulur, akış sürer", () => {
    const queryClient = new QueryClient();
    const spy = vi.spyOn(queryClient, "invalidateQueries");
    renderLink(queryClient);
    FakeEventSource.instances[0]?.emit("landmark", { data: "bozuk" });
    expect(spy).not.toHaveBeenCalled();
    FakeEventSource.instances[0]?.emit("landmark", {
      data: JSON.stringify({ seq: 2, kind: "DEAL_CLOSED", ref: "b1:1", summary: "s", time_us: 2 }),
    });
    expect(spy).toHaveBeenCalled();
  });

  it("hata durumu ve kapanışta temizlik", () => {
    const queryClient = new QueryClient();
    const { unmount } = renderLink(queryClient);
    FakeEventSource.instances[0]?.onerror?.();
    expect(useStreamStatus.getState().status).toBe("error");
    unmount();
    expect(FakeEventSource.instances[0]?.closed).toBe(true);
  });
});
