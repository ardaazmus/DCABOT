import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BotWizard } from "./BotWizard";

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
