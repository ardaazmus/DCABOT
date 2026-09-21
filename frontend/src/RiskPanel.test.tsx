import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  RiskPanel,
  type RiskExplainView,
} from "./RiskPanel";

const explanation: RiskExplainView = {
  blocked: true,
  reasons: [
    { code: "PAIR_BLOCKED", severity: "BLOCKER", message: "Pair blacklistte." },
  ],
};

describe("RiskPanel", () => {
  it("engeli ve nedenleri gösterir", () => {
    render(<RiskPanel explanation={explanation} busy={false} error="" onExplain={vi.fn()} />);
    expect(screen.getByText("VAR")).toBeInTheDocument();
    expect(screen.getByText("Pair blacklistte.")).toBeInTheDocument();
    expect(screen.getByText(/hiçbir kararı değiştirmez/)).toBeInTheDocument();
  });

  it("açıklama isteği payload üretir", () => {
    const onExplain = vi.fn();
    render(<RiskPanel explanation={null} busy={false} error="" onExplain={onExplain} />);
    fireEvent.change(screen.getByLabelText("Bot (opsiyonel)"), { target: { value: "b1" } });
    fireEvent.change(screen.getByLabelText("Sembol (opsiyonel)"), { target: { value: "LUNAUSDT" } });
    fireEvent.click(screen.getByRole("button", { name: /Açıkla/ }));
    expect(onExplain).toHaveBeenCalledWith({ bot_id: "b1", symbol: "LUNAUSDT" });
  });
});
