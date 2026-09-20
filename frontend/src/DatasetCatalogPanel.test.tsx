import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ActionTable } from "./DatasetCatalogPanel";
import type { HistoricalSimulationResult } from "./datasetCatalog";

const actions: HistoricalSimulationResult["actions"] = [
  {
    bar_index: 1,
    open_time_us: 1,
    role: "BASE",
    raw_reference: "bar-1",
    fill_price: "100",
    quantity: "1",
    fee: "0",
  },
  {
    bar_index: 2,
    open_time_us: 3,
    role: "SAFETY",
    raw_reference: "bar-2",
    fill_price: "101",
    quantity: "2",
    fee: "0",
  },
];

describe("ActionTable keyboard selection", () => {
  it("Enter tuşu satır seçimini bildirir", () => {
    const onSelectBarIndex = vi.fn();
    render(<ActionTable actions={actions} fixedSlice={false} onSelectBarIndex={onSelectBarIndex} />);

    fireEvent.keyDown(screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" }), { key: "Enter" });

    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });

  it("Space tuşu satır seçimini bildirir, ilgisiz tuş bildirmez", () => {
    const onSelectBarIndex = vi.fn();
    render(<ActionTable actions={actions} fixedSlice={false} onSelectBarIndex={onSelectBarIndex} />);

    const row = screen.getByRole("button", { name: "Bar 2 aksiyonunu seç" });
    fireEvent.keyDown(row, { key: "a" });
    expect(onSelectBarIndex).not.toHaveBeenCalled();

    fireEvent.keyDown(row, { key: " " });
    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(2);
  });

  it("seçim handler'ı yoksa satır klavyeyle odaklanamaz", () => {
    render(<ActionTable actions={actions} fixedSlice={false} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".historical-action-row-interactive")).toHaveLength(0);
  });

  it("satır içindeki Kopyala butonuna tıklamak veya orada Enter'a basmak satırı seçmez", () => {
    const onSelectBarIndex = vi.fn();
    render(<ActionTable actions={actions} fixedSlice={true} onSelectBarIndex={onSelectBarIndex} />);

    const copyButton = screen.getAllByRole("button", { name: "Kopyala" })[0];
    fireEvent.click(copyButton);
    fireEvent.keyDown(copyButton, { key: "Enter" });

    expect(onSelectBarIndex).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Bar 1 aksiyonunu seç" }));
    expect(onSelectBarIndex).toHaveBeenCalledTimes(1);
    expect(onSelectBarIndex).toHaveBeenCalledWith(1);
  });
});
