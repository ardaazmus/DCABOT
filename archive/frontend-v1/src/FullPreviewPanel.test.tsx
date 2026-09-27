import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  FullPreviewPanel,
  isFullPreview,
  isFullPreviewResponse,
  isFuturesStyleConfig,
  mergeConfigOverrides,
  studioLeverageIssue,
  type FullPreview,
} from "./FullPreviewPanel";

/* tests/api/test_preview_full.py::test_response_contract_is_locked ile aynı şekil. */
const preview: FullPreview = {
  symbol: "BTCUSDT",
  anchor: "100",
  average_cost: "100",
  take_profit_price: "102",
  stop_loss_price: null,
  liquidation_price: null,
  liquidation_note: "venue-sağlar",
  estimated_initial_margin: "100",
  planned_gross_notional: "500",
  within_gross_entry_cap: true,
  levels: [
    { index: 1, price: "90", qty: "1", notional: "90" },
    { index: 2, price: "80", qty: "1", notional: "80" },
  ],
};

describe("FullPreviewPanel", () => {
  const launchProps = { launchBusy: false, launchError: "", launchedId: null as string | null, onLaunchPaper: () => {} };

  it("AA.5a: 5 istatistik + seviyeler dizilir", () => {
    render(<FullPreviewPanel preview={preview} status="ready" error="" baseReady={true} {...launchProps} />);
    expect(screen.getAllByText("100")).toHaveLength(2);
    expect(screen.getByText("102")).toBeInTheDocument();
    expect(screen.getByText("venue-sağlar")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(3);
    expect(within(table).getByText("SO#index")).toBeInTheDocument();
    expect(within(table).getByText("Notional")).toBeInTheDocument();
    expect(within(table).getByText("SO#1")).toBeInTheDocument();
    expect(within(table).getByText("SO#2")).toBeInTheDocument();
    expect(screen.getByText("Hesaplandı")).toBeInTheDocument();
  });

  it("AA.5a: taban-bekleme ve hata durumları", () => {
    const { unmount } = render(<FullPreviewPanel preview={null} status="idle" error="" baseReady={false} {...launchProps} />);
    expect(screen.getByText("Taban config bekleniyor — paper.json okununca önizleme otomatik hesaplanır.")).toBeInTheDocument();
    unmount();
    render(<FullPreviewPanel preview={null} status="error" error="uç 422" baseReady={true} {...launchProps} />);
    expect(screen.getByRole("alert")).toHaveTextContent("uç 422");
  });

  it("AA.13: hazır-önizlemede Paper fırlatma düğmesi çalışır", () => {
    const onLaunchPaper = vi.fn();
    render(<FullPreviewPanel preview={preview} status="ready" error="" baseReady={true} launchBusy={false} launchError="" launchedId={null} onLaunchPaper={onLaunchPaper} />);
    const button = screen.getByRole("button", { name: "Paper'da Başlat" });
    expect(button).toBeEnabled();
    fireEvent.click(button);
    expect(onLaunchPaper).toHaveBeenCalledTimes(1);
  });

  it("AA.13: hazır-değilken düğme kilitli, sonuçlar bildirilir", () => {
    const { unmount } = render(<FullPreviewPanel preview={null} status="idle" error="" baseReady={false} {...launchProps} />);
    expect(screen.getByRole("button", { name: "Paper'da Başlat" })).toBeDisabled();
    unmount();
    const { unmount: unmount2 } = render(<FullPreviewPanel preview={preview} status="ready" error="" baseReady={true} {...launchProps} launchError="uç 409" />);
    expect(screen.getByRole("alert")).toHaveTextContent("uç 409");
    unmount2();
    render(<FullPreviewPanel preview={preview} status="ready" error="" baseReady={true} {...launchProps} launchedId="paper-BTCUSDT-1" />);
    expect(screen.getByRole("status")).toHaveTextContent("paper-BTCUSDT-1");
  });

  it("AA.5a: bindirme saf-kopyalamadır", () => {
    const base = { symbol: "BTCUSDT", safety_qty: "0.001", safety_count: 5, deviation: "0.02", take_profit: "0.03" };
    const merged = mergeConfigOverrides(base, { safety_qty: "0.002", safety_count: "3", deviation: "0.01", leverage: "1", direction: "LONG", margin_mode: "ISOLATED" });
    expect(merged).toEqual({ symbol: "BTCUSDT", safety_qty: "0.002", safety_count: 3, deviation: "0.01", take_profit: "0.03", leverage: "1", direction: "LONG", margin_mode: "ISOLATED" });
    expect(base.safety_count).toBe(5);
  });

  it("Futures-paper: 3 yeni alan verbatim bindirilir", () => {
    const merged = mergeConfigOverrides(
      { leverage: "1", direction: "LONG", margin_mode: "ISOLATED" },
      { safety_qty: "0.002", safety_count: "3", deviation: "0.01", leverage: "5", direction: "SHORT", margin_mode: "CROSS" },
    );
    expect(merged.leverage).toBe("5");
    expect(merged.direction).toBe("SHORT");
    expect(merged.margin_mode).toBe("CROSS");
  });

  it("Futures-paper: kaldıraç ön-kontrolü + futures-tarzı koşulu", () => {
    expect(studioLeverageIssue("1")).toBeUndefined();
    expect(studioLeverageIssue("20")).toBeUndefined();
    expect(studioLeverageIssue("2.5")).toBeUndefined();
    expect(studioLeverageIssue("abc")).toBe("Kaldıraç exact-ondalık olmalıdır.");
    expect(studioLeverageIssue("0")).toBe("Kaldıraç 1-20 aralığında olmalıdır (sunucu ≤100 kabul eder).");
    expect(studioLeverageIssue("21")).toBe("Kaldıraç 1-20 aralığında olmalıdır (sunucu ≤100 kabul eder).");
    expect(isFuturesStyleConfig({ leverage: "1", direction: "LONG" })).toBe(false);
    expect(isFuturesStyleConfig({ leverage: "1", direction: "SHORT" })).toBe(true);
    expect(isFuturesStyleConfig({ leverage: "3", direction: "LONG" })).toBe(true);
    expect(isFuturesStyleConfig({ leverage: "abc", direction: "LONG" })).toBe(false);
  });

  it("AA.5a: guard sözleşmesi", () => {
    expect(isFullPreview(preview)).toBe(true);
    expect(isFullPreview({ ...preview, liquidation_price: "90000" })).toBe(false);
    expect(isFullPreview({ ...preview, within_gross_entry_cap: "yes" })).toBe(false);
    expect(isFullPreviewResponse({ data: preview })).toBe(true);
    expect(isFullPreviewResponse({})).toBe(false);
  });

  it("AB.1-düzeltme: eski uydurma seviye şekli reddedilir", () => {
    expect(isFullPreview({ ...preview, levels: [{ role: "BASE", qty: "0.001", price: "97500", deviation: "0" }] })).toBe(false);
    expect(isFullPreview({ ...preview, levels: [{ index: 0, price: "90", qty: "1", notional: "90" }] })).toBe(false);
    expect(isFullPreview({ ...preview, levels: [{ index: "1", price: "90", qty: "1", notional: "90" }] })).toBe(false);
  });
});
