import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  FuturesPanel,
  isFuturesTrailingView,
  type FuturesFundingView,
  type FuturesGridView,
  type FuturesPnlView,
  type FuturesTrailingView,
} from "./FuturesPanel";

const grid: FuturesGridView = {
  levels: ["100", "150", "200"],
  arithmetic_step: "50",
  level_mode: "ARITHMETIC",
};

const pnl: FuturesPnlView = {
  effective_quantity: "1",
  position_value: "51000",
  unrealized_pnl: "1000",
  settlement_asset: "USDT",
};

const trailing: FuturesTrailingView = {
  status: "ACTIVE",
  activation_price: "100",
  distance: "5",
  high_water: "110",
  stop_price: "105",
};

const funding: FuturesFundingView = {
  amount: "-5.1",
  core_expense: "5.1",
  settlement_asset: "USDT",
};

function renderPanel(overrides = {}) {
  const handlers = {
    onGrid: vi.fn(),
    onPnl: vi.fn(),
    onTrailingArm: vi.fn(),
    onTrailingObserve: vi.fn(),
    onFunding: vi.fn(),
    ...overrides,
  };
  render(
    <FuturesPanel
      grid={grid}
      pnl={pnl}
      trailing={trailing}
      funding={funding}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("FuturesPanel", () => {
  it("grid, pnl, trailing ve funding gösterir", () => {
    renderPanel();
    expect(screen.getByText("100 · 150 · 200")).toBeInTheDocument();
    expect(screen.getByText("51000")).toBeInTheDocument();
    expect(screen.getByText("105")).toBeInTheDocument();
    expect(screen.getByText("-5.1")).toBeInTheDocument();
    expect(screen.getByText(/likidasyon yetkisi yok/)).toBeInTheDocument();
  });

  it("grid ve pnl gönderimleri typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Alt fiyat"), { target: { value: "100" } });
    fireEvent.change(screen.getByLabelText("Üst fiyat"), { target: { value: "200" } });
    fireEvent.click(screen.getByRole("button", { name: /Seviyeleri üret/ }));
    expect(handlers.onGrid).toHaveBeenCalledWith(
      expect.objectContaining({ lower_price: "100", upper_price: "200" }),
    );
    fireEvent.change(screen.getByLabelText("Mark fiyatı"), { target: { value: "51000" } });
    fireEvent.click(screen.getByRole("button", { name: /PnL hesapla/ }));
    expect(handlers.onPnl).toHaveBeenCalledWith(
      expect.objectContaining({ mark_price: "51000" }),
    );
  });

  it("trailing ve funding gönderimleri typed payload üretir", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Aktivasyon"), { target: { value: "100" } });
    fireEvent.click(screen.getByRole("button", { name: /Trailing kur/ }));
    expect(handlers.onTrailingArm).toHaveBeenCalledWith(
      expect.objectContaining({ activation_price: "100" }),
    );
    fireEvent.change(screen.getByLabelText("Gözlenen fiyat"), { target: { value: "110" } });
    fireEvent.click(screen.getByRole("button", { name: /Gözlemi işle/ }));
    expect(handlers.onTrailingObserve).toHaveBeenCalledWith(
      expect.objectContaining({ price: "110" }),
    );
    fireEvent.change(screen.getByLabelText("Funding oranı"), { target: { value: "0.0001" } });
    fireEvent.click(screen.getByRole("button", { name: /Funding hesapla/ }));
    expect(handlers.onFunding).toHaveBeenCalledWith(
      expect.objectContaining({ funding_rate: "0.0001" }),
    );
  });
});

