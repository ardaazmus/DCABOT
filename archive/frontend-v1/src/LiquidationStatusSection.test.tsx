import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  isLiquidationStatusView,
  LiquidationStatusSection,
  type LiquidationStatusView,
} from "./LiquidationStatusSection";

const READY: LiquidationStatusView = {
  state: "DATA_OK",
  liquidation_price: "54000",
  margin_ratio: "0.01",
  is_fast_move: false,
  reason: null,
};

function sectionProps(overrides: {
  symbol?: string | null;
  pairCount?: number;
  status?: LiquidationStatusView | null;
  busy?: boolean;
  error?: string;
  onRefresh?: () => void;
} = {}) {
  return {
    symbol: "BTCUSDT",
    pairCount: 1,
    status: READY,
    busy: false,
    error: "",
    onRefresh: vi.fn(),
    ...overrides,
  };
}

describe("LiquidationStatusSection (D.2 = 8.3)", () => {
  it("canlı venue değerlerini + değişkenlik notunu gösterir (8.3.1 + 8.3.2)", () => {
    render(<LiquidationStatusSection {...sectionProps()} />);

    expect(screen.getByRole("heading", { name: "Likidasyon durumu · BTCUSDT" })).toBeInTheDocument();
    expect(screen.getByText("✓ Güncel")).toBeInTheDocument();
    expect(screen.getByText("54000")).toBeInTheDocument();
    expect(screen.getByText("0.01")).toBeInTheDocument();
    expect(screen.getByText("Bu değer borsanın anlık raporudur, sabit değildir.")).toBeInTheDocument();
  });

  it("hızlı-hareket uyarısını belirgin gösterir (8.3.3)", () => {
    render(
      <LiquidationStatusSection
        {...sectionProps({ status: { ...READY, state: "WATCH", is_fast_move: true } })}
      />,
    );

    const warning = screen.getByRole("alert");
    expect(warning).toHaveTextContent("Hızlı hareket: bu veri daha az güvenilir olabilir.");
    expect(warning).toHaveClass("liq-fastmove");
    expect(screen.getByText("● İzleniyor")).toBeInTheDocument();
  });

  it("venue bağlı değilse dürüst boş gösterir (8.3.4)", () => {
    render(
      <LiquidationStatusSection
        {...sectionProps({
          status: { ...READY, state: "SIMULATED_ONLY", liquidation_price: null, margin_ratio: null, reason: "VENUE_HAS_NO_POSITION_RISK_DATA" },
        })}
      />,
    );

    expect(screen.getByText("Veri yok — venue pozisyon verisi bağlı değil.")).toBeInTheDocument();
    expect(screen.queryByText("54000")).not.toBeInTheDocument();
  });

  it("STALE durumda son bilinen değerleri eski-veri notuyla gösterir", () => {
    render(
      <LiquidationStatusSection {...sectionProps({ status: { ...READY, state: "STALE" } })} />,
    );

    expect(screen.getByText("54000")).toBeInTheDocument();
    expect(screen.getByText("Son bilinen değerler gösteriliyor (eski veri).")).toBeInTheDocument();
  });

  it("pair yoksa sorgulamaz, hata durumunda Yenile çağırır", () => {
    const { rerender } = render(
      <LiquidationStatusSection {...sectionProps({ symbol: null, pairCount: 0, status: null })} />,
    );
    expect(screen.getByText("Pair yok — sorgulanamadı.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Yenile" })).not.toBeInTheDocument();

    const onRefresh = vi.fn();
    rerender(
      <LiquidationStatusSection
        {...sectionProps({ status: null, error: "Pozisyon riski alınamadı.", onRefresh })}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Yenile" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("çok pair'li botta ilk pair'in sorgulandığını yazar", () => {
    render(<LiquidationStatusSection {...sectionProps({ pairCount: 3 })} />);

    expect(screen.getByText("Botun ilk pair'i sorgulanıyor.")).toBeInTheDocument();
  });
});

describe("isLiquidationStatusView", () => {
  it("geçerli gövdeyi kabul eder, bozukları reddeder", () => {
    expect(isLiquidationStatusView(READY)).toBe(true);
    expect(isLiquidationStatusView(null)).toBe(false);
    expect(isLiquidationStatusView({ ...READY, state: "BOGUS" })).toBe(false);
    expect(isLiquidationStatusView({ ...READY, is_fast_move: "yes" })).toBe(false);
    expect(isLiquidationStatusView({ ...READY, liquidation_price: 54000 })).toBe(false);
  });
});
