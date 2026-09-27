import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import successFixture from "../../../tests/fixtures/api/backtest-btcusdt-1h-14d.json";
import tr from "@/messages/tr.json";
import { backtestEnvelopeSchema, type BacktestResult } from "@/lib/api/schemas";
import { StatusBand } from "./status-band";

const RESULT = backtestEnvelopeSchema.parse(successFixture).data;

function renderBand(result: BacktestResult) {
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <StatusBand result={result} />
    </NextIntlClientProvider>,
  );
}

describe("durum bandı", () => {
  it("COMPLETED durumunda yalnız kaynak rozeti vardır", () => {
    renderBand(RESULT);
    expect(screen.getByTestId("backtest-status")).toBeDefined();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("INDETERMINATE amber uyarı + tarih gösterir", () => {
    renderBand({ ...RESULT, status: "INDETERMINATE", indeterminate_at_us: 1788220800000000 });
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("aynı mumda hem safety order hem take profit");
    expect(alert.textContent).toContain("simülasyon burada durdu");
    expect(alert.className).toContain("text-safety");
  });

  it("veri kaynağı rozeti yanıttan gelir", () => {
    renderBand(RESULT);
    const source = RESULT.data_source === "CACHE" ? "Yerel önbellekten" : "Binance'ten indirildi";
    expect(screen.getByText(source)).toBeDefined();
  });
});