describe("FuturesPanel grid bot akışı (Faz 12.3)", () => {
  it("grid tipi seçimi sektör terminolojisini kullanır, Hedge kapalıdır", () => {
    renderPanel();
    const group = screen.getByRole("radiogroup", { name: "Grid Tipi" });
    expect(group).toBeInTheDocument();
    const options = ["Uzun", "Nötr", "Kısa", "Hedge"].map((name) => screen.getByRole("radio", { name }));
    expect(options).toHaveLength(4);
    expect(screen.getByRole("radio", { name: "Hedge" })).toHaveAttribute("aria-disabled", "true");
  });

  it("grid tipi seçimi payload yönünü belirler", () => {
    const handlers = renderPanel();
    fireEvent.click(screen.getByRole("radio", { name: "Kısa" }));
    fireEvent.click(screen.getByRole("button", { name: /Seviyeleri üret/ }));
    expect(handlers.onGrid).toHaveBeenCalledWith(expect.objectContaining({ direction: "SHORT" }));
  });

  it("grid boyutu Aralıklı'dır, Sonsuz varyant kapısıyla kapalıdır", () => {
    renderPanel();
    expect(screen.getByRole("radio", { name: "Aralıklı" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "Sonsuz" })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByText(/Sonsuz grid varyant kapısıyla kapalı/)).toBeInTheDocument();
  });

  it("grid başına brüt aralığı gösterir", () => {
    render(
      <FuturesPanel
        grid={{ levels: ["100", "150", "200"], arithmetic_step: "50", level_mode: "ARITHMETIC", gross_spacing_percent: "50", gross_spacing_percent_exact: true }}
        pnl={pnl}
        trailing={trailing}
        funding={funding}
        busy={false}
        error=""
        onGrid={vi.fn()}
        onPnl={vi.fn()}
        onTrailingArm={vi.fn()}
        onTrailingObserve={vi.fn()}
        onFunding={vi.fn()}
      />,
    );
    const label = screen.getByText("Grid Başına Kâr %");
    expect(label.closest("tr")?.textContent).toContain("50");
  });

  it("yerleşim değerlendirmesi sunucudan alınır", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { decision: "STATIC_CANDIDATE_ONLY", candidate_levels: ["100", "150"], order_authority: "NONE", reason: null } }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.click(screen.getByRole("button", { name: /Yerleşimi değerlendir/ }));
      expect(await screen.findByText("STATIC_CANDIDATE_ONLY")).toBeInTheDocument();
      expect(fetchMock).toHaveBeenCalledWith("/api/futures/grid/placement", expect.objectContaining({ method: "POST" }));
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("pozisyon ve marjin projeksiyonu fill listesinden alınır", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { position_side: "LONG", quantity: "2", average_entry: "125" } }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.click(screen.getByRole("button", { name: /Pozisyonu projekte et/ }));
      expect(await screen.findByText("125")).toBeInTheDocument();
      expect(fetchMock).toHaveBeenCalledWith("/api/futures/grid/position", expect.objectContaining({ method: "POST" }));
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("lifecycle simülasyonu olay listesinden alınır", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { status: "CANCELED", fill_ids: [], replacement_admitted: false, event_count: 2 } }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.click(screen.getByRole("button", { name: /Lifecycle simüle et/ }));
      expect(await screen.findByText("CANCELED")).toBeInTheDocument();
      expect(fetchMock).toHaveBeenCalledWith("/api/futures/grid/lifecycle", expect.objectContaining({ method: "POST" }));
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("ilke ve varyant kabulü salt okunur gösterilir", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: {
          variants: [
            { variant: "INFINITY_GRID", admission: "BLOCKED", reason: "FUTURES_GRID_VARIANT_NOT_VERIFIED" },
          ],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderPanel();
      fireEvent.click(screen.getByRole("button", { name: /İlke ve varyantlar/ }));
      expect(await screen.findByText("INFINITY_GRID")).toBeInTheDocument();
      expect(screen.getByText("BLOCKED")).toBeInTheDocument();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("isFuturesTrailingView", () => {
  it("SHORT tarafın low_water taşıyan, high_water'sız yanıtını kabul eder", () => {
    // POST /api/futures/trailing/arm|observe only includes the water-mark
    // field for the armed side: high_water for LONG, low_water for SHORT.
    expect(
      isFuturesTrailingView({
        status: "ACTIVE",
        activation_price: "100",
        distance: "5",
        stop_price: "95",
        low_water: "90",
      }),
    ).toBe(true);
  });

  it("LONG tarafın high_water taşıyan yanıtını kabul eder", () => {
    expect(isFuturesTrailingView(trailing)).toBe(true);
  });

  it("hem high_water hem low_water eksikse reddeder", () => {
    expect(
      isFuturesTrailingView({
        status: "ACTIVE",
        activation_price: "100",
        distance: "5",
        stop_price: "95",
      }),
    ).toBe(false);
  });
});
