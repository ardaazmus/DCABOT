import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import readFixture from "../../../tests/fixtures/api/notifications-read.json";
import stateFixture from "../../../tests/fixtures/api/notifications-state.json";
import { maxSeqOf, Notifications } from "./notifications";

const ROWS = [
  { seq: 7, kind: "BOT_CREATED", ref: "b1", summary: "Bot kuruldu.", time_us: 7_000_000 },
  { seq: 6, kind: "DEAL_CLOSED", ref: "b1:1", summary: "Deal kapandı.", time_us: 6_000_000 },
];

function stubFetch(empty: boolean) {
  const posts: unknown[] = [];
  const state = empty ? { data: { last_seen_seq: 7, unread_count: 0 } } : stateFixture;
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      let body: unknown = { data: { events: [] } };
      if (url.includes("/api/notifications/state")) {
        body = state;
      } else if (url.includes("/api/events")) {
        body = empty ? { data: { events: [] } } : { data: { events: ROWS } };
      } else if (url.includes("/api/notifications/read")) {
        posts.push(JSON.parse(String((init?.body as string) ?? "{}")));
        body = readFixture;
      }
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
  return posts;
}

function renderBell() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <Notifications />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("bildirim çıngırağı", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maxSeqOf en büyük seq'i verir", () => {
    expect(maxSeqOf(ROWS)).toBe(7);
    expect(maxSeqOf([])).toBe(0);
  });

  it("okunmamış sayısı rozette görünür", async () => {
    stubFetch(false);
    renderBell();
    expect(await screen.findByLabelText("1 okunmamış bildirim")).toBeDefined();
    expect(screen.getByText("1")).toBeDefined();
  });

  it("sıfırda rozet çıkmaz, boş metin görünür", async () => {
    stubFetch(true);
    renderBell();
    expect(await screen.findByLabelText("Bildirimler")).toBeDefined();
    expect(screen.queryByText("1")).toBeNull();
    fireEvent.click(screen.getByLabelText("Bildirimler"));
    expect(await screen.findByText("Henüz bildirim yok")).toBeDefined();
  });

  it("açılır liste satırları ve tüm-merkez bağlantısını gösterir", async () => {
    stubFetch(false);
    renderBell();
    fireEvent.click(await screen.findByLabelText("1 okunmamış bildirim"));
    expect(await screen.findByText("Bot kuruldu.")).toBeDefined();
    expect(screen.getByText("Deal kapandı.")).toBeDefined();
    expect(screen.getByRole("link", { name: "Tüm bildirimler" })).toHaveProperty(
      "href",
      expect.stringContaining("/notifications"),
    );
  });

  it("tümünü okundu işaretle en büyük seq'i gönderir", async () => {
    const posts = stubFetch(false);
    renderBell();
    fireEvent.click(await screen.findByLabelText("1 okunmamış bildirim"));
    fireEvent.click(await screen.findByRole("button", { name: "Tümünü okundu işaretle" }));
    await waitFor(() => expect(posts).toEqual([{ upto_seq: 7 }]));
  });
});
