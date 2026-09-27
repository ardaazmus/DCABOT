import { NextIntlClientProvider } from "next-intl";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import tr from "@/messages/tr.json";
import { WizardField } from "./wizard-field";

function renderField(value: string, decimal = true) {
  const onChange = vi.fn();
  render(
    <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
      <WizardField label="Tut" value={value} onChange={onChange} decimal={decimal} />
    </NextIntlClientProvider>,
  );
  return onChange;
}

describe("ondalık girişi", () => {
  it("virgül noktaya çevrilir", () => {
    const onChange = renderField("1.5");
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "1,5" } });
    expect(onChange).toHaveBeenCalledWith("1.5");
  });

  it("binlik ayırıcıda uyarı gösterir", () => {
    renderField("1.000");
    expect(
      screen.getByText("Ondalık için virgül ya da nokta kullanın, binlik ayırıcı kullanmayın."),
    ).toBeDefined();
  });

  it("normal değerde uyarı yoktur", () => {
    renderField("1.5");
    expect(
      screen.queryByText("Ondalık için virgül ya da nokta kullanın, binlik ayırıcı kullanmayın."),
    ).toBeNull();
  });

  it("decimal değilse dönüşüm yapılmaz", () => {
    const onChange = renderField("a", false);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "a,b" } });
    expect(onChange).toHaveBeenCalledWith("a,b");
  });
});
