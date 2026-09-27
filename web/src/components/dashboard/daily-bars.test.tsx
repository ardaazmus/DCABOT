import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import tr from "@/messages/tr.json";
import { DailyBars } from "./daily-bars";

describe("günlük kâr çubukları", () => {
  it("artı/eksi günleri ham metinle gösterir", () => {
    render(
      <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
        <DailyBars
          rows={[
            { day_start_us: Date.UTC(2026, 8, 10) * 1000, profit: "10.5" },
            { day_start_us: Date.UTC(2026, 8, 11) * 1000, profit: "0" },
            { day_start_us: Date.UTC(2026, 8, 12) * 1000, profit: "-2.25" },
          ]}
        />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Günlük kâr")).toBeDefined();
    expect(screen.getByText("10 Eyl")).toBeDefined();
    expect(screen.getByText("12 Eyl")).toBeDefined();
    expect(screen.getByText("+10,5")).toBeDefined();
    expect(screen.getByText("-2,25")).toBeDefined();
  });

  it("boş satırda hiçbir şey çizmez", () => {
    const { container } = render(
      <NextIntlClientProvider locale="tr" messages={tr}>
        <DailyBars rows={[]} />
      </NextIntlClientProvider>,
    );
    expect(container.textContent).toBe("");
  });
});
