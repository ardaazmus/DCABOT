import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import tr from "@/messages/tr.json";
import { ProfitSplits } from "./profit-splits";

describe("kâr kırılımları", () => {
  it("bot ve parite listelerini değerleriyle gösterir", () => {
    render(
      <NextIntlClientProvider locale="tr" messages={tr}>
        <ProfitSplits
          byBot={[
            { bot_id: "a", bot_name: "Alfa", profit: "8.25", deals_completed: 2 },
            { bot_id: "b", bot_name: "Beta", profit: "-1.5", deals_completed: 1 },
          ]}
          byPair={[{ symbol: "BTCUSDT", profit: "6.75", deals_completed: 3, bots: 2 }]}
        />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Bot bazında kâr")).toBeDefined();
    expect(screen.getByText("Parite bazında kâr")).toBeDefined();
    const alfa = screen.getByText("Alfa");
    expect(alfa.closest("a")?.getAttribute("href")).toBe("/bots/a");
    expect(screen.getByText("BTCUSDT")).toBeDefined();
    expect(screen.getByText("+8,25 USDT")).toBeDefined();
  });
});
