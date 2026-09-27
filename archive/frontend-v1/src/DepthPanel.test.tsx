import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  DEPTH_LIMITS,
  DepthPanel,
  isDepthBookResponse,
  type DepthBook,
} from "./DepthPanel";

const book: DepthBook = {
  symbol: "BTCUSDT",
  last_update_id: 42,
  bids: [["90000", "0.5"]],
  asks: [["90010", "0.3"]],
  observed_at_us: 1750000000000000,
  read_only: true,
  credential_required: false,
};

describe("AA.14 order-book", () => {
  it("guard sözleşmesi", () => {
    expect(isDepthBookResponse({ data: book })).toBe(true);
    expect(isDepthBookResponse({ data: { ...book, bids: [["90000", 0.5]] } })).toBe(false);
    expect(isDepthBookResponse({ data: { ...book, asks: [] , last_update_id: "42"} })).toBe(false);
    expect(isDepthBookResponse({})).toBe(false);
  });

  it("limit kümesi sunucuyla birebir", () => {
    expect([...DEPTH_LIMITS]).toEqual([5, 10, 20, 50, 100, 500, 1000, 5000]);
  });

  it("seviyeler verbatim dizilir", () => {
    render(<DepthPanel book={book} initialSymbol="BTCUSDT" busy={false} error="" onLoad={() => {}} />);
    expect(screen.getByText("90000")).toBeInTheDocument();
    expect(screen.getByText("0.3")).toBeInTheDocument();
    expect(screen.getByText("salt-okunur · credentialsız")).toBeInTheDocument();
  });

  it("form sembol+limiti aynen iletir, bozuk sembol iletmez", () => {
    const onLoad = vi.fn();
    render(<DepthPanel book={null} initialSymbol="BTCUSDT" busy={false} error="" onLoad={onLoad} />);
    fireEvent.change(screen.getByLabelText("Seviye limiti"), { target: { value: "50" } });
    fireEvent.click(screen.getByRole("button", { name: "Derinliği getir" }));
    expect(onLoad).toHaveBeenCalledWith("BTCUSDT", 50);
    fireEvent.change(screen.getByLabelText("Sembol"), { target: { value: "btc usdt" } });
    fireEvent.click(screen.getByRole("button", { name: "Derinliği getir" }));
    expect(onLoad).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert")).toHaveTextContent("alfanumerik");
  });
});
