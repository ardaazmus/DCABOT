import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  DealPanel,
  type DealEventView,
  type DealLifecycleView,
} from "./DealPanel";

const lifecycle: DealLifecycleView = {
  deal_id: "deal-1",
  config_revision_id: "rev-1",
  status: "PAUSED",
  event_sequence: 2,
};

const history: DealEventView[] = [
  { event_id: "event-1", deal_id: "deal-1", config_revision_id: "rev-1", event: "START", event_sequence: 1 },
  { event_id: "event-2", deal_id: "deal-1", config_revision_id: "rev-1", event: "PAUSE", event_sequence: 2 },
];

function renderPanel(overrides = {}) {
  const handlers = {
    onCreate: vi.fn(),
    onAppend: vi.fn(),
    onReplay: vi.fn(),
    onBulk: vi.fn(),
    ...overrides,
  };
  render(
    <DealPanel
      dealId="deal-1"
      lifecycle={lifecycle}
      history={history}
      bulkResults={[{ deal_id: "deal-1", event_id: "b-1", result: "ACCEPTED" }]}
      busy={false}
      error=""
      replayVerified={false}
      {...handlers}
    />,
  );
  return handlers;
}

describe("DealPanel", () => {
  it("durum, geçmiş ve toplu sonucu gösterir", () => {
    renderPanel();
    expect(screen.getByText("PAUSED")).toBeInTheDocument();
    expect(screen.getByText("ACCEPTED")).toBeInTheDocument();
    expect(screen.getByText(/atomik değildir/)).toBeInTheDocument();
  });

  it("açma ve olay typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Deal kimliği"), { target: { value: "deal-9" } });
    fireEvent.click(screen.getByRole("button", { name: /Deal aç/ }));
    expect(handlers.onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ deal_id: "deal-9" }),
    );
    fireEvent.change(screen.getByLabelText("Olay"), { target: { value: "PAUSE" } });
    fireEvent.change(screen.getByLabelText("Sıra"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: /Olay ekle/ }));
    expect(handlers.onAppend).toHaveBeenCalledWith(
      expect.objectContaining({ event: "PAUSE", event_sequence: 2 }),
    );
  });

  it("toplu gönderim deal başına aksiyon üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Deal listesi"), { target: { value: "deal-1, deal-2" } });
    fireEvent.click(screen.getByRole("button", { name: /Toplu gönder/ }));
    expect(handlers.onBulk).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ deal_id: "deal-1" }),
        expect.objectContaining({ deal_id: "deal-2" }),
      ]),
    );
    fireEvent.click(screen.getByRole("button", { name: /^Replay$/ }));
    expect(handlers.onReplay).toHaveBeenCalledTimes(1);
  });

  it("15.5: replay doğrulama rozeti yalnız replay sonrasında görünür", () => {
    renderPanel({ replayVerified: true });
    expect(screen.getByText("Replay Doğrulandı ✓")).toBeInTheDocument();
  });

  it("15.5: replay yapılmadıysa rozet görünmez", () => {
    renderPanel({ replayVerified: false });
    expect(screen.queryByText("Replay Doğrulandı ✓")).not.toBeInTheDocument();
  });

  it("15.5: UNKNOWN durum sarı rozet olur", () => {
    render(
      <DealPanel
        dealId="deal-1"
        lifecycle={{ ...lifecycle, status: "UNKNOWN" }}
        history={history}
        bulkResults={[]}
        busy={false}
        error=""
        replayVerified={false}
        onCreate={() => {}}
        onAppend={() => {}}
        onReplay={() => {}}
        onBulk={() => {}}
      />,
    );
    expect(screen.getByText("UNKNOWN — inceleniyor").className).toMatch(/badge-warn/);
  });
});
