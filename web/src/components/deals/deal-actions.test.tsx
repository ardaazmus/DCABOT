import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import revision409 from "../../../tests/fixtures/api/v2-bots-archive-409-revision.json";
import closedDetail from "../../../tests/fixtures/api/v2-deal-detail-closed.json";
import tr from "@/messages/tr.json";

import { DealActions } from "./deal-actions";

function renderActions(open: boolean, handler: (url: string) => { status: number; body: unknown }) {
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
        <DealActions botId="bot_x" seq={1} revision={3} open={open} testId="deal-actions" />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("deal eylemleri", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("açık deal'de üç eylem vardır", () => {
    const { container } = renderActions(true, () => ({ status: 200, body: closedDetail }));
    expect(screen.getByRole("button", { name: "Fon ekle" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Piyasadan kapat" })).toBeDefined();
    expect(screen.getByRole("button", { name: "İptal et" })).toBeDefined();
    expect(container.querySelector('[data-testid="deal-actions"]')).not.toBeNull();
  });

  it("kapalı deal'de hiçbir şey çizilmez", () => {
    const { container } = renderActions(false, () => ({ status: 200, body: closedDetail }));
    expect(container.querySelector('[data-testid="deal-actions"]')).toBeNull();
  });

  it("fon eklemede geçersiz tutar Al'ı kilitler", async () => {
    renderActions(true, () => ({ status: 200, body: closedDetail }));
    fireEvent.click(screen.getByRole("button", { name: "Fon ekle" }));
    const buy = (await screen.findByRole("button", { name: "Al" })) as HTMLButtonElement;
    expect(buy.disabled).toBe(true);
    const input = (await screen.findByTestId("add-funds-amount")) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "1,5" } });
    expect(input.value).toBe("1.5");
    expect(buy.disabled).toBe(false);
  });

  it("revizyon çakışması kısa not gösterir", async () => {
    renderActions(true, (url) =>
      url.endsWith("/close") ? { status: 409, body: revision409 } : { status: 200, body: closedDetail },
    );
    fireEvent.click(screen.getByRole("button", { name: "Piyasadan kapat" }));
    fireEvent.click(await screen.findByRole("button", { name: "Deal'i kapat" }));
    await screen.findByText("Bot başka yerde değişti, liste yenilendi.");
  });
});
