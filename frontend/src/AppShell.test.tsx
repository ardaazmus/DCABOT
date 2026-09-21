import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

import { APP_SECTIONS, type AppSectionId } from "./appSections";
import { SectionNav } from "./SectionNav";
import { applyTheme, resolveTheme } from "./theme";

describe("appSections", () => {
  it("tam olarak 5 bölüm tanımlar (M3 nav sınırı)", () => {
    expect(APP_SECTIONS.map((section) => section.id)).toEqual([
      "overview",
      "bots",
      "market",
      "events",
      "settings",
    ]);
  });

  it("her bölümün Türkçe etiketi, başlığı ve simgesi vardır", () => {
    for (const section of APP_SECTIONS) {
      expect(section.label.length).toBeGreaterThan(0);
      expect(section.heading.length).toBeGreaterThan(0);
      expect(section.icon.length).toBeGreaterThan(0);
    }
    expect(APP_SECTIONS.map((section) => section.label)).toEqual([
      "Genel Bakış",
      "Botlar & Stratejiler",
      "Piyasa & Veri",
      "Olaylar & Denetim",
      "Ayarlar",
    ]);
  });
});

describe("SectionNav", () => {
  it("5 bölümü link olarak gösterir, aktif bölümü işaretler", () => {
    const onSelect = vi.fn();
    render(<SectionNav active="bots" onSelect={onSelect} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    const links = within(nav).getAllByRole("link");
    expect(links).toHaveLength(5);
    const active = within(nav).getByRole("link", { name: /Botlar & Stratejiler/ });
    expect(active).toHaveAttribute("aria-current", "page");
    expect(active.className).toMatch(/active/);
  });

  it("tıklama yalnızca onSelect çağırır, sayfa yenilemez", () => {
    const onSelect = vi.fn();
    render(<SectionNav active="bots" onSelect={onSelect} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    const target = within(nav).getByRole("link", { name: /Piyasa & Veri/ });
    fireEvent.click(target);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith("market");
  });

  it("geçersiz aktif id gelirse hiçbir öğeyi aktif göstermez", () => {
    render(<SectionNav active={"unknown" as AppSectionId} onSelect={() => {}} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    expect(nav.querySelector('[aria-current="page"]')).toBeNull();
  });
});

describe("App section shell", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("5 bölümü ve bot stüdyosu içeriğini gösterir", async () => {
    render(<App />);
    const nav = await screen.findByRole("navigation", { name: "Ana menü" });
    expect(within(nav).getAllByRole("link")).toHaveLength(5);
    expect(await screen.findByRole("heading", { name: "Botlar & Stratejiler" })).toBeInTheDocument();
    expect(screen.getByText("Bot stüdyosu", { selector: "h2" })).toBeInTheDocument();
  });

  it("bölümler gerçek panelleri gösterir, yer tutucu kalmaz", async () => {
    render(<App />);
    const nav = await screen.findByRole("navigation", { name: "Ana menü" });
    fireEvent.click(within(nav).getByRole("link", { name: /Genel Bakış/ }));
    expect(await screen.findByRole("heading", { name: "Portföy özeti" })).toBeInTheDocument();
    fireEvent.click(within(nav).getByRole("link", { name: /Ayarlar/ }));
    expect(await screen.findByRole("heading", { name: "Testnet hesap görünümü" })).toBeInTheDocument();
    fireEvent.click(within(nav).getByRole("link", { name: /Olaylar & Denetim/ }));
    expect(await screen.findByRole("heading", { name: "Olay merkezi" })).toBeInTheDocument();
    expect(screen.queryByText(/henüz bağlı değil/)).not.toBeInTheDocument();
  });

  it("tema düğmesi data-theme özniteliğini çevirir", async () => {
    render(<App />);
    const header = await screen.findByRole("banner");
    const toggle = within(header).getByRole("button", { name: /Koyu|Açık/ });
    expect(document.documentElement.dataset.theme).toBe("dark");
    fireEvent.click(toggle);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });
});

describe("theme", () => {
  it("kayıtlı tema sistem tercihini ezer, kayıt yoksa sistemi kullanır", () => {
    expect(resolveTheme("light", () => true)).toBe("light");
    expect(resolveTheme("dark", () => true)).toBe("dark");
    expect(resolveTheme(null, () => true)).toBe("light");
    expect(resolveTheme(null, () => false)).toBe("dark");
    expect(resolveTheme("geçersiz", () => true)).toBe("light");
  });

  it("applyTheme kök öğeye data-theme yazar", () => {
    applyTheme(document.documentElement, "light");
    expect(document.documentElement.dataset.theme).toBe("light");
    applyTheme(document.documentElement, "dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
