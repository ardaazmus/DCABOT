import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  BudgetSlider,
  LabeledSlider,
  QuickPercentChips,
  SegmentedControl,
  StepperInput,
  ToggleSwitchRow,
} from "./forms";

describe("SegmentedControl (15.2)", () => {
  const options = [
    { value: "LONG", label: "Uzun" },
    { value: "SHORT", label: "Kısa" },
    { value: "HEDGE", label: "Hedge", disabled: true },
  ];
  it("seçili değeri işaretler, tıklama onChange iletir", () => {
    const onChange = vi.fn();
    render(<SegmentedControl label="Yön" name="direction" value="LONG" options={options} onChange={onChange} />);
    expect(screen.getByRole("radiogroup", { name: "Yön" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Uzun" })).toHaveAttribute("aria-checked", "true");
    fireEvent.click(screen.getByRole("radio", { name: "Kısa" }));
    expect(onChange).toHaveBeenCalledWith("SHORT");
  });
  it("kapalı seçenek tıklanamaz", () => {
    const onChange = vi.fn();
    render(<SegmentedControl label="Yön" name="direction" value="LONG" options={options} onChange={onChange} />);
    expect(screen.getByRole("radio", { name: "Hedge" })).toHaveAttribute("aria-disabled", "true");
    fireEvent.click(screen.getByRole("radio", { name: "Hedge" }));
    expect(onChange).not.toHaveBeenCalled();
  });
});

describe("QuickPercentChips (15.2)", () => {
  const chips = [
    { chip: "1%", ratio: "0.01" },
    { chip: "10%", ratio: "0.1" },
  ];
  it("çip tıklaması exact oran metnini iletir (hesap yok, eşleme tablosu)", () => {
    const onSelect = vi.fn();
    render(<QuickPercentChips label="Hızlı yüzde" options={chips} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole("button", { name: "10%" }));
    expect(onSelect).toHaveBeenCalledWith("0.1");
  });
});

describe("ToggleSwitchRow (15.2)", () => {
  it("anahtar durumunu gösterir ve tıklayınca çevirir", () => {
    const onChange = vi.fn();
    const { rerender } = render(<ToggleSwitchRow label="Zararı Durdur" checked={false} onChange={onChange} />);
    const toggle = screen.getByRole("switch", { name: "Zararı Durdur" });
    expect(toggle).toHaveAttribute("aria-checked", "false");
    fireEvent.click(toggle);
    expect(onChange).toHaveBeenCalledWith(true);
    rerender(<ToggleSwitchRow label="Zararı Durdur" checked={true} onChange={onChange} />);
    expect(screen.getByRole("switch", { name: "Zararı Durdur" })).toHaveAttribute("aria-checked", "true");
  });
});

describe("StepperInput (15.2)", () => {
  it("artı/eksi tam-sayı metnini adımla değiştirir", () => {
    const onChange = vi.fn();
    render(<StepperInput label="Adet" name="count" value="3" min="0" max="50" step="1" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /artır/i }));
    expect(onChange).toHaveBeenCalledWith("4");
    fireEvent.click(screen.getByRole("button", { name: /azalt/i }));
    expect(onChange).toHaveBeenCalledWith("2");
  });
  it("sınırları aşmaz; bozuk metinde güvenli değere döner", () => {
    const onChange = vi.fn();
    const { rerender } = render(<StepperInput label="Adet" name="count" value="50" min="0" max="50" step="1" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /artır/i }));
    expect(onChange).toHaveBeenLastCalledWith("50");
    rerender(<StepperInput label="Adet" name="count" value="bozuk" min="0" max="50" step="1" onChange={onChange} />);
    fireEvent.click(screen.getByRole("button", { name: /artır/i }));
    expect(onChange).toHaveBeenLastCalledWith("1");
  });
});

describe("BudgetSlider (15.2)", () => {
  it("slider exact durak metnini iletir, sayı girişi aynen geçer", () => {
    const onChange = vi.fn();
    render(<BudgetSlider label="Yatırım Tutarı" name="budget" value="100" max="1000" step="10" onChange={onChange} />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "25" } });
    expect(onChange).toHaveBeenCalledWith("250");
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "333.5" } });
    expect(onChange).toHaveBeenCalledWith("333.5");
  });
});

describe("LabeledSlider (15.2)", () => {
  const stops = ["1", "1.5", "2"];
  it("durak listesinden exact metin seçer; Kapalı ×1 demektir", () => {
    const onChange = vi.fn();
    render(
      <LabeledSlider label="Hacim Çarpanı" name="volume_mult" value="1.5" stops={stops} minLabel="Kapalı (×1)" maxLabel="×2" onChange={onChange} />,
    );
    expect(screen.getByText("Kapalı (×1)")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("slider"), { target: { value: "2" } });
    expect(onChange).toHaveBeenCalledWith("2");
    fireEvent.change(screen.getByRole("slider"), { target: { value: "0" } });
    expect(onChange).toHaveBeenCalledWith("1");
  });
});
