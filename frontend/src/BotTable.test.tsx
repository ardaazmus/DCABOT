import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BotContextHeader, BotTable, type BotTableRow } from "./BotTable";

const rows: BotTableRow[] = [
  { botId: "bot-1", name: "Grid Alpha", sessionCount: 2, selected: true },
  { botId: "bot-2", name: null, sessionCount: null, selected: false },
];

describe("BotTable", () => {
  it("satırları ve bilinmeyen alanları dürüst gösterir", () => {
    render(<BotTable rows={rows} busy={false} onSelect={() => {}} />);
    expect(screen.getByText("bot-1")).toBeInTheDocument();
    expect(screen.getByText("Grid Alpha")).toBeInTheDocument();
    expect(screen.getByText("Seçili")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("filtre kimliğe göre daraltır", () => {
    render(<BotTable rows={rows} busy={false} onSelect={() => {}} />);
    fireEvent.change(screen.getByLabelText("Filtre (bot kimliği)"), { target: { value: "bot-2" } });
    expect(screen.queryByText("Grid Alpha")).not.toBeInTheDocument();
    expect(screen.getByText("bot-2")).toBeInTheDocument();
  });

  it("Yükle seçili olmayan satırda handler çağırır", () => {
    const onSelect = vi.fn();
    render(<BotTable rows={rows} busy={false} onSelect={onSelect} />);
    const buttons = screen.getAllByRole("button", { name: "Yükle" });
    expect(buttons[0]).toBeDisabled();
    fireEvent.click(buttons[1]);
    expect(onSelect).toHaveBeenCalledWith("bot-2");
  });

  it("boş envanterde yönlendirici mesaj gösterir", () => {
    render(<BotTable rows={[]} busy={false} onSelect={() => {}} />);
    expect(screen.getByText(/sihirbazla kaydedin/)).toBeInTheDocument();
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
