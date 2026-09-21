import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  ExitPanel,
  type BreakevenView,
  type PercentStateView,
  type TrailingBindView,
} from "./ExitPanel";
import { I18nProvider, LANGUAGE_STORAGE_KEY } from "./i18n";

const binding: TrailingBindView = {
  trigger_price: "105",
  requested_qty: "1",
  remaining_capacity: "1",
  order_authority: "NONE",
};

const percent: PercentStateView = {
  status: "ACTIVE",
  activation_price: "100",
  rate: "0.05",
  high_water: "110",
  stop_price: "104.5",
};

const breakeven: BreakevenView = {
  status: "FEE_AWARE_READY",
  gross_breakeven_price: "99.5",
  fee_aware_breakeven_price: "100.495",
  reason: "FEE_AWARE_READY",
  profile_revision: "test-fees-v1",
  order_authority: "NONE",
};

function renderPanel(overrides = {}) {
  const handlers = {
    onBind: vi.fn(),
    onPercentArm: vi.fn(),
    onPercentObserve: vi.fn(),
    onBreakeven: vi.fn(),
    ...overrides,
  };
  render(
    <ExitPanel
      binding={binding}
      percent={percent}
      breakeven={breakeven}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("ExitPanel", () => {
  it("bağlama, yüzde state ve breakeven gösterir", () => {
    renderPanel();
    expect(screen.getByText("105")).toBeInTheDocument();
    expect(screen.getByText("104.5")).toBeInTheDocument();
    expect(screen.getByText("100.495")).toBeInTheDocument();
    expect(screen.getByText(/Emir yetkisi yok/)).toBeInTheDocument();
  });

  it("çıkış adayı typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Stop fiyatı"), { target: { value: "105" } });
    fireEvent.change(screen.getByLabelText("İstenen çıkış"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: /Çıkış adayı üret/ }));
    expect(handlers.onBind).toHaveBeenCalledWith(
      expect.objectContaining({ side: "LONG", kind: "FIXED", requested_qty: "1" }),
    );
  });

  it("yüzde akışı ve breakeven handler çağırır", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("İz Sürme Oranı %"), { target: { value: "0.05" } });
    fireEvent.click(screen.getByRole("button", { name: /Yüzde trailing kur/ }));
    expect(handlers.onPercentArm).toHaveBeenCalledWith(
      expect.objectContaining({ rate: "0.05" }),
    );
    fireEvent.change(screen.getByLabelText("Gözlenen fiyat"), { target: { value: "110" } });
    fireEvent.click(screen.getByRole("button", { name: /Yüzde gözlemi işle/ }));
    expect(handlers.onPercentObserve).toHaveBeenCalledWith(
      expect.objectContaining({ price: "110" }),
    );
    fireEvent.click(screen.getByRole("button", { name: /Breakeven hesapla/ }));
    expect(handlers.onBreakeven).toHaveBeenCalledTimes(1);
  });

  it("15.2b: TR sektör terminolojisini gösterir (Açık Pozisyon/Aktivasyon)", () => {
    renderPanel();
    expect(screen.getByLabelText("Açık Pozisyon")).toBeInTheDocument();
    expect(screen.getByLabelText("Aktivasyon Fiyatı")).toBeInTheDocument();
    expect(screen.getByLabelText("İz Sürme Oranı %")).toBeInTheDocument();
  });

  it("15.2b: EN dilinde sektör terminolojisini gösterir", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    render(
      <I18nProvider>
        <ExitPanel binding={binding} percent={percent} breakeven={breakeven} busy={false} error="" onBind={() => {}} onPercentArm={() => {}} onPercentObserve={() => {}} onBreakeven={() => {}} />
      </I18nProvider>,
    );
    expect(screen.getByLabelText("Activation Price")).toBeInTheDocument();
    expect(screen.getByLabelText("Trailing Rate %")).toBeInTheDocument();
    expect(screen.getByLabelText("Open Position Size")).toBeInTheDocument();
    window.localStorage.clear();
  });
});
