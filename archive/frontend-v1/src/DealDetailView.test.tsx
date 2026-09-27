import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DealDetailView } from "./DealDetailView";
import type { DealEventView, DealLifecycleView } from "./DealPanel";

const LIFECYCLE: DealLifecycleView = {
  deal_id: "deal-1",
  config_revision_id: "rev-1",
  status: "OPEN",
  event_sequence: 2,
};

const HISTORY: DealEventView[] = [
  { event_id: "event-1", deal_id: "deal-1", config_revision_id: "rev-1", event: "START", event_sequence: 1 },
  { event_id: "event-2", deal_id: "deal-1", config_revision_id: "rev-1", event: "FILL", event_sequence: 2 },
];

function renderDetail(overrides: Partial<Parameters<typeof DealDetailView>[0]> = {}) {
  const onBack = vi.fn();
  const onReplay = vi.fn();
  render(
    <DealDetailView
      dealId="deal-1"
      lifecycle={LIFECYCLE}
      history={HISTORY}
      replayVerified={false}
      busy={false}
      error=""
      onBack={onBack}
      onReplay={onReplay}
      {...overrides}
    />,
  );
  return { onBack, onReplay };
}

describe("DealDetailView (Faz 17 A.4)", () => {
  it("başlık + bilgi ızgarası + olay geçmişi gösterir", () => {
    renderDetail();
    expect(screen.getByRole("heading", { name: "deal-1" })).toBeInTheDocument();
    expect(screen.getAllByText("OPEN")).toHaveLength(2);
    expect(screen.getByText("2 olay")).toBeInTheDocument();
    expect(screen.getByText("START")).toBeInTheDocument();
    expect(screen.getByText("FILL")).toBeInTheDocument();
    expect(screen.getByText("event-2")).toBeInTheDocument();
  });

  it("UNKNOWN rozeti + replay rozeti + hata", () => {
    renderDetail({ lifecycle: { ...LIFECYCLE, status: "UNKNOWN" }, replayVerified: true, error: "Bağlantı koptu." });
    expect(screen.getByText("UNKNOWN — inceleniyor")).toBeInTheDocument();
    expect(screen.getByText("Replay Doğrulandı ✓")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Bağlantı koptu.");
  });

  it("geri + replay düğmeleri", () => {
    const { onBack, onReplay } = renderDetail();
    fireEvent.click(screen.getByRole("button", { name: "← Deal Desk" }));
    expect(onBack).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Replay" }));
    expect(onReplay).toHaveBeenCalledTimes(1);
  });

  it("boş geçmişte yönlendirme, yüklemede durum notu", () => {
    renderDetail({ history: [] });
    expect(screen.getByText(/Olay yok/)).toBeInTheDocument();
    renderDetail({ lifecycle: null, history: [], busy: true });
    expect(screen.getAllByText("Deal yükleniyor…").length).toBeGreaterThan(0);
  });

  it("lifecycle alınamazsa dürüst hata gösterir", () => {
    renderDetail({ lifecycle: null, history: [], busy: false });
    expect(screen.getByText("Deal lifecycle alınamadı.")).toBeInTheDocument();
  });
});
