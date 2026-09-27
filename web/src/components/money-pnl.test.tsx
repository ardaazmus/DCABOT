import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Money, NeutralPercent } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { parseDecimal } from "@/lib/decimal";
import tr from "@/messages/tr.json";

function renderWithIntl(children: React.ReactNode) {
  return render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      {children}
    </NextIntlClientProvider>,
  );
}

describe("Money", () => {
  it("pozitif tutarı Türkçe biçimde gösterir", () => {
    renderWithIntl(<Money value={parseDecimal("1234.5")} suffix="USDT" />);
    expect(screen.getByText("1.234,5 USDT")).toBeInTheDocument();
  });

  it("negatif tutarın eksi işaretini korur", () => {
    renderWithIntl(<Money value={parseDecimal("-3.25")} />);
    expect(screen.getByText("-3,25")).toBeInTheDocument();
  });

  it("sıfırı işaretsiz gösterir", () => {
    renderWithIntl(<Money value={parseDecimal("0")} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("tanımsız değeri em-dash gösterir", () => {
    renderWithIntl(<Money value={undefined} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("Pnl", () => {
  it("pozitif değer yeşil ve artı işaretlidir", () => {
    renderWithIntl(<Pnl value={parseDecimal("12.5")} suffix="USDT" />);
    const node = screen.getByText("+12,5 USDT");
    expect(node).toBeInTheDocument();
    expect(node.className).toContain("text-profit");
  });

  it("negatif değer kırmızı ve eksi işaretlidir", () => {
    renderWithIntl(<Pnl value={parseDecimal("-3.25")} suffix="USDT" />);
    const node = screen.getByText("-3,25 USDT");
    expect(node).toBeInTheDocument();
    expect(node.className).toContain("text-loss");
  });

  it("sıfır nötr renktedir ve işaret almaz", () => {
    renderWithIntl(<Pnl value={parseDecimal("0")} suffix="USDT" />);
    const node = screen.getByText("0 USDT");
    expect(node).toBeInTheDocument();
    expect(node.className).toContain("text-muted-foreground");
  });

  it("yüzde varyantı yüzde işaretiyle gösterir", () => {
    renderWithIntl(<Pnl value={parseDecimal("-1.1")} variant="percent" />);
    const node = screen.getByText("-%1,1");
    expect(node).toBeInTheDocument();
    expect(node.className).toContain("text-loss");
  });

  it("tanımsız değer em-dash gösterir", () => {
    renderWithIntl(<Pnl value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("NeutralPercent", () => {
  it("işaretsiz ve renksiz yüzdedir", () => {
    renderWithIntl(<NeutralPercent value={parseDecimal("1.5")} />);
    const node = screen.getByText("%1,5");
    expect(node).toBeInTheDocument();
    expect(node.className).not.toContain("text-profit");
    expect(node.className).not.toContain("text-loss");
  });

  it("eksi işareti soyulur, iki basamağa yuvarlanır", () => {
    renderWithIntl(<NeutralPercent value={parseDecimal("-14.8949")} />);
    expect(screen.getByText("%14,89")).toBeInTheDocument();
  });

  it("tanımsız değer em-dash gösterir", () => {
    renderWithIntl(<NeutralPercent value={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
