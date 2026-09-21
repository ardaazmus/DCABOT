import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { I18nProvider, LANGUAGE_STORAGE_KEY, parseStringsXml, useI18n } from "./i18n";

const SAMPLE_XML = `<?xml version="1.0" encoding="UTF-8"?>
<resources>
  <string key="nav.bots.label"><tr>Botlar &amp; Stratejiler</tr><en>Bots &amp; Strategies</en></string>
  <string key="only.tr"><tr>Yalnızca TR</tr></string>
</resources>`;

function Probe({ storageKey }: { storageKey?: string }) {
  const { lang, setLang, t } = useI18n();
  return (
    <div>
      <p data-testid="probed">{t("nav.bots.label")}</p>
      <p data-testid="fallback">{t("only.tr")}</p>
      <p data-testid="missing">{t("no.such.key")}</p>
      <p data-testid="lang">{lang}</p>
      <button type="button" onClick={() => setLang(lang === "tr" ? "en" : "tr")}>
        switch
      </button>
      {storageKey && <p data-testid="storage">{storageKey}</p>}
    </div>
  );
}

describe("parseStringsXml", () => {
  it("parses tr/en children per key", () => {
    const table = parseStringsXml(SAMPLE_XML);
    expect(table["nav.bots.label"]).toEqual({ tr: "Botlar & Stratejiler", en: "Bots & Strategies" });
    expect(table["only.tr"]).toEqual({ tr: "Yalnızca TR" });
  });

  it("fails closed on malformed xml", () => {
    expect(parseStringsXml("not <xml")).toEqual({});
    expect(parseStringsXml("")).toEqual({});
  });

  it("ignores entries without a key", () => {
    const table = parseStringsXml(`<resources><string><tr>X</tr></string></resources>`);
    expect(table).toEqual({});
  });
});

describe("I18nProvider", () => {
  it("translates from the single strings.xml table", () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId("probed")).toHaveTextContent("Botlar & Stratejiler");
  });

  it("switches language and persists the choice", () => {
    window.localStorage.clear();
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    fireEvent.click(screen.getByRole("button", { name: "switch" }));
    expect(screen.getByTestId("probed")).toHaveTextContent("Bots & Strategies");
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  });

  it("falls back to Turkish, then to the key itself", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    render(
      <I18nProvider strings={SAMPLE_XML}>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId("fallback")).toHaveTextContent("Yalnızca TR");
    expect(screen.getByTestId("missing")).toHaveTextContent("no.such.key");
    window.localStorage.clear();
  });

  it("restores the stored language on mount", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId("lang")).toHaveTextContent("en");
    window.localStorage.clear();
  });
});

describe("useI18n without provider", () => {
  it("fails closed to Turkish defaults", () => {
    render(<Probe />);
    expect(screen.getByTestId("probed")).toHaveTextContent("Botlar & Stratejiler");
  });
});
