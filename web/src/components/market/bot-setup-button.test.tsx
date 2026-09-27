import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import rulesUsdt from "../../../tests/fixtures/api/symbol-rules-btcusdt.json";
import rulesUsdc from "../../../tests/fixtures/api/symbol-rules-btcusdc.json";
import tr from "@/messages/tr.json";
import { BotSetupButton } from "./bot-setup-button";

function renderButton(symbol: string, rules: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => rules,
    } as Response),
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <BotSetupButton symbol={symbol} />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("bot kur düğmesi (symbol-rules)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("bot_supported ise sihirbaz bağlantısıdır", async () => {
    renderButton("BTCUSDT", rulesUsdt);
    const link = await screen.findByRole("link", { name: "Bu paritede bot kur" });
    expect(link.getAttribute("href")).toBe("/bots/new?symbol=BTCUSDT");
  });

  it("QUOTE_UNSUPPORTED ise devre dışı + USDT ipucudur", async () => {
    renderButton("BTCUSDC", rulesUsdc);
    const button = await screen.findByTitle(
      "Şimdilik yalnız USDT pariteleriyle bot kurulabilir.",
    );
    expect(button).toBeDisabled();
  });

  it("NOT_TRADING ise devre dışı + işlem-dışı ipucudur", async () => {
    renderButton("OLDUSDT", {
      data: { ...rulesUsdt.data, bot_supported: false, bot_unsupported_reason: "NOT_TRADING" },
    });
    const button = await screen.findByTitle("Bu parite şu an işlemde değil.");
    expect(button).toBeDisabled();
  });
});
