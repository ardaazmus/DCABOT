import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BotDetailView } from "./BotDetailView";
import {
  isBotDcaDealCountResponse,
  isBotDcaPerformanceResponse,
  type BotDcaPerformanceView,
  type BotProfileView,
} from "./BotPanel";

const PROFILE: BotProfileView = {
  bot_id: "bot-1",
  name: "Alpha",
  pairs: ["BTCUSDT", "ETHUSDT"],
  blacklist: ["LUNAUSDT"],
  favorites: [],
  virtual_quote_budget: "10000",
};

const PERFORMANCE: BotDcaPerformanceView = {
  bot_id: "bot-1",
  deal_count: 5,
  completed_deal_count: 4,
  win_count: 3,
  win_rate: "0.75",
  total_realized_net: "12.5",
  max_drawdown: "30",
};

function renderDetail(overrides: Partial<Parameters<typeof BotDetailView>[0]> = {}) {
  const onBack = vi.fn();
  const onSelectBot = vi.fn();
  const onRefreshDca = vi.fn();
  const result = render(
    <BotDetailView
      botId="bot-1"
      profile={PROFILE}
      botIds={["bot-1", "bot-2"]}
      sessionCount={2}
      draftParams={{ safetyQty: "0.002", safetyCount: "3", deviation: "0.02" }}
      loading={false}
      renderChart={() => <div data-testid="chart-stub" />}
      overlayNote={null}
      liquidation={null}
      liquidationBusy={false}
      liquidationError=""
      onRefreshLiquidation={() => {}}
      dcaPerformance={PERFORMANCE}
      dcaActiveDeals={1}
      dcaBusy={false}
      dcaError=""
      onRefreshDca={onRefreshDca}
      onBack={onBack}
      onSelectBot={onSelectBot}
      {...overrides}
    />,
  );
  return { onBack, onSelectBot, onRefreshDca, ...result };
}

describe("BotDetailView (Faz 17 A.4)", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("başlık + rozetler + istatistikler + ayarlar + grafik gösterir", () => {
    renderDetail();
    expect(screen.getByRole("heading", { name: "bot-1 · Alpha" })).toBeInTheDocument();
    expect(screen.getByText("2 pair")).toBeInTheDocument();
    expect(screen.getByText("2 session")).toBeInTheDocument();
    expect(screen.getByText("10000 USDT")).toBeInTheDocument();
    expect(screen.getByText("0.002 × 3 @ 0.02")).toBeInTheDocument();
    expect(screen.getByText("BTCUSDT, ETHUSDT")).toBeInTheDocument();
    expect(screen.getByTestId("chart-stub")).toBeInTheDocument();
  });

  it("tip rozeti istemci taslağından okunur, yoksa çıkarılmaz", () => {
    window.localStorage.setItem("dcabot-strategy-draft:bot-1", JSON.stringify({ botType: "DCA" }));
    const { unmount } = renderDetail();
    expect(screen.getAllByText("DCA")).toHaveLength(2);
    unmount();
    window.localStorage.clear();
    renderDetail();
    expect(screen.queryAllByText("DCA")).toHaveLength(0);
  });

  it("hızlı geçiş şeridi diğer botlara geçirir, aktif çip kapalıdır", () => {
    const { onSelectBot } = renderDetail();
    const bar = screen.getByRole("group", { name: "Diğer botlar" });
    expect(bar).toHaveClass("chipbar");
    const active = screen.getByRole("button", { name: "bot-1" });
    expect(active).toHaveAttribute("aria-pressed", "true");
    expect(active).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "bot-2" }));
    expect(onSelectBot).toHaveBeenCalledWith("bot-2");
  });

  it("yükleme sırasında çipler kilitlenir, yükleme notu çıkar", () => {
    renderDetail({ profile: null, loading: true });
    expect(screen.getByText("Bot yükleniyor…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "bot-2" })).toBeDisabled();
    expect(screen.getByTestId("chart-stub")).toBeInTheDocument();
  });

  it("profil alınamazsa dürüst hata gösterir", () => {
    renderDetail({ profile: null, loading: false });
    expect(screen.getByText("Bot profili alınamadı.")).toBeInTheDocument();
  });

  it("geri düğmesi ve overlay notu", () => {
    const { onBack } = renderDetail({ overlayNote: "Seviye önizlemesi alınamadı" });
    expect(screen.getByText("Seviye önizlemesi alınamadı")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "← Botlar" }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("bot listesi boşsa şerit çıkmaz, taslak yoksa tire kalır", () => {
    renderDetail({ botIds: [], draftParams: null });
    expect(screen.queryByRole("group", { name: "Diğer botlar" })).not.toBeInTheDocument();
    expect(screen.getByText("Güvenlik emri (taslak)")).toBeInTheDocument();
  });
});

describe("BotDetailView DCA-performansı (AA.3a)", () => {
  it("7 istatistiği aynen dizer, yenile iletilir", () => {
    const { onRefreshDca } = renderDetail();
    expect(screen.getByText("Oturum toplamları")).toBeInTheDocument();
    expect(screen.getByText("0.75")).toBeInTheDocument();
    expect(screen.getByText("12.5")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "DCA toplamlarını yenile" }));
    expect(onRefreshDca).toHaveBeenCalledTimes(1);
  });

  it("oran-yok + hata + meşgul durumları", () => {
    const { unmount } = renderDetail({ dcaPerformance: { ...PERFORMANCE, win_rate: null }, dcaActiveDeals: null });
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(2);
    unmount();
    const second = renderDetail({ dcaPerformance: null, dcaError: "okunamadı" });
    expect(screen.getByRole("alert")).toHaveTextContent("okunamadı");
    second.unmount();
    renderDetail({ dcaPerformance: null, dcaBusy: true });
    expect(screen.getByRole("button", { name: "DCA toplamlarını yenile" })).toBeDisabled();
    expect(screen.getByText("Okunuyor…")).toBeInTheDocument();
  });

  it("guard sözleşmeleri (deal-count + performance)", () => {
    expect(isBotDcaDealCountResponse({ data: { bot_id: "b", total: 2, active: 1, completed: 1 } })).toBe(true);
    expect(isBotDcaDealCountResponse({ data: { bot_id: "b", total: 2, active: 1 } })).toBe(false);
    expect(isBotDcaDealCountResponse({ data: { bot_id: "b", total: 2.5, active: 1, completed: 1 } })).toBe(false);
    expect(isBotDcaPerformanceResponse({ data: PERFORMANCE })).toBe(true);
    expect(isBotDcaPerformanceResponse({ data: { ...PERFORMANCE, win_rate: null } })).toBe(true);
    expect(isBotDcaPerformanceResponse({ data: { ...PERFORMANCE, win_rate: 0.75 } })).toBe(false);
    expect(isBotDcaPerformanceResponse({ data: { ...PERFORMANCE, total_realized_net: 12.5 } })).toBe(false);
    expect(isBotDcaPerformanceResponse({})).toBe(false);
  });
});
