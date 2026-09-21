import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  RebalancePlanPanel,
  type RebalanceCandidateView,
  type RebalanceDisclosureView,
  type RebalancePlanView,
} from "./RebalancePlanPanel";

const plan: RebalancePlanView = {
  plan_id: "p".repeat(64),
  status: "DRAFT",
  gross_buy: "100",
  gross_sell: "100",
  trigger_policy: "DEVIATION_THRESHOLD",
};

const disclosure: RebalanceDisclosureView = {
  status: "READY",
  total_fee: "0.2",
  lines: [
    {
      asset: "BTC", side: "BUY", gross_delta: "100", fee: "0.1",
      qty: "0.002", quantized_qty: "0.002", remainder_qty: "0", status: "READY",
    },
  ],
};

const candidates: RebalanceCandidateView[] = [
  {
    candidate_id: "c".repeat(64), asset: "BTC", side: "BUY",
    qty: "0.002", status: "CANDIDATE",
  },
];

function renderPanel(overrides = {}) {
  const handlers = { onPlan: vi.fn(), onDisclose: vi.fn(), ...overrides };
  render(
    <RebalancePlanPanel
      plan={plan}
      disclosure={disclosure}
      candidates={candidates}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("RebalancePlanPanel", () => {
  it("plan, disclosure ve adayları gösterir", () => {
    renderPanel();
    expect(screen.getByText("p".repeat(64))).toBeInTheDocument();
    expect(screen.getAllByText("0.002").length).toBe(3);
    expect(screen.getByText("c".repeat(64))).toBeInTheDocument();
    expect(screen.getByText(/emir yetkisi yok/)).toBeInTheDocument();
  });

  it("eşik plan gönderimi typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Mevcut ağırlık"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Hedef ağırlık"), { target: { value: "0.6" } });
    fireEvent.change(screen.getByLabelText("Eşik"), { target: { value: "0.05" } });
    fireEvent.change(screen.getByLabelText("Özsermaye"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("Dağılım"), {
      target: { value: "BTC 0.6 500\nETH 0.4 500" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Planı üret/ }));
    expect(handlers.onPlan).toHaveBeenCalledWith({
      trigger: {
        policy: "threshold",
        current_weight: "0.5",
        target_weight: "0.6",
        threshold: "0.05",
      },
      projection: {
        valuation_asset: "USDT",
        total_equity: "1000",
        allocations: [
          ["BTC", "0.6", "500"],
          ["ETH", "0.4", "500"],
        ],
      },
    });
  });

  it("disclosure gönderimi planı gömer", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Fiyatlar"), { target: { value: "BTC 50000" } });
    fireEvent.change(screen.getByLabelText("Fee oranı"), { target: { value: "0.001" } });
    fireEvent.click(screen.getByRole("button", { name: /Disclosure hesapla/ }));
    expect(handlers.onDisclose).toHaveBeenCalledWith(
      expect.objectContaining({
        plan,
        fee_rate: "0.001",
        prices: [["BTC", "50000"]],
      }),
    );
  });
});
