import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import archive409 from "../../../tests/fixtures/api/v2-bots-archive-409-revision.json";
import created from "../../../tests/fixtures/api/v2-bots-created.json";
import start409 from "../../../tests/fixtures/api/v2-bots-start-409.json";
import tr from "@/messages/tr.json";
import { botEnvelopeSchema } from "@/lib/api/schemas";
import { BotActions } from "./bot-actions";

const BOT = botEnvelopeSchema.parse(created).data;

function renderActions(handler: (url: string) => { status: number; body: unknown }) {
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
        <BotActions bot={BOT} />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("bot eylemleri", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("STOPPED botta yalnız Başlat ve Arşivle vardır", () => {
    renderActions(() => ({ status: 200, body: created }));
    expect(screen.getByRole("button", { name: "Başlat" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Arşivle" })).toBeDefined();
    expect(screen.queryByRole("button", { name: "Duraklat" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Durdur" })).toBeNull();
  });

  it("Başlat 409'u bilgi diyaloğudur, hata kırmızısı yoktur", async () => {
    renderActions((url) =>
      url.endsWith("/start") ? { status: 409, body: start409 } : { status: 200, body: created },
    );
    fireEvent.click(screen.getByRole("button", { name: "Başlat" }));
    const dialog = await screen.findByRole("dialog", { name: "Otomatik çalıştırma henüz yok" });
    expect(dialog.textContent).toContain("Bot kaydedildi.");
    expect(dialog.querySelector(".text-loss")).toBeNull();
    expect(dialog.querySelector(".bg-loss")).toBeNull();
  });

  it("Testnet botta Başlat devre dışıdır ve gerekçe gösterir", () => {
    const testnetBot = { ...BOT, mode: "TESTNET" };
    vi.stubGlobal("fetch", vi.fn());
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    render(
      <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
        <QueryClientProvider client={queryClient}>
          <BotActions bot={testnetBot} />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );
    const start = screen.getByRole("button", { name: "Başlat" });
    expect(start.hasAttribute("disabled")).toBe(true);
    expect(start.getAttribute("title")).toBe("Testnet otomatik çalışma ayrı onay gerektirir");
  });

  it("revizyon çakışması kısa not gösterir", async () => {
    renderActions((url) =>
      url.endsWith("/archive") ? { status: 409, body: archive409 } : { status: 200, body: created },
    );
    fireEvent.click(screen.getByRole("button", { name: "Arşivle" }));
    fireEvent.click(await screen.findByRole("button", { name: "Onayla" }));
    await screen.findByText("Bot başka yerde değişti, liste yenilendi.");
  });
});
