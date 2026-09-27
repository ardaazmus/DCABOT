import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import Home from "./page";

import byBot from "../../tests/fixtures/api/v2-portfolio-by-bot.json";
import byPair from "../../tests/fixtures/api/v2-portfolio-by-pair.json";
import daily from "../../tests/fixtures/api/v2-portfolio-daily.json";
import equity from "../../tests/fixtures/api/v2-portfolio-equity.json";
import bots from "../../tests/fixtures/api/v2-bots-list-one.json";
import summary from "../../tests/fixtures/api/v2-portfolio-summary.json";

vi.mock("@/components/backtest/time-area-chart", () => ({
  TimeAreaChart: ({ testId }: { testId: string }) => <div data-testid={testId} />,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

function stubFetch(empty: boolean) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      let body: unknown = { data: [] };
      if (url.includes("/api/v2/bots") && !url.includes("/deals") && !url.includes("/events")) {
        body = empty ? { data: [] } : bots;
      } else if (url.includes("/stats/portfolio/summary")) {
        body = summary;
      } else if (url.includes("/stats/portfolio/equity")) {
        body = equity;
      } else if (url.includes("/stats/portfolio/daily-profit")) {
        body = daily;
      } else if (url.includes("/stats/portfolio/by-bot")) {
        body = byBot;
      } else if (url.includes("/stats/portfolio/by-pair")) {
        body = byPair;
      } else if (url.includes("/api/events")) {
        body = { data: { events: [] } };
      }
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
}

function renderHome() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <Home />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("kontrol merkezi (gerçek fixture)", () => {
  it("bot yoksa kurulum daveti gösterir", async () => {
    stubFetch(true);
    renderHome();
    expect(await screen.findByTestId("dashboard-empty")).toBeDefined();
    expect(screen.getByText("İlk botunu kur")).toBeDefined();
    expect(screen.getByRole("link", { name: "Bot kur" })).toHaveProperty(
      "href",
      expect.stringContaining("/bots/new"),
    );
    expect(screen.getByRole("link", { name: "Önce backtest et" })).toHaveProperty(
      "href",
      expect.stringContaining("/backtest"),
    );
    vi.unstubAllGlobals();
  });

  it("veriyle KPI + grafik + kırılımları gösterir", async () => {
    stubFetch(false);
    renderHome();
    expect(await screen.findByTestId("dashboard-kpis")).toBeDefined();
    expect(screen.getByText("4.998,51547241 USDT")).toBeDefined();
    expect(screen.getByText("Özsermaye")).toBeDefined();
    expect(screen.getByTestId("dashboard-equity")).toBeDefined();
    expect(screen.getByText("Günlük kâr")).toBeDefined();
    expect(screen.getByText("Bot bazında kâr")).toBeDefined();
    expect(screen.getByText("Parite bazında kâr")).toBeDefined();
    expect(screen.getByText("Aktif deal'ler")).toBeDefined();
    vi.unstubAllGlobals();
  });
});
