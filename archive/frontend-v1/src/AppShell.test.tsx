import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

import { APP_SECTIONS, type AppSectionId } from "./appSections";
import { SectionNav } from "./SectionNav";
import { applyTheme, resolveTheme } from "./theme";

const NINE_IDS = [
  "overview",
  "bots",
  "create",
  "deals",
  "backtest",
  "lab",
  "risk",
  "market",
  "system",
] as const;

const NINE_LABELS = [
  "Genel Bakış",
  "Botlarım",
  "Bot Kur",
  "Aktif İşlemler",
  "Backtest",
  "Strateji Lab",
  "Risk",
  "Piyasa & Veri",
  "Sistem",
];

describe("appSections", () => {
  it("tam olarak 9 bölüm tanımlar (AB.1 nav)", () => {
    expect(APP_SECTIONS.map((section) => section.id)).toEqual([...NINE_IDS]);
  });

  it("her bölümün Türkçe etiketi, başlığı ve simgesi vardır", () => {
    for (const section of APP_SECTIONS) {
      expect(section.label.length).toBeGreaterThan(0);
      expect(section.heading.length).toBeGreaterThan(0);
      expect(section.icon.length).toBeGreaterThan(0);
    }
    expect(APP_SECTIONS.map((section) => section.label)).toEqual(NINE_LABELS);
  });
});

