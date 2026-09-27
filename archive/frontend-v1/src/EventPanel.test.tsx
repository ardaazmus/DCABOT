import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  EventPanel,
  type CenterEventView,
} from "./EventPanel";

const events: CenterEventView[] = [
  { seq: 2, kind: "DEAL_EVENT", ref: "deal-1", summary: "START", time_us: 200 },
  { seq: 1, kind: "DEAL_CREATED", ref: "deal-1", summary: "created", time_us: 100 },
];

describe("EventPanel", () => {
  it("olayları gösterir", () => {
    render(<EventPanel events={events} busy={false} error="" onRefresh={vi.fn()} />);
    expect(screen.getByText(/#2 DEAL_EVENT/)).toBeInTheDocument();
    expect(screen.getByText(/Yerel kanal/)).toBeInTheDocument();
  });

  it("yenileme handler çağırır", () => {
    const onRefresh = vi.fn();
    render(<EventPanel events={[]} busy={false} error="" onRefresh={onRefresh} />);
    fireEvent.click(screen.getByRole("button", { name: /Olayları yenile/ }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
