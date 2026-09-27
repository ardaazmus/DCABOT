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

  it("AA.2a: 4 kart gerçek değerleri gösterir", () => {
    render(<DashboardPanel dashboard={dashboard} busy={false} error="" onRefresh={vi.fn()} />);
    const list = screen.getByRole("list", { name: "Portföy özeti kartları" });
    expect(list).toBeInTheDocument();
    expect(screen.getByText("Paper Nakit")).toBeInTheDocument();
    expect(screen.getByText("1 / 1")).toBeInTheDocument();
    expect(screen.getByText("2 / 1")).toBeInTheDocument();
    expect(screen.getByText("RUNNING: 2 · PAUSED: 1")).toBeInTheDocument();
  });

  it("AA.2a: değerleme kartları dürüst-boş notu taşır", () => {
    render(<DashboardPanel dashboard={dashboard} busy={false} error="" onRefresh={vi.fn()} />);
    expect(screen.getByRole("status")).toHaveTextContent("portföy-özet ucu bekleniyor (AA.-1)");
  });

  it("AA.2a: boş durum-dağılımı ve boş dashboard", () => {
    const empty: DashboardView = {
      ...dashboard,
      deals: { deals: 0, by_status: {} },
    };
    const { unmount } = render(<DashboardPanel dashboard={empty} busy={false} error="" onRefresh={vi.fn()} />);
    expect(screen.getByText("durum dağılımı yok")).toBeInTheDocument();
    unmount();
    render(<DashboardPanel dashboard={null} busy={false} error="" onRefresh={vi.fn()} />);
    expect(screen.queryByRole("list", { name: "Portföy özeti kartları" })).not.toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("yenileme handler çağırır", () => {
    const onRefresh = vi.fn();
    render(<DashboardPanel dashboard={null} busy={false} error="" onRefresh={onRefresh} />);
    fireEvent.click(screen.getByRole("button", { name: /Özeti yenile/ }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
