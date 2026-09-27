import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import tr from "@/messages/tr.json";
import { KpiGrid } from "./kpi-grid";

describe("kontrol merkezi KPI kartları", () => {
  it("dört göstergeyi ham metinle gösterir", () => {
    render(
      <NextIntlClientProvider locale="tr" messages={tr}>
        <KpiGrid
          summary={{
            total_value: "3518.25",
            today_profit: "-2.25",
            active_bots: 2,
            deployed_capital: "1500",
          }}
        />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Toplam değer")).toBeDefined();
    expect(screen.getByText("3.518,25 USDT")).toBeDefined();
    expect(screen.getByText("Bugünkü kâr")).toBeDefined();
    expect(screen.getByText("Aktif bot")).toBeDefined();
    expect(screen.getByText("2")).toBeDefined();
    expect(screen.getByText("Bağlı sermaye")).toBeDefined();
  });
});
