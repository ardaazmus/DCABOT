import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BotWizard, readDraftPreviewParams } from "./BotWizard";

const DRAFT_PREFIX = "dcabot-strategy-draft:";

function renderWizard() {
  const onRegister = vi.fn();
  const onOpenBacktest = vi.fn();
  render(<BotWizard busy={false} error="" onRegister={onRegister} onOpenBacktest={onOpenBacktest} />);
  return { onRegister, onOpenBacktest };
}

function renderWizardOptimize() {
  const onRegister = vi.fn();
  const onOpenBacktest = vi.fn();
  render(
    <BotWizard
      busy={false}
      error=""
      onRegister={onRegister}
      onOpenBacktest={onOpenBacktest}
      optimizeDatasetId="ds-1"
      optimizeProfileId="prof-1"
    />,
  );
  return { onRegister, onOpenBacktest };
}

function renderWizardWithBars(closes: string[]) {
  const onRegister = vi.fn();
  const onOpenBacktest = vi.fn();
  render(
    <BotWizard
      busy={false}
      error=""
      onRegister={onRegister}
      onOpenBacktest={onOpenBacktest}
      chartBars={closes.map((close, index) => ({
        bar_index: index,
        open_time_us: index * 60000000,
        close_time_us: index * 60000000 + 59999999,
        open: close,
        high: close,
        low: close,
        close,
        base_volume: "1",
      }))}
    />,
  );
  return { onRegister, onOpenBacktest };
}

function next() {
  fireEvent.click(screen.getByRole("button", { name: "İleri" }));
}

function fillIdentity() {
  fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-9" } });
  fireEvent.change(screen.getByLabelText("Bot adı"), { target: { value: "Deneme" } });
  fireEvent.change(screen.getByLabelText("Parite 1"), { target: { value: "BTCUSDT" } });
  fireEvent.click(screen.getByRole("button", { name: /Pair ekle/ }));
  fireEvent.change(screen.getByLabelText("Parite 2"), { target: { value: "ETHUSDT" } });
}

