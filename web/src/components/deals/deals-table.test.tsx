import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import activeList from "../../../tests/fixtures/api/v2-deals-active.json";
import botJson from "../../../tests/fixtures/api/v2-bots-get.json";
import closedList from "../../../tests/fixtures/api/v2-deals-closed.json";
import openDetail from "../../../tests/fixtures/api/v2-deal-detail-open.json";
import tr from "@/messages/tr.json";
import { dealsEnvelopeSchema } from "@/lib/api/schemas";

import { DealsTable } from "./deals-table";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const ACTIVE = dealsEnvelopeSchema.parse(activeList).data;
const CLOSED = dealsEnvelopeSchema.parse(closedList).data;

function stubFetch(direction: "LONG" | "SHORT" = "LONG") {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      let body: unknown = botJson;
      if (url.includes("/deals/")) {
        body = openDetail;
      } else {
        const match = /\/api\/v2\/bots\/([^/?]+)$/.exec(url);
        if (match?.[1] !== undefined) {
          body = {
            data: {
              ...botJson.data,
              bot_id: decodeURIComponent(match[1]),
              strategy: { ...botJson.data.strategy, direction },
            },
          };
        }
      }
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
}

function renderTable(mode: "active" | "history") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <DealsTable rows={mode === "active" ? ACTIVE : CLOSED} mode={mode} testId="deals" />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("birleşik deal tablosu (gerçek fixture)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("aktif satırda canlı ekonomi ve SO ilerlemesi gösterir", async () => {
    stubFetch();
    renderTable("active");
    // Masaüstü tablosu + mobil kartı aynı satırı iki kez çizer.
    expect(await screen.findAllByText("BTCUSDT")).toHaveLength(2);
    expect(screen.getAllByText("W-F6 fixture")).toHaveLength(2);
    // TP 85841.93 TR biçimiyle (detay sorgusu beklenir).
    expect(await screen.findAllByText("85.841,93 USDT")).toHaveLength(2);
    expect(await screen.findAllByText("SO 0/6")).toHaveLength(2);
    const links = screen.getAllByRole("link", { name: "#1" });
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveProperty("href", expect.stringContaining("/deals/"));
  });

  it("geçmiş satırda kâr ve manuel rozeti gösterir", async () => {
    stubFetch();
    renderTable("history");
    expect(await screen.findAllByText("BTCUSDT")).toHaveLength(2);
    expect(screen.getAllByText("Manuel kapatma")).toHaveLength(2);
    expect(screen.getAllByText(/-0,1/)).toHaveLength(2);
  });

  it("yön rozeti bot stratejisinden gelir", async () => {
    stubFetch();
    renderTable("active");
    expect(await screen.findAllByText("Long")).toHaveLength(2);
  });

  it("SHORT botun satırı Short rozeti taşır", async () => {
    stubFetch("SHORT");
    renderTable("active");
    expect(await screen.findAllByText("Short")).toHaveLength(2);
  });

  it("boş listede davet gösterir", () => {
    stubFetch();
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
        <QueryClientProvider client={queryClient}>
          <DealsTable rows={[]} mode="active" testId="deals" />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Aktif deal yok")).toBeDefined();
  });
});
