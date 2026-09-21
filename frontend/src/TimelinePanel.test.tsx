import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  TimelinePanel,
  type TimelineFrameView,
} from "./TimelinePanel";

const frame: TimelineFrameView = {
  deal_id: "deal-1",
  step: 1,
  of: 2,
  lifecycle: {
    deal_id: "deal-1",
    config_revision_id: "rev-1",
    status: "RUNNING",
    event_sequence: 1,
  },
  event: {
    event_id: "e-1",
    deal_id: "deal-1",
    config_revision_id: "rev-1",
    event: "START",
    event_sequence: 1,
  },
};

describe("TimelinePanel", () => {
  it("çerçeveyi gösterir", () => {
    render(<TimelinePanel frame={frame} busy={false} error="" onSeek={vi.fn()} />);
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByText(/Geçmiş ledger değişmez/)).toBeInTheDocument();
  });

  it("geri/ileri/başar seek üretir", () => {
    const onSeek = vi.fn();
    render(<TimelinePanel frame={frame} busy={false} error="" onSeek={onSeek} />);
    fireEvent.click(screen.getByRole("button", { name: /Geri/ }));
    expect(onSeek).toHaveBeenCalledWith(0);
    fireEvent.click(screen.getByRole("button", { name: /İleri/ }));
    expect(onSeek).toHaveBeenCalledWith(2);
    fireEvent.click(screen.getByRole("button", { name: /Başa sar/ }));
    expect(onSeek).toHaveBeenCalledWith(0);
  });
});
