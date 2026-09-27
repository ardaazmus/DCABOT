import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import tr from "@/messages/tr.json";
import { MonthlyBars } from "./monthly-bars";

function renderBars() {
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <MonthlyBars
        rows={[
          { month: "2026-07", return_percent: "1.25", complete: true },
          { month: "2026-08", return_percent: "-0.30", complete: false },
        ]}
      />
    </NextIntlClientProvider>,
  );
}

describe("aylık getiri çubukları", () => {
  it("kısmi ay soluk + kısmi etiketi alır", () => {
    renderBars();
    expect(screen.getByText("kısmi")).toBeDefined();
    // Etiket ve yüzde yerelleşir, ham metin ipucundadır.
    expect(screen.getByText("Tem 2026")).toBeDefined();
    expect(screen.getByText("Ağu 2026")).toBeDefined();
    expect(screen.getByText("%1,25")).toBeDefined();
    const negative = screen.getByText("%-0,3");
    expect(negative.getAttribute("title")).toBe("-0.30");
  });

  it("tam ayda kısmi etiketi yoktur", () => {
    render(
      <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
        <MonthlyBars rows={[{ month: "2026-07", return_percent: "1.25", complete: true }]} />
      </NextIntlClientProvider>,
    );
    expect(screen.queryByText("kısmi")).toBeNull();
  });
});
