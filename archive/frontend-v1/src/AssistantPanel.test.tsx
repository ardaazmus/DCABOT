import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AssistantPanel } from "./AssistantPanel";
import type { DashboardView } from "./DashboardPanel";
import type { CenterEventView } from "./EventPanel";
import type { CanaryStatusView } from "./RiskPanel";

const dashboard: DashboardView = {
  paper: { sessions: 2, total_cash: "1000", positions: 1, open_orders: 0 },
  bots: { bots: 3, bound_sessions: 1 },
  deals: { deals: 5, by_status: { OPEN: 2, CLOSED: 3 } },
  backups: { backups: 4 },
};

const events: CenterEventView[] = [
  { seq: 2, kind: "DEAL_EVENT", ref: "deal-1", summary: "START", time_us: 200 },
  { seq: 1, kind: "DEAL_CREATED", ref: "deal-1", summary: "created", time_us: 100 },
];

const canary: CanaryStatusView = {
  verdict: "PASS",
  reasons: [],
  kill_switch_engaged: false,
  approval_present: true,
  spec_status: "READY",
  paper_fill_count: 3,
  observed_at: "2026-09-23T12:00:00Z",
};

function renderPanel(overrides: Partial<Parameters<typeof AssistantPanel>[0]> = {}) {
  return render(
    <AssistantPanel
      dashboard={dashboard}
      dashboardError=""
      events={events}
      eventsError=""
      canary={canary}
      canaryError=""
      busy={false}
      onRefresh={vi.fn()}
      {...overrides}
    />,
  );
}

describe("AssistantPanel", () => {
  it("hiçbir soru seçilmeden boş-durum gösterir", () => {
    renderPanel();
    expect(screen.getByText(/Bir soru seçin/)).toBeInTheDocument();
  });

  it("durum-ne sorusu sunucu verisini aynen birleştirir", () => {
    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: "Durum ne?" }));
    expect(screen.getByText(/Bot: 3/)).toBeInTheDocument();
    expect(screen.getByText(/OPEN: 2/)).toBeInTheDocument();
    expect(screen.getByText(/canary: PASS/)).toBeInTheDocument();
  });

  it("canary-durumu sorusu kill-switch ve onay durumunu gösterir", () => {
    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: "Canary durumu?" }));
    expect(screen.getByText(/Kill-switch: kapalı/)).toBeInTheDocument();
    expect(screen.getByText(/Onay: var/)).toBeInTheDocument();
  });

  it("son-olaylar sorusu olayları listeler", () => {
    renderPanel();
    fireEvent.click(screen.getByRole("button", { name: "Son olaylar?" }));
    expect(screen.getByText(/#2 DEAL_EVENT/)).toBeInTheDocument();
  });

  it("kill-switch sorusu açık durumda uyarı metni verir", () => {
    renderPanel({ canary: { ...canary, kill_switch_engaged: true } });
    fireEvent.click(screen.getByRole("button", { name: "Kill-switch açık mı?" }));
    expect(screen.getByText(/Kill-switch AÇIK/)).toBeInTheDocument();
  });

  it("veri yokken dürüst-boş metin gösterir, uydurmaz", () => {
    renderPanel({ dashboard: null, dashboardError: "" });
    fireEvent.click(screen.getByRole("button", { name: "Durum ne?" }));
    expect(screen.getByText(/Özet henüz okunmadı/)).toBeInTheDocument();
  });

  it("hata varken hatayı gösterir", () => {
    renderPanel({ canary: null, canaryError: "bağlantı yok" });
    fireEvent.click(screen.getByRole("button", { name: "Canary durumu?" }));
    expect(screen.getByText(/Canary okunamadı: bağlantı yok/)).toBeInTheDocument();
  });

  it("yenile düğmesi handler çağırır", () => {
    const onRefresh = vi.fn();
    renderPanel({ onRefresh });
    fireEvent.click(screen.getByRole("button", { name: /Verileri yenile/ }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});
