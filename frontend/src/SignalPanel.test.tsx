import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  SignalPanel,
  type SignalCandidateView,
  type SignalReadinessView,
} from "./SignalPanel";

const readiness: SignalReadinessView = { signal_id: "s1", status: "READY" };
const candidate: SignalCandidateView = {
  candidate_id: "c".repeat(64),
  signal_id: "s1",
  side: "BUY",
  qty: "0.01",
  expires_us: 1700000060000000,
};

function renderPanel(overrides = {}) {
  const handlers = { onHash: vi.fn(), onAssess: vi.fn(), onBind: vi.fn(), ...overrides };
  render(
    <SignalPanel
      payloadHash={"a".repeat(64)}
      readiness={readiness}
      candidate={candidate}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("SignalPanel", () => {
  it("hash, readiness ve adayı gösterir", () => {
    renderPanel();
    expect(screen.getByText(/a{64}/)).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();
    expect(screen.getByText("c".repeat(64))).toBeInTheDocument();
    expect(screen.getByText(/emir yetkisi yok/)).toBeInTheDocument();
  });

  it("hash ve assess akışı typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Yük (JSON)"), {
      target: { value: '{"action":"BUY"}' },
    });
    fireEvent.click(screen.getByRole("button", { name: /Hash üret/ }));
    expect(handlers.onHash).toHaveBeenCalledWith({ action: "BUY" });
    fireEvent.change(screen.getByLabelText("Signal ID"), { target: { value: "s1" } });
    fireEvent.click(screen.getByRole("button", { name: /Readiness ölç/ }));
    expect(handlers.onAssess).toHaveBeenCalledWith(
      expect.objectContaining({ signal: expect.objectContaining({ signal_id: "s1" }) }),
    );
  });

  it("bind akışı aday parametrelerini taşır", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Aksiyon"), { target: { value: "BUY" } });
    fireEvent.change(screen.getByLabelText("Sembol"), { target: { value: "BTCUSDT" } });
    fireEvent.change(screen.getByLabelText("Miktar"), { target: { value: "0.01" } });
    fireEvent.click(screen.getByRole("button", { name: /Aday bağla/ }));
    expect(handlers.onBind).toHaveBeenCalledWith(
      expect.objectContaining({ action: "BUY", symbol: "BTCUSDT", qty: "0.01" }),
    );
  });
});
