import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  isRegimeGateResponse,
  RegimePanel,
  type RegimeGateResult,
} from "./RegimePanel";

const datasets = [{ dataset_id: "d1", dataset_type: "kline_csv_zip", instrument: "BTCUSDT", interval: "1h" }] as never;

function bars(count: number) {
  return Array.from({ length: count }, (_, index) => ({
    bar_index: index,
    open_time_us: 0,
    close_time_us: 0,
    open: "9",
    high: "10",
    low: "8",
    close: "9",
    base_volume: "1",
  }));
}

const result: RegimeGateResult = {
  state: "TREND_CANDIDATE",
  direction: "UP",
  confidence: "0.5",
  adx: "25",
  plus_di: "30",
  minus_di: "5",
  bb_width: null,
};

describe("AA.8 regime kartı", () => {
  it("guard sözleşmesi", () => {
    expect(isRegimeGateResponse({ data: result })).toBe(true);
    expect(isRegimeGateResponse({ data: { ...result, direction: 3 } })).toBe(false);
    expect(isRegimeGateResponse({ data: { ...result, confidence: 0.5 } })).toBe(false);
    expect(isRegimeGateResponse({})).toBe(false);
  });

  it("sonuç verbatim dizilir, null tire olur", () => {
    render(<RegimePanel datasets={datasets} bars={bars(120)} label="d1" seriesBusy={false} seriesError="" busy={false} error="" result={result} onSelectSeries={() => {}} onRun={() => {}} />);
    expect(screen.getAllByText("TREND_CANDIDATE")).toHaveLength(2);
    expect(screen.getByText("UP")).toBeInTheDocument();
    expect(screen.getByText("0.5")).toBeInTheDocument();
    expect(screen.getByText("olasılık DEĞİLDİR", { exact: false })).toBeInTheDocument();
  });

  it("geçerli form son-N barı aynen POST'lar", () => {
    const onRun = vi.fn();
    render(<RegimePanel datasets={datasets} bars={bars(10)} label="d1" seriesBusy={false} seriesError="" busy={false} error="" result={null} onSelectSeries={() => {}} onRun={onRun} />);
    fireEvent.change(screen.getByLabelText("Bar sayısı — sondan (2-5000)"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Rejimi değerlendir" }));
    expect(onRun).toHaveBeenCalledTimes(1);
    const payload = onRun.mock.calls[0][0];
    expect(payload.bars).toHaveLength(5);
    expect(payload.bars[0]).toEqual({ high: "10", low: "8", close: "9" });
    expect(payload.adx_window).toBe(3);
    expect(payload.squeeze_threshold).toBe("0.01");
  });

  it("bozuk girdi POST'lamaz", () => {
    const onRun = vi.fn();
    render(<RegimePanel datasets={datasets} bars={bars(10)} label="d1" seriesBusy={false} seriesError="" busy={false} error="" result={null} onSelectSeries={() => {}} onRun={onRun} />);
    fireEvent.change(screen.getByLabelText("Trend eşiği"), { target: { value: "abc" } });
    fireEvent.click(screen.getByRole("button", { name: "Rejimi değerlendir" }));
    expect(onRun).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("exact-ondalık");
  });
});
