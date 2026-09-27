import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  AdvancedDetails,
  CalculatedPreview,
  ConditionalField,
  FieldGroup,
  NumericParameter,
  RiskCritical,
  Section,
  TextParameter,
} from "./forms";

describe("forms", () => {
  it("Section başlık + içerik gösterir", () => {
    render(<Section id="s" eyebrow="TEST" title="Başlık"><p>içerik</p></Section>);
    expect(screen.getByRole("heading", { name: "Başlık" })).toBeInTheDocument();
    expect(screen.getByText("içerik")).toBeInTheDocument();
  });

  it("TextParameter hata durumunda alert ve aria-invalid üretir", () => {
    render(<TextParameter label="Ad" name="name" value="" error="Gerekli" onChange={() => {}} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Gerekli");
    expect(screen.getByLabelText("Ad")).toHaveAttribute("aria-invalid", "true");
  });

  it("NumericParameter onChange değerini iletir", () => {
    const onChange = vi.fn();
    render(<NumericParameter label="Sayı" name="n" value="1" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Sayı"), { target: { value: "2" } });
    expect(onChange).toHaveBeenCalledWith("2");
  });

  it("ConditionalField koşula göre gösterir/gizler", () => {
    const { rerender } = render(<ConditionalField when={false}><p>gizli</p></ConditionalField>);
    expect(screen.queryByText("gizli")).not.toBeInTheDocument();
    rerender(<ConditionalField when={true}><p>gizli</p></ConditionalField>);
    expect(screen.getByText("gizli")).toBeInTheDocument();
  });

  it("CalculatedPreview değer + birim + not gösterir", () => {
    render(<CalculatedPreview label="Toplam" value="340" unit="USDT" note="backend" />);
    expect(screen.getByText("340")).toBeInTheDocument();
    expect(screen.getByText("USDT")).toBeInTheDocument();
    expect(screen.getByText("backend")).toBeInTheDocument();
  });

  it("AdvancedDetails varsayılan kapalıdır, tıklayınca açılır", () => {
    render(<AdvancedDetails title="Gelişmiş: listeler"><p>blacklist</p></AdvancedDetails>);
    const details = document.querySelector("details");
    expect(details?.open).toBe(false);
    fireEvent.click(screen.getByText("Gelişmiş: listeler"));
    expect(details?.open).toBe(true);
    expect(screen.getByText("blacklist")).toBeInTheDocument();
  });

  it("3. katman seviyesi zorla açık gösterilir", () => {
    render(
      <AdvancedDetails title="Gelişmiş: bir">
        <AdvancedDetails title="Gelişmiş: iki">
          <AdvancedDetails title="Gelişmiş: üç">
            <p>derin içerik</p>
          </AdvancedDetails>
        </AdvancedDetails>
      </AdvancedDetails>,
    );
    expect(screen.getByText(/Katman sınırı aşıldı/)).toBeInTheDocument();
    expect(screen.getByText("derin içerik")).toBeInTheDocument();
    expect(document.querySelectorAll("details")).toHaveLength(2);
  });

  it("RiskCritical katman içinde uyarı verir ve açıktır", () => {
    render(
      <AdvancedDetails title="Gelişmiş: risk">
        <RiskCritical label="Bütçe"><p>bütçe alanı</p></RiskCritical>
      </AdvancedDetails>,
    );
    expect(screen.getByText(/Risk-kritik alan katlanamaz/)).toBeInTheDocument();
    expect(screen.getByText("bütçe alanı")).toBeInTheDocument();
  });

  it("RiskCritical katmansız durumda sarmalamadan gösterir", () => {
    render(<RiskCritical label="Bütçe"><p>bütçe alanı</p></RiskCritical>);
    expect(screen.queryByText(/katlanamaz/)).not.toBeInTheDocument();
    expect(screen.getByText("bütçe alanı")).toBeInTheDocument();
  });
});
