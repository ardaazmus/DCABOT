import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  TwoLegPanel,
  type TwoLegProjectionView,
} from "./TwoLegPanel";

const projection: TwoLegProjectionView = {
  state: "ONE_LEG_FILLED",
  leg_a_identity: {
    account_id: "acct-1",
    venue_profile: "BINANCE-SPOT",
    product_id: "BTCUSDT",
    symbol: "BTCUSDT",
    position_mode: "HEDGE",
    hedge_side: "LONG",
  },
  leg_b_identity: null,
  leg_a_quantity: "0.5",
  leg_b_quantity: "0",
  leg_a_status: "FULL",
  leg_b_status: "NONE",
  fills: [
    { fill_id: "f-a1", leg_id: "A", quantity: "0.5", fill_status: "FULL", event_time_us: 1000 },
  ],
};

function renderPanel(overrides = {}) {
  const handlers = {
    onStart: vi.fn(),
    onFill: vi.fn(),
    onRecovery: vi.fn(),
    onTimeout: vi.fn(),
    onReplay: vi.fn(),
    ...overrides,
  };
  render(
    <TwoLegPanel
      sessionId="sess-1"
      projection={projection}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("TwoLegPanel", () => {
  it("projeksiyon durum ve bacakları gösterir", () => {
    renderPanel();
    expect(screen.getByText("ONE_LEG_FILLED")).toBeInTheDocument();
    expect(screen.getByText(/sentetik bacak üretilmez/)).toBeInTheDocument();
  });

  it("start ve fill gönderimleri typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Session kimliği"), { target: { value: "sess-9" } });
    fireEvent.click(screen.getByRole("button", { name: /Session başlat/ }));
    expect(handlers.onStart).toHaveBeenCalledWith("sess-9");
    fireEvent.change(screen.getByLabelText("Fill kimliği"), { target: { value: "f-a2" } });
    fireEvent.change(screen.getByLabelText("Miktar"), { target: { value: "1.25" } });
    fireEvent.click(screen.getByRole("button", { name: /Fill kabul et/ }));
    expect(handlers.onFill).toHaveBeenCalledWith(
      expect.objectContaining({ fill_id: "f-a2", quantity: "1.25", leg_id: "A" }),
    );
  });

  it("terminal ve replay düğmeleri handler çağırır", () => {
    const handlers = renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /Recovery işaretle/ }));
    fireEvent.click(screen.getByRole("button", { name: /Timeout işaretle/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Replay$/ }));
    expect(handlers.onRecovery).toHaveBeenCalledTimes(1);
    expect(handlers.onTimeout).toHaveBeenCalledTimes(1);
    expect(handlers.onReplay).toHaveBeenCalledTimes(1);
  });
});
