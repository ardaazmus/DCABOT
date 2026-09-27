import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { GlobalSymbolSelect } from "./GlobalSymbolSelect";

const SYMBOLS = [
  { symbol: "BTCUSDT", status: "TRADING", base_asset: "BTC", quote_asset: "USDT" },
  { symbol: "ETHUSDT", status: "TRADING", base_asset: "ETH", quote_asset: "USDT" },
];

function renderSelect(overrides: Record<string, unknown> = {}) {
  const onSelect = vi.fn();
  const onRetry = vi.fn();
  render(
    <GlobalSymbolSelect
      symbols={SYMBOLS}
      count={2}
      status="ready"
      error=""
      selectedSymbol="BTCUSDT"
      lastPrice={{ symbol: "BTCUSDT", price: "97123.40000000" }}
      priceStatus="ready"
      onSelect={onSelect}
      onRetry={onRetry}
      {...overrides}
    />,
  );
  return { onSelect, onRetry };
}

describe("GlobalSymbolSelect (AB.1)", () => {
  it("sembol + arama + fiyatı tek grupta gösterir", () => {
    renderSelect();
    expect(screen.getByRole("group", { name: "Global sembol" })).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "Sembol ara" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Global sembol seç" })).toHaveValue("BTCUSDT");
    expect(screen.getByLabelText("Son fiyat")).toHaveTextContent("97123.40000000");
  });

  it("arama listeyi süzer, seçim onSelect çağırır", () => {
    const { onSelect } = renderSelect();
    fireEvent.change(screen.getByRole("searchbox", { name: "Sembol ara" }), { target: { value: "eth" } });
    const combo = screen.getByRole("combobox", { name: "Global sembol seç" });
    expect(combo.querySelectorAll("option")).toHaveLength(1);
    fireEvent.change(combo, { target: { value: "ETHUSDT" } });
    expect(onSelect).toHaveBeenCalledWith("ETHUSDT");
  });

  it("tanımsız fiyat boş yazılır, 0 uydurulmaz", () => {
    renderSelect({ lastPrice: null, priceStatus: "idle" });
    expect(screen.getByLabelText("Son fiyat")).toHaveTextContent("");
  });

  it("liste hatasında yeniden-dene gösterir", () => {
    const { onRetry } = renderSelect({ status: "error", error: "ağ yok" });
    fireEvent.click(screen.getByRole("button", { name: "Tekrar dene" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
