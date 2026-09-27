import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import successFixture from "../../../tests/fixtures/api/backtest-btcusdt-1h-14d.json";
import tr from "@/messages/tr.json";
import { backtestEnvelopeSchema, type BacktestResult } from "@/lib/api/schemas";

import { KpiGrid } from "./kpi-grid";

const RESULT = backtestEnvelopeSchema.parse(successFixture).data;

function renderGrid(result: BacktestResult) {
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <KpiGrid result={result} />
    </NextIntlClientProvider>,
  );
}

describe("kpi ızgarası", () => {
  it("eski kayıtta Profit Factor çizgisi gösterir", () => {
    renderGrid(RESULT);
    expect(screen.getByText("Profit Factor")).toBeDefined();
    expect(screen.getByText("—")).toBeDefined();
  });

  it("oranı iki basamak kısaltır, tam değeri başlıkta taşır", () => {
    renderGrid({
      ...RESULT,
      summary: { ...RESULT.summary, profit_factor: "1.85673" },
    });
    const tile = screen.getByTitle("1.85673");
    expect(tile.textContent).toContain("1,86");
  });
});
