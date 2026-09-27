import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import created from "../../../tests/fixtures/api/v2-bots-created.json";
import tr from "@/messages/tr.json";
import { BotCopyButton } from "./bot-copy-button";

const COPIED = {
  data: { ...(created as { data: Record<string, unknown> }).data, bot_id: "bot_2", name: "Klon (2)" },
};

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

function renderButton(handler: (url: string) => { status: number; body: unknown }) {
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
        <BotCopyButton botId="bot_1" />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("bot kopyalama düğmesi", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    push.mockClear();
  });

  it("başarıda kopyanın detayına gider", async () => {
    const seen: string[] = [];
    renderButton((url) => {
      seen.push(url);
      return { status: 201, body: COPIED };
    });
    fireEvent.click(screen.getByTestId("bot-copy"));
    await vi.waitFor(() => expect(push).toHaveBeenCalledWith("/bots/bot_2"));
    expect(seen.some((url) => url.endsWith("/api/v2/bots/bot_1/copy"))).toBe(true);
  });

  it("hatayı gösterir, yönlenmez", async () => {
    renderButton(() => ({
      status: 404,
      body: {
        type: "urn:local-api:problem:BOT-NOT-FOUND",
        title: "Bot bulunamadı",
        status: 404,
        detail: "Bot bulunamadı.",
        code: "BOT_NOT_FOUND",
      },
    }));
    fireEvent.click(screen.getByTestId("bot-copy"));
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe("Bot bulunamadı.");
    expect(push).not.toHaveBeenCalled();
  });
});