describe("BotWizard (birleşik akış, Faz 12.2)", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("geçersiz kimlikle ilerlemez", () => {
    renderWizard();
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("Bot kimliği geçersiz");
  });

  it("5 adımı tamamlayıp typed payload gönderir ve taslağı saklar", () => {
    const { onRegister } = renderWizard();
    fillIdentity();
    next();
    expect(screen.getByText("Adım 2/5 · Giriş")).toBeInTheDocument();
    next();
    expect(screen.getByText("Adım 3/5 · Çıkış")).toBeInTheDocument();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    expect(screen.getByText("Adım 5/5 · Önizleme")).toBeInTheDocument();
    expect(screen.getAllByText("Baz Emir").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Kâr Al (TP)").length).toBeGreaterThanOrEqual(1);
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    expect(onRegister).toHaveBeenCalledWith({
      bot_id: "bot-9",
      name: "Deneme",
      pairs: ["BTCUSDT", "ETHUSDT"],
      blacklist: [],
      favorites: [],
      virtual_quote_budget: "10000",
    });
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.baseQty).toBe("0.001");
    expect(draft.takeProfit).toBe("0.01");
    expect(draft.startCondition).toBe("immediate");
  });

  it("yinelenen pair ve negatif bütçeyi engeller", () => {
    renderWizard();
    fireEvent.change(screen.getByLabelText("Bot kimliği"), { target: { value: "bot-9" } });
    fireEvent.change(screen.getByLabelText("Bot adı"), { target: { value: "Deneme" } });
    fireEvent.change(screen.getByLabelText("Parite 1"), { target: { value: "BTCUSDT" } });
    fireEvent.click(screen.getByRole("button", { name: /Pair ekle/ }));
    fireEvent.change(screen.getByLabelText("Parite 2"), { target: { value: "BTCUSDT" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("benzersiz");
    fireEvent.click(screen.getByRole("button", { name: "Parite 2 kaldır" }));
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "-5" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("exact decimal");
  });

  it("bozuk giriş/çıkış değerleriyle ilerlemez", () => {
    renderWizard();
    fillIdentity();
    next();
    fireEvent.change(screen.getByLabelText("Fiyat Sapması"), { target: { value: "abc" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("Fiyat Sapması");
    fireEvent.change(screen.getByLabelText("Fiyat Sapması"), { target: { value: "0.02" } });
    next();
    fireEvent.change(screen.getByLabelText("Kâr Al (TP)"), { target: { value: "xx" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("Kâr Al");
  });

  it("geriye dönük test düğmesi backtest yüzeyini açar", () => {
    const { onOpenBacktest } = renderWizard();
    fillIdentity();
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "100" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Geriye Dönük Test" }));
    expect(onOpenBacktest).toHaveBeenCalledTimes(1);
  });

  it("15.2: güvenlik adedi stepper ile değişir", () => {
    renderWizard();
    fillIdentity();
    next();
    fireEvent.click(screen.getByRole("button", { name: /Güvenlik Emri Sayısı artır/ }));
    expect(screen.getByLabelText("Güvenlik Emri Sayısı")).toHaveValue("4");
  });

  it("15.2: çarpanlar etiketli slider ile seçilir", () => {
    renderWizard();
    fillIdentity();
    next();
    const volume = screen.getByRole("slider", { name: "Hacim Çarpanı" });
    fireEvent.change(volume, { target: { value: "10" } });
    next();
    expect(screen.getByText("Adım 3/5 · Çıkış")).toBeInTheDocument();
  });

  it("15.2: TP çipi exact oranı yazar", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    fireEvent.click(screen.getByRole("button", { name: "5%" }));
    expect(screen.getByLabelText("Kâr Al (TP)")).toHaveValue("0.05");
  });

  it("15.2: SL anahtarı alanı açar/kapatır, kapalıyken değer silinir", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    const toggle = screen.getByRole("switch", { name: "Zararı Durdur (SL)" });
    expect(document.querySelector('input[name="wizard_stop_loss"]')).not.toBeInTheDocument();
    fireEvent.click(toggle);
    expect(document.querySelector('input[name="wizard_stop_loss"]')).toHaveValue("0.01");
    fireEvent.click(screen.getByRole("switch", { name: "Zararı Durdur (SL)" }));
    expect(document.querySelector('input[name="wizard_stop_loss"]')).not.toBeInTheDocument();
  });

  it("15.3: pair satırları eklenir/kaldırılır, CSV eşzamanlı kalır", () => {
    renderWizard();
    fillIdentity();
    fireEvent.click(screen.getByRole("button", { name: /Pair ekle/ }));
    fireEvent.change(screen.getByLabelText("Parite 3"), { target: { value: "SOLUSDT" } });
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "100" } });
    next();
    expect(screen.getByText("Adım 5/5 · Önizleme")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
  });

  it("15.3: hazır ayar şablon yükünü taslağa yazar", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: [{ template_id: "tpl-1", payload_sha256: "ab".repeat(32), declared_capabilities: ["dca"] }] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: {
            template_id: "tpl-1",
            payload_sha256: "ab".repeat(32),
            declared_capabilities: ["dca"],
            payload: { base_qty: "0.5", safety_count: 4, unknown_key: "x" },
          },
        }),
      });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fillIdentity();
      fireEvent.click(screen.getByRole("button", { name: "Hazır ayar kullan" }));
      expect(await screen.findByText("tpl-1")).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Uygula" }));
      expect(await screen.findByText(/Doldurulan alan: 2/)).toBeInTheDocument();
      next();
      expect(screen.getByLabelText("Baz Emir")).toHaveValue("0.5");
      expect(screen.getByLabelText("Güvenlik Emri Sayısı")).toHaveValue("4");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("başlatma koşulu taslağa yazılır", () => {
    renderWizard();
    fillIdentity();
    fireEvent.click(screen.getByRole("radio", { name: "Webhook" }));
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "100" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.startCondition).toBe("webhook");
  });

  it("15.6: başlatma koşulu segmenttir, dropdown yok", () => {
    renderWizard();
    expect(screen.getByRole("radio", { name: "Hemen" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "İndikatör" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Webhook" })).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Bot Başlatma Koşulu" })).not.toBeInTheDocument();
  });

  it("15.6: indikatör seçilince kesişim formu açılır, hemen seçilince kapanır", () => {
    renderWizard();
    expect(screen.queryByLabelText("Hızlı Periyot")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: "İndikatör" }));
    expect(screen.getByLabelText("Hızlı Periyot")).toBeInTheDocument();
    expect(screen.getByLabelText("Yavaş Periyot")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "SMA" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "EMA" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Yukarı Kesim" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Aşağı Kesim" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sinyali önizle" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: "Hemen" }));
    expect(screen.queryByLabelText("Hızlı Periyot")).not.toBeInTheDocument();
  });

  it("15.6: önizleme kesişimleri backend'den getirir", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { fast: [], slow: [], events: [{ index: 4, direction: "GOLDEN" }] } }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizardWithBars(["3", "2", "1", "2", "3"]);
      fireEvent.click(screen.getByRole("radio", { name: "İndikatör" }));
      fireEvent.change(screen.getByLabelText("Hızlı Periyot"), { target: { value: "2" } });
      fireEvent.change(screen.getByLabelText("Yavaş Periyot"), { target: { value: "3" } });
      fireEvent.click(screen.getByRole("button", { name: "Sinyali önizle" }));
      expect(await screen.findByText("Bar 4 · Yukarı Kesim")).toBeInTheDocument();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/signals/indicators/cross",
        expect.objectContaining({ method: "POST" }),
      );
      const body = JSON.parse(fetchMock.mock.calls[0][1].body as string) as Record<string, unknown>;
      expect(body).toEqual({ closes: ["3", "2", "1", "2", "3"], fast_window: 2, slow_window: 3, kind: "sma" });
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("15.6: veri yokken önizleme boş-durum gösterir, istek atmaz", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fireEvent.click(screen.getByRole("radio", { name: "İndikatör" }));
      fireEvent.click(screen.getByRole("button", { name: "Sinyali önizle" }));
      expect(screen.getByText("Önce grafik verisi yükleyin")).toBeInTheDocument();
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("15.6: webhook seçilince URL görünür", () => {
    renderWizard();
    expect(screen.queryByText("/api/signals/webhook/tradingview")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: "Webhook" }));
    expect(screen.getByText("/api/signals/webhook/tradingview")).toBeInTheDocument();
  });

  it("G.3: maks. aktif safety alanı boş varsayılanla gelir ve taslağa yazılır", () => {
    renderWizard();
    fillIdentity();
    next();
    const field = screen.getByLabelText("Maks. Aktif Safety") as HTMLInputElement;
    expect(field.value).toBe("");
    expect(screen.getByText("Boş bırakılırsa safety sayısı kullanılır.")).toBeInTheDocument();
    fireEvent.change(field, { target: { value: "2" } });
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.maxActive).toBe("2");
  });

  it("G.3: safety sayısını aşan veya bozuk değerle ilerlemez", () => {
    renderWizard();
    fillIdentity();
    next();
    fireEvent.change(screen.getByLabelText("Maks. Aktif Safety"), { target: { value: "9" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("1 ile safety sayısı (3) arasında");
    fireEvent.change(screen.getByLabelText("Maks. Aktif Safety"), { target: { value: "abc" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("boş ya da tam sayı");
    fireEvent.change(screen.getByLabelText("Maks. Aktif Safety"), { target: { value: "" } });
    next();
    expect(screen.getByText("Adım 3/5 · Çıkış")).toBeInTheDocument();
  });

  it.each([
    { payload: { max_active_safety_orders: 2 }, expected: "2", applied: 1 },
    { payload: { max_active_safety_orders: null, safety_count: 5 }, expected: "", applied: 2 },
  ])("G.3: preset değeri $expected olarak alana yansır", async ({ payload, expected, applied }) => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/templates") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ data: [{ template_id: "t1", payload_sha256: "a", declared_capabilities: [] }] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          data: { template_id: "t1", payload_sha256: "a", declared_capabilities: [], payload },
        }),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fireEvent.click(screen.getByRole("button", { name: "Hazır ayar kullan" }));
      expect(await screen.findByRole("button", { name: "Uygula" })).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Uygula" }));
      expect(await screen.findByText(`Doldurulan alan: ${applied}`)).toBeInTheDocument();
      fillIdentity();
      next();
      expect((screen.getByLabelText("Maks. Aktif Safety") as HTMLInputElement).value).toBe(expected);
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("G.2: emir tipleri Limit varsayılanla gelir, slippage gizlidir, taslağa yazılır", () => {
    renderWizard();
    fillIdentity();
    next();
    for (const label of ["Baz emir tipi", "Safety emir tipi", "Çıkış emir tipi", "Stop emir tipi"]) {
      const group = screen.getByRole("radiogroup", { name: label });
      expect(within(group).getByRole("radio", { name: "Limit" })).toHaveAttribute("aria-checked", "true");
    }
    expect(screen.queryByLabelText("Maks. ters slippage (bps)")).not.toBeInTheDocument();
    expect(screen.getByText("Referans fiyat: MARK (sabit).")).toBeInTheDocument();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.baseOrderType).toBe("LIMIT");
    expect(draft.safetyOrderType).toBe("LIMIT");
    expect(draft.exitOrderType).toBe("LIMIT");
    expect(draft.stopOrderType).toBe("LIMIT");
    expect(draft.maxSlippageBps).toBe("");
  });

  it("G.2: Market rol slippage olmadan ilerlemez; 1-9999 dışı reddedilir", () => {
    renderWizard();
    fillIdentity();
    next();
    fireEvent.click(within(screen.getByRole("radiogroup", { name: "Safety emir tipi" })).getByRole("radio", { name: "Market" }));
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("1-9999 tam sayı");
    for (const bad of ["abc", "0", "10000"]) {
      fireEvent.change(screen.getByLabelText("Maks. ters slippage (bps)"), { target: { value: bad } });
      next();
      expect(screen.getByRole("alert")).toHaveTextContent("1-9999 tam sayı");
    }
    fireEvent.change(screen.getByLabelText("Maks. ters slippage (bps)"), { target: { value: "25" } });
    next();
    expect(screen.getByText("Adım 3/5 · Çıkış")).toBeInTheDocument();
  });

  it("G.2: tüm roller Limit iken dolu kalan slippage ilerlemez", () => {
    renderWizard();
    fillIdentity();
    next();
    const group = screen.getByRole("radiogroup", { name: "Çıkış emir tipi" });
    fireEvent.click(within(group).getByRole("radio", { name: "Market" }));
    fireEvent.change(screen.getByLabelText("Maks. ters slippage (bps)"), { target: { value: "25" } });
    fireEvent.click(within(group).getByRole("radio", { name: "Limit" }));
    expect(screen.queryByLabelText("Maks. ters slippage (bps)")).not.toBeInTheDocument();
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("boş olmalıdır");
  });

  it("G.2: preset emir tipi anahtarlarını yoksayar", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/templates") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ data: [{ template_id: "t1", payload_sha256: "a", declared_capabilities: [] }] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          data: {
            template_id: "t1",
            payload_sha256: "a",
            declared_capabilities: [],
            payload: { base_order_type: "MARKET", max_adverse_slippage_bps: "25", safety_count: 5 },
          },
        }),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fireEvent.click(screen.getByRole("button", { name: "Hazır ayar kullan" }));
      expect(await screen.findByRole("button", { name: "Uygula" })).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Uygula" }));
      expect(await screen.findByText("Doldurulan alan: 1")).toBeInTheDocument();
      fillIdentity();
      next();
      const group = screen.getByRole("radiogroup", { name: "Baz emir tipi" });
      expect(within(group).getByRole("radio", { name: "Limit" })).toHaveAttribute("aria-checked", "true");
      expect(screen.queryByLabelText("Maks. ters slippage (bps)")).not.toBeInTheDocument();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("G.1: marjin modu Isolated varsayılanla gelir, uyarı yoktur, taslağa yazılır", () => {
    renderWizard();
    const group = screen.getByRole("radiogroup", { name: "Marjin modu" });
    expect(within(group).getByRole("radio", { name: "Isolated" })).toHaveAttribute("aria-checked", "true");
    expect(screen.queryByText("Cross modda bu botun zararı hesabınızdaki diğer pozisyonları etkileyebilir.")).not.toBeInTheDocument();
    fillIdentity();
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.marginMode).toBe("ISOLATED");
  });

  it("G.1: Cross seçilince 8.1 uyarısı görünür ve taslağa yazılır", () => {
    renderWizard();
    const group = screen.getByRole("radiogroup", { name: "Marjin modu" });
    fireEvent.click(within(group).getByRole("radio", { name: "Cross" }));
    expect(screen.getByRole("note")).toHaveTextContent("Cross modda bu botun zararı hesabınızdaki diğer pozisyonları etkileyebilir.");
    fireEvent.click(within(group).getByRole("radio", { name: "Isolated" }));
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    fireEvent.click(within(group).getByRole("radio", { name: "Cross" }));
    fillIdentity();
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.marginMode).toBe("CROSS");
  });

  it("G.1: preset margin_mode anahtarını yoksayar", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/templates") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ data: [{ template_id: "t1", payload_sha256: "a", declared_capabilities: [] }] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          data: {
            template_id: "t1",
            payload_sha256: "a",
            declared_capabilities: [],
            payload: { margin_mode: "CROSS", safety_count: 5 },
          },
        }),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fireEvent.click(screen.getByRole("button", { name: "Hazır ayar kullan" }));
      expect(await screen.findByRole("button", { name: "Uygula" })).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Uygula" }));
      expect(await screen.findByText("Doldurulan alan: 1")).toBeInTheDocument();
      const group = screen.getByRole("radiogroup", { name: "Marjin modu" });
      expect(within(group).getByRole("radio", { name: "Isolated" })).toHaveAttribute("aria-checked", "true");
      expect(screen.queryByRole("note")).not.toBeInTheDocument();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("H: kademe editörü 2 satırla ilerler ve taslağa JSON yazar", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    fireEvent.click(screen.getByRole("button", { name: "Kademe ekle" }));
    fireEvent.click(screen.getByRole("button", { name: "Kademe ekle" }));
    fireEvent.change(screen.getByLabelText("Kademe 1 Ağırlık"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Kademe 1 Hedef oran"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("Kademe 2 Ağırlık"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Kademe 2 Hedef oran"), { target: { value: "0.02" } });
    expect(screen.getByText("Ağırlıklar toplamı=1 ve artan hedef sırası sunucuda doğrulanır.")).toBeInTheDocument();
    next();
    expect(screen.getByText("Adım 4/5 · Bütçe")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.takeProfitLadder).toBe('[["0.5","0.01"],["0.5","0.02"]]');
  });

  it("H: tek kademe ve bozuk hücreler ilerlemez", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    fireEvent.click(screen.getByRole("button", { name: "Kademe ekle" }));
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("en az 2 kademe");
    fireEvent.click(screen.getByRole("button", { name: "Kademe ekle" }));
    fireEvent.change(screen.getByLabelText("Kademe 1 Ağırlık"), { target: { value: "abc" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("(0,1]");
    for (const bad of ["0", "0.00", "1.5"]) {
      fireEvent.change(screen.getByLabelText("Kademe 1 Ağırlık"), { target: { value: bad } });
      next();
      expect(screen.getByRole("alert")).toHaveTextContent("(0,1]");
    }
    fireEvent.change(screen.getByLabelText("Kademe 1 Ağırlık"), { target: { value: "0.5" } });
    for (const bad of ["0", "1", "1.0", "abc"]) {
      fireEvent.change(screen.getByLabelText("Kademe 1 Hedef oran"), { target: { value: bad } });
      next();
      expect(screen.getByRole("alert")).toHaveTextContent("(0,1)");
    }
    fireEvent.change(screen.getByLabelText("Kademe 1 Hedef oran"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("Kademe 2 Ağırlık"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Kademe 2 Hedef oran"), { target: { value: "0.02" } });
    fireEvent.click(screen.getByRole("button", { name: "Kademe 2 kaldır" }));
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("en az 2 kademe");
  });

  it("H: SL oran aralığı + bar eş-zorunluluğu", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    fireEvent.click(screen.getByRole("switch", { name: "Zararı Durdur (SL)" }));
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("pozitif tam sayı");
    for (const bad of ["0", "-2"]) {
      fireEvent.change(screen.getByLabelText("SL onay barı"), { target: { value: bad } });
      next();
      expect(screen.getByRole("alert")).toHaveTextContent("pozitif tam sayı");
    }
    fireEvent.change(screen.getByLabelText("SL onay barı"), { target: { value: "3" } });
    const stopLossInput = document.querySelector('input[name="wizard_stop_loss"]') as HTMLInputElement;
    fireEvent.change(stopLossInput, { target: { value: "1.5" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("(0,1)");
    fireEvent.change(stopLossInput, { target: { value: "0.05" } });
    next();
    expect(screen.getByText("Adım 4/5 · Bütçe")).toBeInTheDocument();
  });

  it("H: SL kapatılınca bar temizlenir, bayat değer kalmaz", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    fireEvent.click(screen.getByRole("switch", { name: "Zararı Durdur (SL)" }));
    fireEvent.change(screen.getByLabelText("SL onay barı"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("switch", { name: "Zararı Durdur (SL)" }));
    expect(screen.queryByLabelText("SL onay barı")).not.toBeInTheDocument();
    next();
    expect(screen.getByText("Adım 4/5 · Bütçe")).toBeInTheDocument();
  });

  it("H: süre + aksiyon eş-zorunluluğu", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    for (const bad of ["0", "-5"]) {
      fireEvent.change(screen.getByLabelText("Maks. deal süresi (sn)"), { target: { value: bad } });
      next();
      expect(screen.getByRole("alert")).toHaveTextContent("pozitif tam sayı");
    }
    fireEvent.change(screen.getByLabelText("Maks. deal süresi (sn)"), { target: { value: "3600" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("seçilmelidir");
    fireEvent.change(screen.getByLabelText("Süre-dolumu aksiyonu"), { target: { value: "WARN_ONLY" } });
    fireEvent.change(screen.getByLabelText("Maks. deal süresi (sn)"), { target: { value: "" } });
    expect(screen.queryByLabelText("Süre-dolumu aksiyonu")).not.toBeInTheDocument();
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("boş olmalıdır");
    fireEvent.change(screen.getByLabelText("Maks. deal süresi (sn)"), { target: { value: "3600" } });
    next();
    expect(screen.getByText("Adım 4/5 · Bütçe")).toBeInTheDocument();
  });

  it("H: reinvest 0..1 dışı reddedilir, sınırlar geçer", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    expect(screen.getByText(/Deal-kapanış bağlantısı ayrı iş/)).toBeInTheDocument();
    for (const bad of ["abc", "1.5", "-0.1"]) {
      fireEvent.change(screen.getByLabelText("Reinvest oranı"), { target: { value: bad } });
      next();
      expect(screen.getByRole("alert")).toHaveTextContent("0..1");
    }
    fireEvent.change(screen.getByLabelText("Reinvest oranı"), { target: { value: "1" } });
    next();
    expect(screen.getByText("Adım 4/5 · Bütçe")).toBeInTheDocument();
  });

  it("H: preset H anahtarlarını yoksayar", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/templates") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ data: [{ template_id: "t1", payload_sha256: "a", declared_capabilities: [] }] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          data: {
            template_id: "t1",
            payload_sha256: "a",
            declared_capabilities: [],
            payload: {
              take_profit_ladder: [["0.5", "0.01"], ["0.5", "0.02"]],
              stop_loss_rate: "0.05",
              stop_loss_confirmation_bars: 3,
              max_deal_duration_seconds: 3600,
              max_deal_duration_action: "WARN_ONLY",
              safety_count: 5,
            },
          },
        }),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fireEvent.click(screen.getByRole("button", { name: "Hazır ayar kullan" }));
      expect(await screen.findByRole("button", { name: "Uygula" })).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Uygula" }));
      expect(await screen.findByText("Doldurulan alan: 1")).toBeInTheDocument();
      fillIdentity();
      next();
      next();
      expect(screen.queryByLabelText("Kademe 1 Ağırlık")).not.toBeInTheDocument();
      expect((screen.getByLabelText("Reinvest oranı") as HTMLInputElement).value).toBe("");
      expect((screen.getByLabelText("Maks. deal süresi (sn)") as HTMLInputElement).value).toBe("");
      expect(screen.queryByLabelText("Süre-dolumu aksiyonu")).not.toBeInTheDocument();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("I: kâr para birimi Quote varsayılanla gelir, taslağa yazılır", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    const group = screen.getByRole("radiogroup", { name: "Kâr para birimi" });
    expect(within(group).getByRole("radio", { name: "Quote (varsayılan)" })).toHaveAttribute("aria-checked", "true");
    expect(screen.queryByText("Base kâr seçtiniz: bu coin'e uzun vadeli güveniyor olmalısınız.")).not.toBeInTheDocument();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.profitAsset).toBe("QUOTE");
  });

  it("I: Base uyarı + tek-seferlik onay ister", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    const group = screen.getByRole("radiogroup", { name: "Kâr para birimi" });
    fireEvent.click(within(group).getByRole("radio", { name: "Base" }));
    expect(screen.getByRole("note")).toHaveTextContent("Base kâr seçtiniz: bu coin'e uzun vadeli güveniyor olmalısınız.");
    const ack = screen.getByRole("checkbox", { name: "Base kâr riskini anladım, kabul ediyorum" });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("onayı gerekli");
    fireEvent.click(ack);
    expect(screen.queryByRole("checkbox", { name: "Base kâr riskini anladım, kabul ediyorum" })).not.toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("Base kâr seçtiniz");
    next();
    expect(screen.getByText("Adım 4/5 · Bütçe")).toBeInTheDocument();
  });

  it("I: Base + kademe birlikte ilerlemez (onay da bypass edemez)", () => {
    renderWizard();
    fillIdentity();
    next();
    next();
    fireEvent.click(screen.getByRole("button", { name: "Kademe ekle" }));
    fireEvent.click(screen.getByRole("button", { name: "Kademe ekle" }));
    fireEvent.change(screen.getByLabelText("Kademe 1 Ağırlık"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Kademe 1 Hedef oran"), { target: { value: "0.01" } });
    fireEvent.change(screen.getByLabelText("Kademe 2 Ağırlık"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Kademe 2 Hedef oran"), { target: { value: "0.02" } });
    const group = screen.getByRole("radiogroup", { name: "Kâr para birimi" });
    fireEvent.click(within(group).getByRole("radio", { name: "Base" }));
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("birlikte kullanılamaz");
    fireEvent.click(screen.getByRole("checkbox", { name: "Base kâr riskini anladım, kabul ediyorum" }));
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("birlikte kullanılamaz");
  });

  it("I: deal limitleri boş ya da pozitif tam sayı olur, taslağa yazılır", () => {
    renderWizard();
    fillIdentity();
    expect(screen.getByText("Boş = sınırsız. Aşımda reddedilir, kuyruğa alınmaz. Orkestrasyon bağlantısı ayrı iş.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Hesap-geneli maks."), { target: { value: "0" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("pozitif tam sayı");
    fireEvent.change(screen.getByLabelText("Hesap-geneli maks."), { target: { value: "-3" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("pozitif tam sayı");
    fireEvent.change(screen.getByLabelText("Hesap-geneli maks."), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Bot başına maks."), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Aynı paritede maks."), { target: { value: "1" } });
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "10000" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.maxActiveDealsAccount).toBe("10");
    expect(draft.maxActiveDealsPerBot).toBe("2");
    expect(draft.allowedDealsOnSamePair).toBe("1");
  });

  it("I: preset I anahtarlarını yoksayar", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url === "/api/templates") {
        return Promise.resolve({
          ok: true,
          json: async () => ({ data: [{ template_id: "t1", payload_sha256: "a", declared_capabilities: [] }] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({
          data: {
            template_id: "t1",
            payload_sha256: "a",
            declared_capabilities: [],
            payload: {
              profit_asset: "BTC",
              max_active_deals_account: 5,
              max_active_deals_per_bot: 2,
              allowed_deals_on_same_pair: 1,
              safety_count: 5,
            },
          },
        }),
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizard();
      fireEvent.click(screen.getByRole("button", { name: "Hazır ayar kullan" }));
      expect(await screen.findByRole("button", { name: "Uygula" })).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "Uygula" }));
      expect(await screen.findByText("Doldurulan alan: 1")).toBeInTheDocument();
      expect((screen.getByLabelText("Hesap-geneli maks.") as HTMLInputElement).value).toBe("");
      fillIdentity();
      next();
      next();
      const group = screen.getByRole("radiogroup", { name: "Kâr para birimi" });
      expect(within(group).getByRole("radio", { name: "Quote (varsayılan)" })).toHaveAttribute("aria-checked", "true");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("15.6: otomatik ad üretir, çakışanı atlar", () => {
    window.localStorage.setItem(`${DRAFT_PREFIX}dca-bot-1`, JSON.stringify({ name: "dca-bot-1" }));
    renderWizard();
    fireEvent.click(screen.getByRole("button", { name: "Otomatik ad üret" }));
    expect(screen.getByLabelText("Bot adı")).toHaveValue("dca-bot-2");
  });

  it("15.6: indikatör config taslağa yazılır", () => {
    renderWizard();
    fillIdentity();
    fireEvent.click(screen.getByRole("radio", { name: "İndikatör" }));
    fireEvent.click(screen.getByRole("radio", { name: "EMA" }));
    fireEvent.change(screen.getByLabelText("Hızlı Periyot"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Yavaş Periyot"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("radio", { name: "Aşağı Kesim" }));
    next();
    next();
    next();
    fireEvent.change(screen.getByLabelText("Yatırım Tutarı"), { target: { value: "100" } });
    next();
    fireEvent.click(screen.getByRole("button", { name: "Botu kaydet" }));
    const draft = JSON.parse(window.localStorage.getItem(`${DRAFT_PREFIX}bot-9`) ?? "null") as Record<string, string>;
    expect(draft.indicatorKind).toBe("ema");
    expect(draft.fastWindow).toBe("2");
    expect(draft.slowWindow).toBe("3");
    expect(draft.crossCondition).toBe("down");
  });

  it("15.6: geçersiz periyotla ilerlemez", () => {
    renderWizard();
    fillIdentity();
    fireEvent.click(screen.getByRole("radio", { name: "İndikatör" }));
    fireEvent.change(screen.getByLabelText("Hızlı Periyot"), { target: { value: "abc" } });
    next();
    expect(screen.getByRole("alert")).toHaveTextContent("Hızlı Periyot");
  });

  it("15.7: optimize bağlamı yokken dürüst not gösterir", () => {
    renderWizard();
    fillIdentity();
    next();
    expect(screen.getByText(/Optimize için veri seti ve profil gerekir/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Optimize" })).not.toBeInTheDocument();
  });

  it("15.7: öneri forma uygulanır", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: {
          trial_count: 7,
          skipped_count: 2,
          best_metric: "12.5",
          best_recipe_id: "trial-3",
          best_overrides: { deviation: "0.05", take_profit: "0.02" },
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizardOptimize();
      fillIdentity();
      next();
      fireEvent.click(screen.getByRole("button", { name: "Optimize" }));
      expect(await screen.findByText(/En iyi net: 12\.5/)).toBeInTheDocument();
      expect(screen.getByText(/7 deneme · 2 atlandı/)).toBeInTheDocument();
      const body = JSON.parse(fetchMock.mock.calls[0][1].body as string) as Record<string, unknown>;
      expect(body.dataset_id).toBe("ds-1");
      expect(body.profile_id).toBe("prof-1");
      expect(body.max_trials).toBe(9);
      expect(body.sampler).toBe("grid");
      fireEvent.click(screen.getByRole("button", { name: "Öneriyi uygula" }));
      expect(screen.getByLabelText("Fiyat Sapması")).toHaveValue("0.05");
      next();
      expect(screen.getByLabelText("Kâr Al (TP)")).toHaveValue("0.02");
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("15.7: geçersiz deneme sayısıyla istek atılmaz", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizardOptimize();
      fillIdentity();
      next();
      fireEvent.change(screen.getByLabelText("Deneme sayısı"), { target: { value: "abc" } });
      fireEvent.click(screen.getByRole("button", { name: "Optimize" }));
      expect(screen.getByText("Deneme sayısı 1-32 tam sayı olmalı.")).toBeInTheDocument();
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("BotWizard overlay parametre yayını (Faz 17 A.3)", () => {
  function renderWizardOverlay() {
    const onParamsChange = vi.fn();
    render(<BotWizard busy={false} error="" onRegister={vi.fn()} onParamsChange={onParamsChange} />);
    return { onParamsChange };
  }

  it("açılışta varsayılan parametreleri yayınlar", () => {
    const { onParamsChange } = renderWizardOverlay();
    expect(onParamsChange).toHaveBeenCalledTimes(1);
    expect(onParamsChange).toHaveBeenCalledWith({ safetyQty: "0.002", safetyCount: "3", deviation: "0.02" });
  });

  it("güvenlik emri değişiminde güncel değerleri yayınlar", () => {
    const { onParamsChange } = renderWizardOverlay();
    fillIdentity();
    next();
    fireEvent.change(screen.getByLabelText("Güvenlik Emri"), { target: { value: "0.005" } });
    expect(onParamsChange).toHaveBeenLastCalledWith({ safetyQty: "0.005", safetyCount: "3", deviation: "0.02" });
  });

  it("overlay-dışı alan değişiminde yayın yapmaz", () => {
    const { onParamsChange } = renderWizardOverlay();
    fireEvent.change(screen.getByLabelText("Bot adı"), { target: { value: "X" } });
    expect(onParamsChange).toHaveBeenCalledTimes(1);
  });
});

describe("readDraftPreviewParams (Faz 17 A.4)", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  it("eksiksiz taslaktan üçlüyü okur", () => {
    window.localStorage.setItem("dcabot-strategy-draft:bot-1", JSON.stringify({ safetyQty: "0.002", safetyCount: "3", deviation: "0.02", botType: "DCA" }));
    expect(readDraftPreviewParams("bot-1")).toEqual({ safetyQty: "0.002", safetyCount: "3", deviation: "0.02" });
  });

  it("yok/eksik/bozuk taslakta null döner", () => {
    expect(readDraftPreviewParams("bot-9")).toBeNull();
    window.localStorage.setItem("dcabot-strategy-draft:bot-1", JSON.stringify({ safetyQty: "0.002" }));
    expect(readDraftPreviewParams("bot-1")).toBeNull();
    window.localStorage.setItem("dcabot-strategy-draft:bot-2", "{bozuk");
    expect(readDraftPreviewParams("bot-2")).toBeNull();
    window.localStorage.setItem("dcabot-strategy-draft:bot-3", JSON.stringify({ safetyQty: "", safetyCount: "3", deviation: "0.02" }));
    expect(readDraftPreviewParams("bot-3")).toBeNull();
  });
});

describe("AI Önerici görünürlüğü (B.2)", () => {
  it("hazırken başlık + motor adı görünür", () => {
    renderWizardOptimize();
    fillIdentity();
    next();
    expect(screen.getByText("AI Önerici")).toBeInTheDocument();
    expect(screen.getByText(/Motor: ızgara araması/)).toBeInTheDocument();
  });

  it("hazır değilken başlık + dürüst not görünür", () => {
    renderWizard();
    fillIdentity();
    next();
    expect(screen.getByText("AI Önerici")).toBeInTheDocument();
    expect(screen.getByText(/Optimize için veri seti ve profil gerekir/)).toBeInTheDocument();
  });

  it("sonuçta AI rozeti çıkar", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: { trial_count: 7, best_metric: "12.5", best_recipe_id: "trial-3", best_overrides: { deviation: "0.05" } },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    try {
      renderWizardOptimize();
      fillIdentity();
      next();
      fireEvent.click(screen.getByRole("button", { name: "Optimize" }));
      expect(await screen.findByText("AI önerisi")).toBeInTheDocument();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("AA.7b: externalFill taslağa tek-kez uygulanır, bilinmeyen anahtar atlanır", () => {
    render(
      <BotWizard
        busy={false}
        error=""
        onRegister={vi.fn()}
        externalFill={{ values: { take_profit: "0.05", safety_count: 5, bogus_key: "x" }, nonce: 1 }}
      />,
    );
    fillIdentity();
    next();
    expect(screen.getByLabelText("Güvenlik Emri Sayısı")).toHaveValue("5");
    next();
    expect(screen.getByLabelText("Kâr Al (TP)")).toHaveValue("0.05");
  });
});
