import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import type { Bot } from "@/lib/api/schemas";
import { GridBotDetail } from "./grid-bot-detail";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const GRID_BOT = {
  bot_id: "bot_grid1",
  name: "Grid test",
  type: "GRID",
  mode: "PAPER",
  status: "RUNNING",
  status_reason: null,
  symbol: "BTCUSDT",
  budget: "900",
  strategy: {
    symbol: "BTCUSDT",
    mode: "ARITHMETIC",
    lower_price: "80000",
    upper_price: "89000",
    interval_count: 9,
    fee_rate: "0.001",
    stop_loss_price: null,
    take_profit_pct: null,
    trailing_up_pct: null,
    trailing_down_pct: null,
  },
  revision: 2,
  created_at_us: 1,
  updated_at_us: 2,
  archived: false,
} as unknown as Bot;

const GRID_STATE = {
  grid_status: "ACTIVE",
  entry_price: "81250",
  last_price: "81200",
  levels: ["80000", "81000", "82000"],
  pending: ["SELL", "SELL"],
  locked_quote: ["0", "0"],
  locked_base: ["0.00125", "0.00123"],
  quote_reserve: "0.5",
  base_free: "0",
  cycles_closed: 1,
  realized_profit_quote: "-798.25",
  fees_paid_quote: "0.9",
  equity_at_last: "901.5",
  fills_recent: [{ fill_id: "grid:9", side: "SELL", price: "81000", base_quantity: "0.00125" }],
  trailing_shifts: 0,
  last_bar_open_us: 1,
  updated_at_us: 2,
};

const FUTURES_BOT = {
  ...GRID_BOT,
  bot_id: "bot_fgrid1",
  name: "Futures grid test",
  type: "FUTURES_GRID",
  strategy: { ...GRID_BOT.strategy, direction: "SHORT", leverage: 3 },
} as unknown as Bot;

const FUTURES_STATE = {
  grid_status: "ACTIVE",
  direction: "SHORT",
  leverage: 3,
  entry_price: "84500",
  last_price: "84400",
  levels: ["80000", "84500", "89000"],
  pending: ["BUY", "BUY"],
  locked_margin: ["0", "20"],
  wallet_free: "860",
  open_lots: [{ interval: 1, quantity: "0.001", entry_price: "84500", locked_margin: "16.9" }],
  cycles_closed: 2,
  realized_gross_pnl: "5",
  fees_paid_quote: "0.9",
  funding_cashflow: "-0.01",
  funding_events_count: 1,
  equity_at_last: "904",
  fills_recent: [{ fill_id: "fgrid:3", side: "BUY", price: "84400", quantity: "0.001" }],
  trailing_shifts: 0,
  liq_estimate_price: null,
  liq_estimate_tier: null,
  last_bar_open_us: 1,
  updated_at_us: 2,
};

function stubFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string | URL | Request) => {
      const href = String(url);
      const body = href.includes("/grid") ? { data: GRID_STATE } : { data: [] };
      return { ok: true, status: 200, json: async () => body } as Response;
    }),
  );
}

function stubFuturesFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string | URL | Request) => {
      const href = String(url);
      const body = href.includes("/grid") ? { data: FUTURES_STATE } : { data: [] };
      return { ok: true, status: 200, json: async () => body } as Response;
    }),
  );
}

function renderDetail(bot: Bot = GRID_BOT) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <QueryClientProvider client={queryClient}>
        <GridBotDetail bot={bot} />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

describe("GridBotDetail", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("strateji, seviyeler ve dolgular listelenir", async () => {
    stubFetch();
    renderDetail();
    expect(await screen.findByTestId("grid-levels")).toBeInTheDocument();
    expect(screen.getByText("80000 USDT", { exact: false })).toBeInTheDocument();
    expect(screen.getByTestId("grid-fills")).toHaveTextContent("grid:9");
    expect(screen.getByText("Grid", { exact: true })).toBeInTheDocument();
  });

  it("futures yön, kaldıraç, fonlama ve lotları gösterir", async () => {
    stubFuturesFetch();
    renderDetail(FUTURES_BOT);
    expect(await screen.findByTestId("grid-levels")).toBeInTheDocument();
    expect(screen.getByText("Vadeli Grid", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("SHORT · 3x")).toBeInTheDocument();
    expect(screen.getByTestId("grid-fills")).toHaveTextContent("fgrid:3");
  });

  it("durum hatası yükleme iletisi gösterir", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 500, json: async () => ({}) }) as Response),
    );
    renderDetail();
    expect(await screen.findAllByRole("alert")).not.toHaveLength(0);
  });
});
