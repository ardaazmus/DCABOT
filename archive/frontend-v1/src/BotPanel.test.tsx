import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  BotPanel,
  type BotCheckView,
  type BotProfileView,
} from "./BotPanel";

const profile: BotProfileView = {
  bot_id: "bot-1",
  name: "Grid Alpha",
  pairs: ["BTCUSDT", "ETHUSDT"],
  blacklist: ["LUNAUSDT"],
  favorites: ["BTCUSDT"],
  virtual_quote_budget: "10000",
};

const check: BotCheckView = {
  bot_id: "bot-1",
  symbol: "LUNAUSDT",
  verdict: "BLOCKED_BLACKLIST",
  reason: "blacklistte",
};

function renderPanel(overrides = {}) {
  const handlers = {
    onRegister: vi.fn(),
    onSelect: vi.fn(),
    onUpdateLists: vi.fn(),
    onBind: vi.fn(),
    onCheck: vi.fn(),
    onRefresh: vi.fn(),
    ...overrides,
  };
  render(
    <BotPanel
      botIds={["bot-1"]}
      profile={profile}
      sessions={{ "sess-1": "BTCUSDT" }}
      check={check}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("BotPanel", () => {
  it("profil, session ve pair kararını gösterir", () => {
    renderPanel();
    expect(screen.getByText(/Grid Alpha/)).toBeInTheDocument();
    expect(screen.getByText(/LUNAUSDT: BLOCKED_BLACKLIST/)).toBeInTheDocument();
    expect(screen.getByText(/yalnız bir botun olabilir/)).toBeInTheDocument();
  });

  it("kayıt ve bağlama typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-2" } });
    fireEvent.change(screen.getByLabelText("Pair listesi"), { target: { value: "BTCUSDT" } });
    fireEvent.click(screen.getByRole("button", { name: /Bot kaydet/ }));
    expect(handlers.onRegister).toHaveBeenCalledWith(
      expect.objectContaining({ bot_id: "bot-2", pairs: ["BTCUSDT"] }),
    );
    fireEvent.change(screen.getByLabelText("Session kimliği"), { target: { value: "sess-9" } });
    fireEvent.click(screen.getByRole("button", { name: /Session bağla/ }));
    expect(handlers.onBind).toHaveBeenCalledWith(
      expect.objectContaining({ session_id: "sess-9" }),
    );
  });

  it("liste, kontrol, seçim ve yenileme handler çağırır", () => {
    const handlers = renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /Listeleri güncelle/ }));
    fireEvent.click(screen.getByRole("button", { name: /Pair kontrolü/ }));
    fireEvent.click(screen.getByRole("button", { name: /Botu yükle/ }));
    fireEvent.click(screen.getByRole("button", { name: /Listeyi yenile/ }));
    expect(handlers.onUpdateLists).toHaveBeenCalledTimes(1);
    expect(handlers.onCheck).toHaveBeenCalledWith("BTCUSDT");
    expect(handlers.onSelect).toHaveBeenCalledWith("bot-1");
    expect(handlers.onRefresh).toHaveBeenCalledTimes(1);
  });
});
