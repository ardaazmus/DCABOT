import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BotContextHeader, BotTable, type BotTableRow } from "./BotTable";

const rows: BotTableRow[] = [
  { botId: "bot-1", name: "Grid Alpha", sessionCount: 2, selected: true },
  { botId: "bot-2", name: null, sessionCount: null, selected: false },
];

describe("BotTable", () => {
  it("satırları ve bilinmeyen alanları dürüst gösterir", () => {
    render(<BotTable rows={rows} busy={false} onSelect={() => {}} onCreate={() => {}} onOpenHistory={() => {}} />);
    expect(screen.getByText("bot-1")).toBeInTheDocument();
    expect(screen.getByText("Grid Alpha")).toBeInTheDocument();
    expect(screen.getByText("Seçili")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("filtre kimliğe göre daraltır", () => {
    render(<BotTable rows={rows} busy={false} onSelect={() => {}} onCreate={() => {}} onOpenHistory={() => {}} />);
    fireEvent.change(screen.getByLabelText("Filtre (bot kimliği)"), { target: { value: "bot-2" } });
    expect(screen.queryByText("Grid Alpha")).not.toBeInTheDocument();
    expect(screen.getByText("bot-2")).toBeInTheDocument();
  });

  it("Yükle seçili olmayan satırda handler çağırır", () => {
    const onSelect = vi.fn();
    render(<BotTable rows={rows} busy={false} onSelect={onSelect} onCreate={() => {}} onOpenHistory={() => {}} />);
    const buttons = screen.getAllByRole("button", { name: "Yükle" });
    expect(buttons[0]).toBeDisabled();
    fireEvent.click(buttons[1]);
    expect(onSelect).toHaveBeenCalledWith("bot-2");
  });

  it("15.3: boş envanterde standart boş-durum + CTA gösterir", () => {
    const onCreate = vi.fn();
    render(<BotTable rows={[]} busy={false} onSelect={() => {}} onCreate={onCreate} onOpenHistory={() => {}} />);
    expect(screen.getByText("Aktif bot yok")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yeni bot oluştur" }));
    expect(onCreate).toHaveBeenCalledTimes(1);
  });

  it("15.3: Aktif/Geçmiş sekmeleri; geçmişte satır uydurulmaz", () => {
    const onOpenHistory = vi.fn();
    render(<BotTable rows={rows} busy={false} onSelect={() => {}} onCreate={() => {}} onOpenHistory={onOpenHistory} />);
    expect(screen.getByRole("tab", { name: "Aktif botlar" })).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("tab", { name: "Geçmiş" }));
    expect(screen.queryByText("bot-1")).not.toBeInTheDocument();
    expect(screen.getByText(/Olaylar & Denetim/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Geçmişi aç" }));
    expect(onOpenHistory).toHaveBeenCalledTimes(1);
  });

  it("15.3: tip filtresi taslak türüne göre daraltır", () => {
    window.localStorage.setItem("dcabot-strategy-draft:bot-1", JSON.stringify({ botType: "GRID" }));
    window.localStorage.setItem("dcabot-strategy-draft:bot-2", JSON.stringify({ botType: "DCA" }));
    render(<BotTable rows={rows} busy={false} onSelect={() => {}} onCreate={() => {}} onOpenHistory={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Grid" }));
    expect(screen.getByText("bot-1")).toBeInTheDocument();
    expect(screen.queryByText("bot-2")).not.toBeInTheDocument();
    window.localStorage.clear();
  });
});

describe("BotContextHeader", () => {
  it("profilsiz durumda seçim ister", () => {
    render(<BotContextHeader profile={null} sessionCount={0} />);
    expect(screen.getByText("bot seçili değil")).toBeInTheDocument();
    expect(screen.getByText(/tablodan bir bot yükleyin/)).toBeInTheDocument();
  });

  it("profil + sayaç + sekmeleri gösterir", () => {
    render(
      <BotContextHeader
        profile={{ bot_id: "bot-1", name: "Grid Alpha", pairs: ["BTCUSDT"], blacklist: [], favorites: [], virtual_quote_budget: "10000" }}
        sessionCount={2}
      />,
    );
    expect(screen.getByText("bot-1 · Grid Alpha")).toBeInTheDocument();
    expect(screen.getByText("10000 USDT")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Kayıt" })).toHaveAttribute("href", "#bot-register");
    expect(screen.getByRole("link", { name: "Listeler" })).toHaveAttribute("href", "#bot-lists");
    expect(screen.getByRole("link", { name: "Session" })).toHaveAttribute("href", "#bot-sessions");
  });
});
