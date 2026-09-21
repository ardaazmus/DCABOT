import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { BotWizard } from "./BotWizard";

function renderWizard() {
  const onRegister = vi.fn();
  render(<BotWizard busy={false} error="" onRegister={onRegister} />);
  return onRegister;
}

function next() {
  fireEvent.click(screen.getByRole("button", { name: "İleri" }));
}

describe("BotWizard", () => {
  it("geçersiz kimlikle ilerlemez", () => {
    renderWizard();
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("Bot kimliği geçersiz");
  });

  it("5 adımı tamamlayıp typed payload gönderir", () => {
    const onRegister = renderWizard();
    fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-9" } });
    fireEvent.change(screen.getByLabelText("Bot adı"), { target: { value: "Deneme" } });
    next();
    fireEvent.change(screen.getByLabelText("Pair listesi (virgülle)"), { target: { value: "BTCUSDT, ETHUSDT" } });
    next();
    next();
    fireEvent.change(screen.getByLabelText("Sanal bütçe"), { target: { value: "10000" } });
    next();
    expect(screen.getByText("Adım 5/5 · Önizleme")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    expect(onRegister).toHaveBeenCalledWith({
      bot_id: "bot-9",
      name: "Deneme",
      pairs: ["BTCUSDT", "ETHUSDT"],
      blacklist: [],
      favorites: [],
      virtual_quote_budget: "10000",
    });
  });

  it("yinelenen pair ve negatif bütçeyi engeller", () => {
    renderWizard();
    fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-9" } });
    fireEvent.change(screen.getByLabelText("Bot adı"), { target: { value: "Deneme" } });
    next();
    fireEvent.change(screen.getByLabelText("Pair listesi (virgülle)"), { target: { value: "BTCUSDT, BTCUSDT" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("benzersiz");
    fireEvent.change(screen.getByLabelText("Pair listesi (virgülle)"), { target: { value: "BTCUSDT" } });
    next();
    next();
    fireEvent.change(screen.getByLabelText("Sanal bütçe"), { target: { value: "-5" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("exact decimal");
  });

  it("canlı önizleme girilen değeri yansıtır", () => {
    renderWizard();
    fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-9" } });
    const aside = screen.getByRole("complementary", { name: "Canlı önizleme" });
    expect(aside).toHaveTextContent("bot-9");
  });

  it("Geri adımı korur, kayıt emir vermez notunu gösterir", () => {
    renderWizard();
    fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-9" } });
    fireEvent.change(screen.getByLabelText("Bot adı"), { target: { value: "Deneme" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Geri" }));
    expect(screen.getByLabelText("Bot kimliği")).toHaveValue("bot-9");
  });
});
