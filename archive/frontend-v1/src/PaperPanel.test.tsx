import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  PaperPanel,
  isPaperSnapshot,
  type PaperPrint,
  type PaperSnapshot,
} from "./PaperPanel";

const snapshot: PaperSnapshot = {
  session_id: "a".repeat(64),
  status: "PAPER_ACTIVE",
  cash: "10000",
  positions: [],
  orders: [
    {
      client_order_id: "c1", symbol: "BTCUSDT", side: "BUY",
      order_type: "MARKET", qty: "0.01", limit_price: null,
      filled_qty: "0", status: "SIMULATED_NEW",
    },
  ],
  fills: [],
  marks: [{ symbol: "BTCUSDT", price: "50000", event_id: "e1" }],
};

const prints: PaperPrint[] = [
  { event_id: "e1", symbol: "BTCUSDT", price: "50000", qty: "1" },
];

const draft = { symbol: "BTCUSDT", side: "BUY", qty: "0.01", clientOrderId: "c2" };

function renderPanel(overrides = {}) {
  const handlers = {
    onActivate: vi.fn(),
    onRefresh: vi.fn(),
    onOrderDraftChange: vi.fn(),
    onPlace: vi.fn(),
    onFill: vi.fn(),
    ...overrides,
  };
  render(
    <PaperPanel
      snapshot={snapshot}
      prints={prints}
      busy={false}
      error=""
      orderDraft={draft}
      {...handlers}
    />,
  );
  return handlers;
}

describe("isPaperSnapshot", () => {
  it("geçerli snapshotu kabul eder, sayı tipini reddeder", () => {
    expect(isPaperSnapshot(snapshot)).toBe(true);
    expect(isPaperSnapshot({ ...snapshot, cash: 10000 })).toBe(false);
    expect(isPaperSnapshot(null)).toBe(false);
  });
});

describe("PaperPanel", () => {
  it("nakit, pozisyon ve emirleri gösterir", () => {
    renderPanel();
    expect(screen.getByText(/10000/)).toBeInTheDocument();
    expect(screen.getByText("0.01")).toBeInTheDocument();
    expect(screen.getByText("SIMULATED_NEW")).toBeInTheDocument();
    expect(screen.getAllByText(/sanal para/).length).toBeGreaterThan(0);
  });

  it("yenile ve emir düğmeleri geri çağrıları tetikler", () => {
    const handlers = renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /Piyasayı yenile/ }));
    fireEvent.click(screen.getByRole("button", { name: /Sanal emir ver/ }));
    expect(handlers.onRefresh).toHaveBeenCalledTimes(1);
    expect(handlers.onPlace).toHaveBeenCalledTimes(1);
  });

  it("print satırındaki doldur düğmesi event id ile çağırır", () => {
    const handlers = renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /e1.*doldur/i }));
    expect(handlers.onFill).toHaveBeenCalledWith("c1", "e1");
  });

  it("snapshot yokken aktivasyon düğmesi gösterir", () => {
    const onActivate = vi.fn();
    render(
      <PaperPanel
        snapshot={null}
        prints={[]}
        busy={false}
        error=""
        orderDraft={draft}
        onActivate={onActivate}
        onRefresh={() => {}}
        onOrderDraftChange={() => {}}
        onPlace={() => {}}
        onFill={() => {}}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Paper session aç/ }));
    expect(onActivate).toHaveBeenCalledTimes(1);
  });
});
