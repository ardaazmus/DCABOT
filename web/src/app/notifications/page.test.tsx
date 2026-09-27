import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import readFixture from "../../../tests/fixtures/api/notifications-read.json";
import stateFixture from "../../../tests/fixtures/api/notifications-state.json";
import NotificationsPage from "./page";

const ROWS = [
  { seq: 3, kind: "BOT_STARTED", ref: "b1", summary: "Bot başlatıldı.", time_us: 3_000_000 },
  { seq: 2, kind: "BOT_CREATED", ref: "b1", summary: "Bot kuruldu.", time_us: 2_000_000 },
];

function stubFetch(empty: boolean) {
  const posts: unknown[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      let body: unknown = { data: { events: [] } };
      if (url.includes("/api/notifications/state")) {
        body = stateFixture;
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

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <NotificationsPage />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("bildirim merkezi sayfası", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("geçmişi listeler, okundu işaretle en büyük seq'i gönderir", async () => {
    const posts = stubFetch(false);
    renderPage();
    expect(await screen.findByRole("heading", { name: "Bildirimler" })).toBeDefined();
    expect(await screen.findByText("Bot başlatıldı.")).toBeDefined();
    expect(screen.getByText("Bot kuruldu.")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Tümünü okundu işaretle" }));
    await waitFor(() => expect(posts).toEqual([{ upto_seq: 3 }]));
  });

  it("olay yoksa boş durum gösterir", async () => {
    stubFetch(true);
    renderPage();
    expect(await screen.findByText("Henüz bildirim yok")).toBeDefined();
  });
});
