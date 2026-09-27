import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  isVenueLastPrice,
  isVenueSymbolList,
  SymbolSelector,
  type VenueSymbol,
} from "./SymbolSelector";

const SYMBOLS: VenueSymbol[] = [
  { symbol: "BTCUSDT", status: "TRADING", base_asset: "BTC", quote_asset: "USDT" },
  { symbol: "ETHUSDT", status: "TRADING", base_asset: "ETH", quote_asset: "USDT" },
  { symbol: "SOLUSDC", status: "BREAK", base_asset: "SOL", quote_asset: "USDC" },
];

function renderReady(overrides: Partial<Parameters<typeof SymbolSelector>[0]> = {}) {
  const onSelect = vi.fn();
  const onRetry = vi.fn();
  render(
    <SymbolSelector
      symbols={SYMBOLS}
      count={SYMBOLS.length}
      status="ready"
      error=""
      selectedSymbol="BTCUSDT"
      lastPrice={{ symbol: "BTCUSDT", price: "50000" }}
      priceStatus="ready"
      onSelect={onSelect}
      onRetry={onRetry}
      {...overrides}
    />,
  );
  return { onSelect, onRetry };
}

describe("SymbolSelector (Faz 17 A.1)", () => {
  it("seçili sembolü ve canlı fiyatı düğmede gösterir", () => {
    renderReady();
    const button = screen.getByRole("button", { expanded: false });
    expect(within(button).getByText("BTCUSDT")).toBeInTheDocument();
    expect(within(button).getByText("50000")).toBeInTheDocument();
  });

  it("açılır listede çift, parite ve venue statüsünü gösterir", () => {
    renderReady();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    const listbox = screen.getByRole("listbox", { name: /Borsa sembolleri/ });
    const options = within(listbox).getAllByRole("option");
    expect(options).toHaveLength(3);
    expect(within(listbox).getByText("SOL / USDC")).toBeInTheDocument();
    expect(within(listbox).getByText("BREAK")).toBeInTheDocument();
    expect(screen.getByText("3 çift listelendi · Binance spot")).toBeInTheDocument();
  });

  it("arama büyük/küçük harf duyarsız filtreler", () => {
    renderReady();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    fireEvent.change(screen.getByLabelText("Sembol ara"), { target: { value: "eth" } });
    const listbox = screen.getByRole("listbox", { name: /Borsa sembolleri/ });
    expect(within(listbox).getAllByRole("option")).toHaveLength(1);
    expect(within(listbox).getByText("ETHUSDT")).toBeInTheDocument();
    expect(screen.getByText("1 sonuç / 3 çift · Binance spot")).toBeInTheDocument();
  });

  it("arama sonuç vermezse dürüstçe boş gösterir", () => {
    renderReady();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    fireEvent.change(screen.getByLabelText("Sembol ara"), { target: { value: "ZZZ" } });
    expect(screen.getByText("Sonuç yok.")).toBeInTheDocument();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("Enter ilk eşleşmeyi seçer ve kapatır", () => {
    const { onSelect } = renderReady();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    fireEvent.change(screen.getByLabelText("Sembol ara"), { target: { value: "sol" } });
    fireEvent.keyDown(screen.getByLabelText("Sembol ara"), { key: "Enter" });
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith("SOLUSDC");
    expect(screen.getByRole("button", { expanded: false })).toBeInTheDocument();
  });

  it("satır tıklaması seçer ve kapatır", () => {
    const { onSelect } = renderReady();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    fireEvent.click(screen.getByRole("option", { name: /ETHUSDT/ }));
    expect(onSelect).toHaveBeenCalledWith("ETHUSDT");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("Escape seçim yapmadan kapatır", () => {
    const { onSelect } = renderReady();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    fireEvent.keyDown(screen.getByLabelText("Sembol ara"), { key: "Escape" });
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("hata durumunda mesaj ve tekrar düğmesi gösterir", () => {
    const { onRetry } = renderReady({ status: "error", error: "Upstream kapalı.", symbols: [], count: 0 });
    expect(screen.getByRole("alert")).toHaveTextContent("Upstream kapalı.");
    fireEvent.click(screen.getByRole("button", { name: /Tekrar dene/ }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("fiyat alınamazsa listeyi engellemez, not düşer", () => {
    renderReady({ lastPrice: null, priceStatus: "error" });
    expect(screen.getByText(/canlı fiyat alınamadı/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    expect(screen.getByRole("listbox", { name: /Borsa sembolleri/ })).toBeInTheDocument();
  });

  it("sözleşme muhafızları eksik/yanlış gövdeyi reddeder", () => {
    expect(isVenueSymbolList({
      environment: "BINANCE_SPOT",
      symbols: [{ symbol: "BTCUSDT", status: "TRADING", base_asset: "BTC", quote_asset: "USDT" }],
      count: 1,
      observed_at_us: 1,
      read_only: true,
      credential_required: false,
    })).toBe(true);
    expect(isVenueSymbolList({ environment: "BINANCE_SPOT", symbols: [], count: 0 })).toBe(false);
    expect(isVenueSymbolList({
      environment: "BINANCE_SPOT",
      symbols: [{ symbol: "BTCUSDT", status: "TRADING" }],
      count: 1,
      observed_at_us: 1,
      read_only: true,
      credential_required: false,
    })).toBe(false);
    expect(isVenueLastPrice({
      environment: "BINANCE_SPOT",
      symbol: "BTCUSDT",
      price: "50000",
      event_id: "1",
      event_time_us: 1,
      read_only: true,
      credential_required: false,
    })).toBe(true);
    expect(isVenueLastPrice({ symbol: "BTCUSDT", price: 50000 })).toBe(false);
  });
});
