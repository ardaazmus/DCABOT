import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  SignalPanel,
  type SignalCandidateView,
  type SignalReadinessView,
} from "./SignalPanel";

const readiness: SignalReadinessView = { signal_id: "s1", status: "READY" };
const candidate: SignalCandidateView = {
  candidate_id: "c".repeat(64),
  signal_id: "s1",
  side: "BUY",
  qty: "0.01",
  expires_us: 1700000060000000,
};

function renderPanel(overrides = {}) {
  const handlers = { onHash: vi.fn(), onAssess: vi.fn(), onBind: vi.fn(), ...overrides };
  render(
    <SignalPanel
      payloadHash={"a".repeat(64)}
      readiness={readiness}
      candidate={candidate}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("SignalPanel webhook akışı (Faz 12.4)", () => {
  it("3 adımı ve alert şablonunu gösterir", () => {
    renderPanel();
    expect(screen.getByText(/1\. Ayarlar/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Alertler/)).toBeInTheDocument();
    expect(screen.getByText(/3\. Başlat/)).toBeInTheDocument();
    expect(screen.getByText("/api/signals/webhook/tradingview")).toBeInTheDocument();
    expect(screen.getByText(/strategy\.order\.id/)).toBeInTheDocument();
  });

  it("token durumunu sır ifşa etmeden denetler", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { configured: true } }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.click(screen.getByRole("button", { name: /Durumu denetle/ }));
      expect(await screen.findByText("Yapılandırıldı")).toBeInTheDocument();
      expect(fetchMock).toHaveBeenCalledWith("/api/signals/webhook/status");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("alertleri listeler, seçim bind formunu doldurur", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: {
          intakes: [
            { signal_id: "tv-aaa", symbol: "BTCUSDT", action: "BUY", event_time_us: 100, status: "ACCEPTED" },
          ],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.click(screen.getByRole("button", { name: /Alertleri yenile/ }));
      expect(await screen.findByText("tv-aaa")).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: /tv-aaa/ }));
      expect((screen.getByLabelText("Webhook sinyal ID") as HTMLInputElement).value).toBe("tv-aaa");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("bind adımı adayı sunucudan alır", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: { candidate_id: "cand-1", signal_id: "tv-aaa", side: "BUY", qty: "0.01", expires_us: 200 },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.change(screen.getByLabelText("Webhook sinyal ID"), { target: { value: "tv-aaa" } });
      fireEvent.click(screen.getByRole("button", { name: /Sinyali adaya bağla/ }));
      expect(await screen.findByText("cand-1")).toBeInTheDocument();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/signals/webhook/tv-aaa/bind",
        expect.objectContaining({ method: "POST" }),
      );
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("15.6: maks. sermaye geçersizse bind engellenir", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.change(screen.getByLabelText("Webhook sinyal ID"), { target: { value: "tv-aaa" } });
      fireEvent.change(screen.getByLabelText("Maks. Sermaye"), { target: { value: "abc" } });
      fireEvent.click(screen.getByRole("button", { name: /Sinyali adaya bağla/ }));
      expect(screen.getByText("Maks. sermaye boş ya da exact decimal olmalı.")).toBeInTheDocument();
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("15.6: maks. sermaye aday sonucunda yankılanır", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: { candidate_id: "cand-1", signal_id: "tv-aaa", side: "BUY", qty: "0.01", expires_us: 200 },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.change(screen.getByLabelText("Webhook sinyal ID"), { target: { value: "tv-aaa" } });
      fireEvent.change(screen.getByLabelText("Maks. Sermaye"), { target: { value: "500" } });
      fireEvent.click(screen.getByRole("button", { name: /Sinyali adaya bağla/ }));
      expect(await screen.findByText("cand-1")).toBeInTheDocument();
      expect(screen.getByText("Maks. sermaye")).toBeInTheDocument();
      expect(screen.getByText("500")).toBeInTheDocument();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("SignalPanel", () => {
  it("hash, readiness ve adayı gösterir", () => {
    renderPanel();
    expect(screen.getByText(/a{64}/)).toBeInTheDocument();
    expect(screen.getByText("READY")).toBeInTheDocument();
    expect(screen.getByText("c".repeat(64))).toBeInTheDocument();
    expect(screen.getByText(/emir yetkisi yok/)).toBeInTheDocument();
  });

  it("hash ve assess akışı typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Yük (JSON)"), {
      target: { value: '{"action":"BUY"}' },
    });
    fireEvent.click(screen.getByRole("button", { name: /Hash üret/ }));
    expect(handlers.onHash).toHaveBeenCalledWith({ action: "BUY" });
    fireEvent.change(screen.getByLabelText("Signal ID"), { target: { value: "s1" } });
    fireEvent.click(screen.getByRole("button", { name: /Readiness ölç/ }));
    expect(handlers.onAssess).toHaveBeenCalledWith(
      expect.objectContaining({ signal: expect.objectContaining({ signal_id: "s1" }) }),
    );
  });

  it("bind akışı aday parametrelerini taşır", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Aksiyon"), { target: { value: "BUY" } });
    fireEvent.change(screen.getByLabelText("Sembol"), { target: { value: "BTCUSDT" } });
    fireEvent.change(screen.getByLabelText("Miktar"), { target: { value: "0.01" } });
    fireEvent.click(screen.getByRole("button", { name: /Aday bağla/ }));
    expect(handlers.onBind).toHaveBeenCalledWith(
      expect.objectContaining({ action: "BUY", symbol: "BTCUSDT", qty: "0.01" }),
    );
  });
});
