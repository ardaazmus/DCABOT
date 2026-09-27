import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { LabPanel } from "./LabPanel";

describe("LabPanel (E.2)", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("tanıtım + whale iskeleti + zorunlu risk uyarısını gösterir, veri uydurmaz", () => {
    render(<LabPanel />);

    expect(screen.getByRole("heading", { name: "Lab" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Whale Wall Detection" })).toBeInTheDocument();
    expect(screen.getByText("Tespit motoru hazır (E.3) — canlı gösterim ayrı dilimde bağlanacak.")).toBeInTheDocument();
    expect(
      screen.getByText("Bu özellik ek borsa isteği yapar, hesabınızın rate-limit'ini kullanır."),
    ).toBeInTheDocument();
  });

  it("tek-seferlik onay localStorage'a yazılır ve kalıcı olur", () => {
    render(<LabPanel />);

    const checkbox = screen.getByRole("checkbox", {
      name: "Anladım, Lab özelliklerinin ek borsa isteği yapacağını kabul ediyorum.",
    });
    fireEvent.click(checkbox);

    expect(window.localStorage.getItem("dcabot.lab.risk_ack")).toBe("1");
    expect(screen.getByText("Risk bildirimi onaylandı.")).toBeInTheDocument();
  });

  it("önceden onaylanmışsa onay notunu gösterir", () => {
    window.localStorage.setItem("dcabot.lab.risk_ack", "1");
    render(<LabPanel />);

    expect(screen.getByText("Risk bildirimi onaylandı.")).toBeInTheDocument();
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });
});
