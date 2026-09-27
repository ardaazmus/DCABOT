import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import { ReplayForm } from "./replay-form";

const SUCCESS = {
  data: {
    bars: 2880,
    deals_opened: 2,
    deals_closed: 1,
    fills: 0,
    events: 5,
    first_bar_open_us: 1789862400000000,
    last_bar_open_us: 1790035140000000,
    symbols: ["BTCUSDT"],
    stopped: null,
  },
};

function isoDaysAgo(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().slice(0, 10);
}

function renderForm(handler: (url: string) => { status: number; body: unknown }) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const { status, body } = handler(String(input));
      return new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/problem+json" },
      });
    }),
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <ReplayForm botId="bot_1" />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("geçmiş çalıştırma formu", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("varsayılan aralık son 3→1 gündür", () => {
    renderForm(() => ({ status: 200, body: SUCCESS }));
    expect((screen.getByTestId("replay-start") as HTMLInputElement).value).toBe(isoDaysAgo(3));
    expect((screen.getByTestId("replay-end") as HTMLInputElement).value).toBe(isoDaysAgo(1));
  });

  it("başarıda özet gösterir", async () => {
    const seen: string[] = [];
    renderForm((url) => {
      seen.push(url);
      return { status: 200, body: SUCCESS };
    });
    fireEvent.click(screen.getByTestId("replay-run"));
    const result = await screen.findByTestId("replay-result");
    expect(result.textContent).toContain("2880");
    expect(result.textContent).toContain("2");
    expect(seen.some((url) => url.endsWith("/api/v2/bots/bot_1/replay"))).toBe(true);
    // Başarıda form sonuç paneline dönüşür; ikinci çalıştırma düğmesi kalkar.
    expect(screen.queryByTestId("replay-run")).toBeNull();
  });

  it("422 alan hatası ilgili tarihin altında görünür", async () => {
    renderForm(() => ({
      status: 422,
      body: {
        type: "urn:local-api:problem:REPLAY-RANGE-TOO-LONG",
        title: "Geçmiş çalıştırma ayarları geçersiz",
        status: 422,
        detail: "En fazla 10080 mum (7 gün); aralığı kısaltın.",
        code: "REPLAY_RANGE_TOO_LONG",
        errors: [{ field: "start_date", code: "REPLAY_RANGE_TOO_LONG" }],
      },
    }));
    fireEvent.click(screen.getByTestId("replay-run"));
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("7 gün");
    expect(screen.queryByTestId("replay-error")).toBeNull();
  });

  it("409 genel hatadır", async () => {
    renderForm(() => ({
      status: 409,
      body: {
        type: "urn:local-api:problem:REPLAY-STATE-EXISTS",
        title: "Bot geçmişte çalıştırılamaz",
        status: 409,
        detail: "Bu botun zaten çalışmışlığı var; geçmiş çalıştırma bir kez yapılır.",
        code: "REPLAY_STATE_EXISTS",
      },
    }));
    fireEvent.click(screen.getByTestId("replay-run"));
    const alert = await screen.findByTestId("replay-error");
    expect(alert.textContent).toContain("bir kez");
  });
});
