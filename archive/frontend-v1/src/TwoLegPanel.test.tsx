import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  TwoLegPanel,
  type TwoLegProjectionView,
} from "./TwoLegPanel";
import { I18nProvider, LANGUAGE_STORAGE_KEY } from "./i18n";

const projection: TwoLegProjectionView = {
  state: "ONE_LEG_FILLED",
  leg_a_identity: {
    account_id: "acct-1",
    venue_profile: "BINANCE-SPOT",
    product_id: "BTCUSDT",
    symbol: "BTCUSDT",
    position_mode: "HEDGE",
    hedge_side: "LONG",
  },
  leg_b_identity: null,
  leg_a_quantity: "0.5",
  leg_b_quantity: "0",
  leg_a_status: "FULL",
  leg_b_status: "NONE",
  fills: [
    { fill_id: "f-a1", leg_id: "A", quantity: "0.5", fill_status: "FULL", event_time_us: 1000 },
  ],
};

function renderPanel(overrides = {}) {
  const handlers = {
    onStart: vi.fn(),
    onFill: vi.fn(),
    onRecovery: vi.fn(),
    onTimeout: vi.fn(),
    onReplay: vi.fn(),
    ...overrides,
  };
  render(
    <TwoLegPanel
      sessionId="sess-1"
      projection={projection}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("TwoLegPanel", () => {
  it("projeksiyon durum ve bacakları gösterir", () => {
    renderPanel();
    expect(screen.getByText("ONE_LEG_FILLED")).toBeInTheDocument();
    expect(screen.getByText(/sentetik bacak üretilmez/)).toBeInTheDocument();
  });

  it("start ve fill gönderimleri typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Session kimliği"), { target: { value: "sess-9" } });
    fireEvent.click(screen.getByRole("button", { name: /Session başlat/ }));
    expect(handlers.onStart).toHaveBeenCalledWith("sess-9");
    const cardA = within(screen.getByRole("group", { name: "Hedge Bacağı A kartı" }));
    fireEvent.change(cardA.getByLabelText("Fill kimliği"), { target: { value: "f-a2" } });
    fireEvent.change(cardA.getByLabelText("Miktar"), { target: { value: "1.25" } });
    fireEvent.click(cardA.getByRole("button", { name: /Fill kabul et/ }));
    expect(handlers.onFill).toHaveBeenCalledWith(
      expect.objectContaining({ fill_id: "f-a2", quantity: "1.25", leg_id: "A" }),
    );
  });

  it("terminal ve replay düğmeleri handler çağırır", () => {
    const handlers = renderPanel();
    fireEvent.click(screen.getByRole("button", { name: /Kurtarma Gerekli işaretle/ }));
    fireEvent.click(screen.getByRole("button", { name: /Zaman Aşımı işaretle/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Replay$/ }));
    expect(handlers.onRecovery).toHaveBeenCalledTimes(1);
    expect(handlers.onTimeout).toHaveBeenCalledTimes(1);
    expect(handlers.onReplay).toHaveBeenCalledTimes(1);
  });

  it("15.3c: durum şeridi hedge durumunu + dolum sayısını + session gösterir", () => {
    renderPanel();
    const strip = screen.getByTestId("hedge-status-strip");
    expect(within(strip).getByText("ONE_LEG_FILLED")).toBeInTheDocument();
    expect(within(strip).getByText("sess-1")).toBeInTheDocument();
    expect(within(strip).getByText("1")).toBeInTheDocument();
  });

  it("15.3c: iki bacak kartı bağımsız form taşır", () => {
    const handlers = renderPanel();
    const cardA = within(screen.getByRole("group", { name: "Hedge Bacağı A kartı" }));
    const cardB = within(screen.getByRole("group", { name: "Hedge Bacağı B kartı" }));
    expect(cardA.getByText("AÇIK · 0.5")).toBeInTheDocument();
    expect(cardB.getByText("KAPALI · 0")).toBeInTheDocument();
    fireEvent.change(cardB.getByLabelText("Fill kimliği"), { target: { value: "f-b1" } });
    fireEvent.change(cardB.getByLabelText("Miktar"), { target: { value: "2" } });
    fireEvent.click(cardB.getByRole("radio", { name: "Kısa" }));
    fireEvent.click(cardB.getByRole("radio", { name: "Kısmi" }));
    fireEvent.click(cardB.getByRole("button", { name: /Fill kabul et/ }));
    expect(handlers.onFill).toHaveBeenCalledWith(
      expect.objectContaining({ leg_id: "B", hedge_side: "SHORT", fill_status: "PARTIAL" }),
    );
    expect(cardA.getByLabelText("Fill kimliği")).toHaveValue("");
  });

  it("15.3c: direnç/destek kapalı rozeti taşır", () => {
    renderPanel();
    expect(screen.getByText("Direnç/Destek seviyeleri")).toBeInTheDocument();
    expect(screen.getByText("Kapalı")).toBeInTheDocument();
  });

  it("15.2b: TR sektör terminolojisini gösterir (Hedge Bacağı/Dolum)", () => {
    renderPanel();
    const cardA = within(screen.getByRole("group", { name: "Hedge Bacağı A kartı" }));
    expect(cardA.getByRole("radiogroup", { name: "Hedge Yönü" })).toBeInTheDocument();
    expect(cardA.getByRole("radiogroup", { name: "Dolum Durumu" })).toBeInTheDocument();
    expect(screen.getByText("Hedge Bacağı A")).toBeInTheDocument();
  });

  it("15.2b: EN dilinde sektör terminolojisini gösterir", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    render(
      <I18nProvider>
        <TwoLegPanel sessionId="sess-1" projection={projection} busy={false} error="" onStart={() => {}} onFill={() => {}} onRecovery={() => {}} onTimeout={() => {}} onReplay={() => {}} />
      </I18nProvider>,
    );
    const cardA = within(screen.getByRole("group", { name: "Hedge Leg A card" }));
    expect(cardA.getByRole("radiogroup", { name: "Hedge Direction" })).toBeInTheDocument();
    expect(cardA.getByRole("radiogroup", { name: "Fill Status" })).toBeInTheDocument();
    expect(screen.getByText("Hedge Leg A")).toBeInTheDocument();
    window.localStorage.clear();
  });
});
