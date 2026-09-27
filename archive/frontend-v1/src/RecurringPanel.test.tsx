import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  RecurringPanel,
  type RecurringScheduleView,
} from "./RecurringPanel";

const schedule: RecurringScheduleView = {
  symbol: "BTCUSDT",
  quote_amount: "100",
  start_us: 1000000,
  interval_us: 500000,
  count: 3,
  slots: [
    { index: 0, slot_us: 1000000 },
    { index: 1, slot_us: 1500000 },
    { index: 2, slot_us: 2000000 },
  ],
  total_quote: "300",
  order_authority: "NONE",
};

describe("RecurringPanel", () => {
  it("projeksiyonu gösterir", () => {
    render(<RecurringPanel schedule={schedule} busy={false} error="" onProject={vi.fn()} />);
    expect(screen.getByText("300")).toBeInTheDocument();
    expect(screen.getByText(/emir yetkisi yok/)).toBeInTheDocument();
  });

  it("projeksiyon typed payload üretir", () => {
    const onProject = vi.fn();
    render(<RecurringPanel schedule={null} busy={false} error="" onProject={onProject} />);
    fireEvent.change(screen.getByLabelText("Slot sayısı"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: /Takvimi projekte et/ }));
    expect(onProject).toHaveBeenCalledWith(
      expect.objectContaining({ symbol: "BTCUSDT", count: 5 }),
    );
  });
});
