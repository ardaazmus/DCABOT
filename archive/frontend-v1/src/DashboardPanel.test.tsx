import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  DashboardPanel,
  type DashboardView,
} from "./DashboardPanel";

const dashboard: DashboardView = {
  paper: { sessions: 2, total_cash: "10000", positions: 1, open_orders: 1 },
  bots: { bots: 2, bound_sessions: 1 },
  deals: { deals: 3, by_status: { RUNNING: 2, PAUSED: 1 } },
  backups: { backups: 2 },
};

describe("DashboardPanel", () => {
  it("özet satırları gösterir", () => {
    render(<DashboardPanel dashboard={dashboard} busy={false} error="" onRefresh={vi.fn()} />);
    expect(screen.getByText("10000")).toBeInTheDocument();
    expect(screen.getByText(/Salt-okunur toplama/)).toBeInTheDocument();
  });

  it("yenileme handler çağırır", () => {
    const onRefresh = vi.fn();
    render(<DashboardPanel dashboard={null} busy={false} error="" onRefresh={onRefresh} />);
    fireEvent.click(screen.getByRole("button", { name: /Özeti yenile/ }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
