import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  PortfolioPanel,
  isPortfolioDcaPerformanceResponse,
  type PortfolioDcaPerformance,
} from "./PortfolioPanel";

const DATA: PortfolioDcaPerformance = {
  bot_count: 3,
  winning_bot_count: 2,
  total_realized_net: "10",
  bots: [
    { bot_id: "bot-1", realized_net: "12.5", share_of_total: "0.7" },
    { bot_id: "bot-2", realized_net: "2", share_of_total: "0.2" },
    { bot_id: "bot-3", realized_net: "-4.5", share_of_total: "-0.1" },
  ],
};

describe("PortfolioPanel", () => {
  it("AA.13b: özet + halka + tablo; negatif-pay halka-dışı", () => {
    const onRefresh = vi.fn();
    const { container } = render(<PortfolioPanel data={DATA} busy={false} error="" onRefresh={onRefresh} />);
    expect(screen.getByText("Portföy halkası")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "3 bot, toplam net 10" })).toBeInTheDocument();
    expect(container.querySelectorAll("svg.portfolio-ring path").length).toBe(2);
    expect(screen.getByText("-4.5")).toBeInTheDocument();
    expect(screen.getByText("-0.1")).toBeInTheDocument();
    expect(screen.getByText("1 bot halka-dışı (negatif/sıfır/tanımsız pay) — değerler tabloda aynen.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yenile" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("AA.13b: null-pay tire olur, sıfır yazılmaz", () => {
    render(
      <PortfolioPanel
        data={{ bot_count: 1, winning_bot_count: 0, total_realized_net: "0", bots: [{ bot_id: "bot-9", realized_net: "0", share_of_total: null }] }}
        busy={false}
        error=""
        onRefresh={vi.fn()}
      />,
    );
    expect(screen.getAllByText("0")).toHaveLength(3);
    expect(screen.getAllByText("—")).toHaveLength(1);
  });

  it("AA.13b: pozitif-toplam-1-aşımında halka çizilmez, tablo tamdır", () => {
    render(
      <PortfolioPanel
        data={{ bot_count: 2, winning_bot_count: 1, total_realized_net: "5", bots: [
          { bot_id: "bot-1", realized_net: "8", share_of_total: "0.9" },
          { bot_id: "bot-2", realized_net: "7", share_of_total: "0.8" },
        ] }}
        busy={false}
        error=""
        onRefresh={vi.fn()}
      />,
    );
    expect(screen.getByText("Pozitif-pay toplamı 1’i aştığı için halka çizilemedi (kayıplı botlar var) — tablo tamdır.")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("0.9")).toBeInTheDocument();
    expect(screen.getByText("0.8")).toBeInTheDocument();
  });

  it("AA.13b: botsuz + hata + meşgul durumları", () => {
    const { unmount } = render(
      <PortfolioPanel data={{ bot_count: 0, winning_bot_count: 0, total_realized_net: "3", bots: [] }} busy={false} error="" onRefresh={vi.fn()} />,
    );
    expect(screen.getByText("Bot-bağlantılı oturum yok — halka çizilemez (botsuz oturumlar toplama girer, halkaya girmez).")).toBeInTheDocument();
    unmount();
    const second = render(<PortfolioPanel data={null} busy={false} error="uç kapalı" onRefresh={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent("uç kapalı");
    second.unmount();
    render(<PortfolioPanel data={null} busy={true} error="" onRefresh={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Okunuyor…" })).toBeDisabled();
  });

  it("AA.13b: guard sözleşmesi", () => {
    expect(isPortfolioDcaPerformanceResponse({ data: DATA })).toBe(true);
    expect(isPortfolioDcaPerformanceResponse({ data: { ...DATA, bots: [{ bot_id: "b", realized_net: "1", share_of_total: 0.5 }] } })).toBe(false);
    expect(isPortfolioDcaPerformanceResponse({ data: { ...DATA, total_realized_net: 10 } })).toBe(false);
    expect(isPortfolioDcaPerformanceResponse({ data: { ...DATA, winning_bot_count: "2" } })).toBe(false);
    expect(isPortfolioDcaPerformanceResponse({})).toBe(false);
  });
});
