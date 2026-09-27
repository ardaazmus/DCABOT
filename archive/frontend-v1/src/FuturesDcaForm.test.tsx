import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FuturesDcaForm } from "./FuturesDcaForm";
import type { FuturesGridView } from "./FuturesPanel";

const grid: FuturesGridView = {
  levels: ["100", "150", "200"],
  arithmetic_step: "50",
  level_mode: "ARITHMETIC",
};

function renderForm(gridValue: FuturesGridView | null = grid) {
  const onGrid = vi.fn();
  render(<FuturesDcaForm grid={gridValue} busy={false} error="" onGrid={onGrid} />);
  return { onGrid };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("FuturesDcaForm (15.3b)", () => {
  it("Pionex sırasını gösterir: merdiven → TP → yatırım", () => {
    renderForm();
    expect(screen.getByRole("heading", { name: "Futures DCA Bot" })).toBeInTheDocument();
    expect(screen.getByText(/1\. Pozisyon Fiyatı Ekle/)).toBeInTheDocument();
    expect(screen.getByText(/2\. Kâr Al Fiyatı/)).toBeInTheDocument();
    expect(screen.getByText(/3\. Yatırım/)).toBeInTheDocument();
  });

  it("merdiven satırları grid seviyelerinden gelir, paylar düzenlenir", () => {
    renderForm();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    const firstShares = screen.getByLabelText("1. satır payı");
    expect(firstShares).toHaveValue("1");
    fireEvent.change(firstShares, { target: { value: "3" } });
    expect(firstShares).toHaveValue("3");
  });

  it("seviye yokken merdiven boş-durum gösterir", () => {
    renderForm(null);
    expect(screen.getByText(/Önce seviyeleri üretin/)).toBeInTheDocument();
  });

  it("özet merdiven ucundan toplam pay + ort. giriş gösterir", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { direction: "LONG", leg_count: 3, total_shares: "6", weighted_average_entry: "150", weighted_average_exact: true } }),
      }),
    );
    const { onGrid } = renderForm();
    expect(onGrid).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("1. satır payı"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("2. satır payı"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Özeti hesapla" }));
    expect(await screen.findByText("6")).toBeInTheDocument();
    expect(await screen.findAllByText("150")).toHaveLength(2);
    expect(fetch).toHaveBeenCalledWith(
      "/api/futures/ladder/summary",
      expect.objectContaining({ method: "POST" }),
    );
    const body = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as string);
    expect(body.direction).toBe("LONG");
    expect(body.legs).toEqual([
      { price: "100", shares: "3" },
      { price: "150", shares: "2" },
      { price: "200", shares: "1" },
    ]);
  });

  it("exact olmayan ortalama bayrakla gösterilir, yuvarlanmaz", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { direction: "LONG", leg_count: 2, total_shares: "3", weighted_average_entry: null, weighted_average_exact: false } }),
      }),
    );
    renderForm({ levels: ["100", "150"], arithmetic_step: "50", level_mode: "ARITHMETIC" });
    fireEvent.change(screen.getByLabelText("2. satır payı"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Özeti hesapla" }));
    expect(await screen.findByText("exact değil (yuvarlatılmadı)")).toBeInTheDocument();
    expect(screen.getAllByText("3")).toHaveLength(2);
  });

  it("15.5: özet satırında Exact rozeti + tooltip", () => {
    renderForm();
    expect(screen.getByText("Exact ✓")).toHaveAttribute("title", "Kesirli aritmetik, yuvarlama kaybı yok");
  });

  it("TP çipleri exact oranı yazar", () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "5%" }));
    expect(screen.getByLabelText("Kâr Al Oranı")).toHaveValue("0.05");
  });

  it("marjin özeti + yatırımı kullanır, likidasyon dürüstçe yok sayılır", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { direction: "LONG", leg_count: 3, total_shares: "7", weighted_average_entry: "150", weighted_average_exact: true } }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: { notional: "450", required_initial_margin: "45", reserve_asset: "USDT", capacity_status: "OK" },
        }),
      });
    vi.stubGlobal("fetch", fetchMock);
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Özeti hesapla" }));
    expect(await screen.findByText("7")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "1000" } });
    fireEvent.click(screen.getByRole("button", { name: "Marjini projekte et" }));
    expect(await screen.findByText("45")).toBeInTheDocument();
    expect(screen.getByText(/Likidasyon tahmini bu fazda yok/)).toBeInTheDocument();
    const marginBody = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(marginBody.reference_price).toBe("150");
    expect(marginBody.available_margin).toBe("1000");
  });
});