describe("SectionNav", () => {
  it("9 bölümü link olarak gösterir, aktif bölümü işaretler", () => {
    const onSelect = vi.fn();
    render(<SectionNav active="bots" onSelect={onSelect} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    const links = within(nav).getAllByRole("link");
    expect(links).toHaveLength(9);
    const active = within(nav).getByRole("link", { name: /Botlarım/ });
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

  it("linkler hash rota taşır", () => {
    render(<SectionNav active="overview" onSelect={() => {}} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    expect(within(nav).getByRole("link", { name: /Aktif İşlemler/ })).toHaveAttribute("href", "#/deals");
    expect(within(nav).getByRole("link", { name: /Strateji Lab/ })).toHaveAttribute("href", "#/lab");
  });

  it("geçersiz aktif id gelirse hiçbir öğeyi aktif göstermez", () => {
    render(<SectionNav active={"unknown" as AppSectionId} onSelect={() => {}} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    expect(nav.querySelector('[aria-current="page"]')).toBeNull();
  });

  it("AB.1: Lab ana nav'ın içindedir ve grup başlıkları vardır", () => {
    render(<SectionNav active="lab" onSelect={() => {}} />);
    const nav = screen.getByRole("navigation", { name: "Ana menü" });
    const labLink = within(nav).getByRole("link", { name: /Strateji Lab/ });
    expect(labLink).toHaveAttribute("aria-current", "page");
    expect(within(nav).getByText("Botlar")).toBeInTheDocument();
    expect(within(nav).getByText("Analiz")).toBeInTheDocument();
    expect(within(nav).getByText("Veri & Sistem")).toBeInTheDocument();
  });
});

describe("App section shell", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-theme");
    window.location.hash = "";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("varsayılan Genel Bakış açılır: karo satırı + hero + portföy özeti", async () => {
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Genel Bakış" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Özet göstergeler" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Piyasa grafiği/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Portföy özeti" })).toBeInTheDocument();
    expect(window.location.hash).toBe("#/overview");
  });

  it("9 bölüm gerçek panelleri gösterir, yer tutucu kalmaz", async () => {
    render(<App />);
    const nav = await screen.findByRole("navigation", { name: "Ana menü" });
    expect(within(nav).getAllByRole("link")).toHaveLength(9);
    const cases: Array<[RegExp, string, RegExp]> = [
      [/Genel Bakış/, "overview", /Portföy özeti/],
      [/Botlarım/, "bots", /^Botlarım$/],
      [/Bot Kur/, "create", /Bot stüdyosu/],
      [/Aktif İşlemler/, "deals", /Deal lifecycle ve toplu işlem/],
      [/Backtest/, "backtest", /OPT sekmesi/],
      [/Strateji Lab/, "lab", /Whale Wall Detection/],
      [/Risk/, "risk", /Neden işlem açılmıyor/],
      [/Piyasa & Veri/, "market", /Public venue snapshot/],
      [/Sistem/, "system", /Olay merkezi/],
    ];
    for (const [linkName, sectionId, panelName] of cases) {
      fireEvent.click(within(nav).getByRole("link", { name: linkName }));
      expect(await screen.findByRole("heading", { name: panelName })).toBeInTheDocument();
      expect(document.getElementById(`section-${sectionId}`)).not.toBeNull();
      expect(window.location.hash).toBe(`#/${sectionId}`);
    }
    expect(screen.queryByText(/henüz bağlı değil/)).not.toBeInTheDocument();
  });

  it("15.1: overview'da karo satırı hero'dan önce gelir", async () => {
    render(<App />);
    const hero = await screen.findByRole("heading", { name: /Piyasa grafiği/ });
    const workspace = hero.closest(".workspace");
    expect(workspace).not.toBeNull();
    const tiles = workspace!.querySelector('[aria-label="Özet göstergeler"]');
    expect(tiles).not.toBeNull();
    expect(tiles!.compareDocumentPosition(hero) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("15.3: Bot Kur'da + Yeni Bot tek-amaç görünüme geçer, Geri döndürür", async () => {
    render(<App />);
    const nav = await screen.findByRole("navigation", { name: "Ana menü" });
    fireEvent.click(within(nav).getByRole("link", { name: /Bot Kur/ }));
    expect(await screen.findByRole("heading", { name: "Bot Kur" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "+ Yeni Bot" }));
    expect(await screen.findByRole("heading", { name: "Bot Oluştur" })).toBeInTheDocument();
    expect(screen.queryByText("Bot stüdyosu", { selector: "h2" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: "Sinyal Botu" }));
    expect(await screen.findByText("Sinyal botu: indikatör başlatma")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Kapat" }));
    expect(await screen.findByText("Bot stüdyosu", { selector: "h2" })).toBeInTheDocument();
  });

  it("Botlarım'daki oluşturma Bot Kur'a geçirir", async () => {
    render(<App />);
    const nav = await screen.findByRole("navigation", { name: "Ana menü" });
    fireEvent.click(within(nav).getByRole("link", { name: /Botlarım/ }));
    expect(await screen.findByRole("heading", { name: "Botlarım" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yeni bot oluştur" }));
    expect(await screen.findByRole("heading", { name: "Bot Oluştur" })).toBeInTheDocument();
    expect(window.location.hash).toBe("#/create");
  });

  it("üst çubukta tek global sembol seçici vardır", async () => {
    render(<App />);
    await screen.findByRole("navigation", { name: "Ana menü" });
    const header = screen.getByRole("banner");
    const group = within(header).getByRole("group", { name: "Global sembol" });
    expect(within(group).getByRole("searchbox", { name: "Sembol ara" })).toBeInTheDocument();
    expect(within(group).getByRole("combobox", { name: "Global sembol seç" })).toBeInTheDocument();
    expect(within(header).getByRole("status", { name: "Durum şeridi" })).toBeInTheDocument();
    expect(screen.getAllByRole("group", { name: "Global sembol" })).toHaveLength(1);
  });

  it("hash ile açılır, geri/ileri hash'i izler, bilinmeyen overview'a düşer", async () => {
    window.location.hash = "#/risk";
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Risk" })).toBeInTheDocument();
    window.location.hash = "#/deals";
    window.dispatchEvent(new Event("hashchange"));
    expect(await screen.findByRole("heading", { name: "Aktif İşlemler" })).toBeInTheDocument();
    window.location.hash = "#/nope";
    window.dispatchEvent(new Event("hashchange"));
    expect(await screen.findByRole("heading", { name: "Genel Bakış" })).toBeInTheDocument();
  });

  it("derin bağ bot/deal detayını açar", async () => {
    window.location.hash = "#/bots/b-1";
    const { unmount } = render(<App />);
    expect(await screen.findByRole("heading", { name: "Botlarım" })).toBeInTheDocument();
    expect(screen.queryByRole("tablist", { name: "Bot listesi" })).not.toBeInTheDocument();
    expect(window.location.hash).toBe("#/bots/b-1");
    unmount();
    window.location.hash = "#/deals/d-2";
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Aktif İşlemler" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Deal lifecycle ve toplu işlem" })).not.toBeInTheDocument();
    expect(window.location.hash).toBe("#/deals/d-2");
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
