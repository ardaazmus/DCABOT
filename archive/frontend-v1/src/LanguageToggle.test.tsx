import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { I18nProvider, LANGUAGE_STORAGE_KEY } from "./i18n";

describe("shell language toggle (Faz 12.5)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("TR/EN düğmesi nav etiketlerini tek XML tablosundan çevirir", async () => {
    render(
      <I18nProvider>
        <App />
      </I18nProvider>,
    );
    const nav = await screen.findByRole("navigation", { name: "Ana menü" });
    expect(within(nav).getByRole("link", { name: /Botlar & Stratejiler/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "TR" }));
    expect(within(nav).getByRole("link", { name: /Bots & Strategies/ })).toBeInTheDocument();
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  });

  it("bot stüdyosu sektör terminolojisini gösterir (Baz Emir)", async () => {
    render(
      <I18nProvider>
        <App />
      </I18nProvider>,
    );
    expect((await screen.findAllByText("Baz Emir")).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Güvenlik Emri Sayısı").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Fiyat Sapması").length).toBeGreaterThanOrEqual(1);
  });
});
