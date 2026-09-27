import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TelegramSettingsCard } from "./telegram-settings";
import tr from "@/messages/tr.json";

const STATUS = {
  data: {
    vault: "OK",
    configured: false,
    enabled: false,
    chat_id: "",
    cursor_seq: 0,
    last_error: null,
  },
};

function stubFetch(body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, status: 200, json: async () => body }) as Response),
  );
}

function renderCard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <TelegramSettingsCard />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("TelegramSettingsCard", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("yapılandırılmamış durumu ve formu gösterir", async () => {
    stubFetch(STATUS);
    renderCard();
    expect(await screen.findByTestId("telegram-settings")).toBeInTheDocument();
    expect(await screen.findByText("Yapılandırılmadı")).toBeInTheDocument();
    expect(screen.getByTestId("telegram-token")).toHaveAttribute("type", "password");
    expect(screen.getByTestId("telegram-save")).toBeDisabled();
  });

  it("bağlı durumda test ve yönetim eylemleri görünür", async () => {
    stubFetch({
      data: { ...STATUS.data, configured: true, enabled: true, chat_id: "987654321" },
    });
    renderCard();
    expect(await screen.findByTestId("telegram-test")).toBeInTheDocument();
    expect(screen.getByTestId("telegram-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("telegram-forget")).toBeInTheDocument();
  });

  it("kasa yokken formu gizler", async () => {
    stubFetch({ data: { ...STATUS.data, vault: "UNAVAILABLE" } });
    renderCard();
    const notices = await screen.findAllByText("OS kasası yok");
    expect(notices.length).toBeGreaterThan(0);
    expect(screen.queryByTestId("telegram-token")).not.toBeInTheDocument();
  });
});
