export type AppSectionId =
  | "overview"
  | "bots"
  | "create"
  | "deals"
  | "backtest"
  | "lab"
  | "risk"
  | "market"
  | "system";

export type AppSection = {
  id: AppSectionId;
  label: string;
  heading: string;
  icon: string;
  /** Sidebar grup başlığı; boşsa grupsuz (en üst) gösterilir. */
  group: string;
  intent: string;
};

/** Faz AB.1: 9-öğe nav — Faz 11'in "kalıcı 5-bölüm" kararı geçersiz kılındı. */
export const APP_SECTIONS: AppSection[] = [
  {
    id: "overview",
    label: "Genel Bakış",
    heading: "Genel Bakış",
    icon: "📊",
    group: "",
    intent: "Portföy/bot özeti, canlı grafik ve durum akışı.",
  },
  {
    id: "bots",
    label: "Botlarım",
    heading: "Botlarım",
    icon: "🤖",
    group: "Botlar",
    intent: "Bot tablosu, bot bağlamı ve motor-detay şeridi.",
  },
  {
    id: "create",
    label: "Bot Kur",
    heading: "Bot Kur",
    icon: "➕",
    group: "Botlar",
    intent: "Tek oluşturma yolu: stüdyo + Bot Oluştur görünümü.",
  },
  {
    id: "deals",
    label: "Aktif İşlemler",
    heading: "Aktif İşlemler",
    icon: "💼",
    group: "Botlar",
    intent: "Deal paneli, DCA seansları, exit, zaman çizgisi, paper.",
  },
  {
    id: "backtest",
    label: "Backtest",
    heading: "Backtest",
    icon: "⚙️",
    group: "Analiz",
    intent: "Dataset kataloğu, optimizasyon, overfitting, kayıtlı koşular.",
  },
  {
    id: "lab",
    label: "Strateji Lab",
    heading: "Strateji Lab",
    icon: "🧪",
    group: "Analiz",
    intent: "Preset karşılaştırma, şablonlar, portföy, rebalance, sinyal, futures.",
  },
  {
    id: "risk",
    label: "Risk",
    heading: "Risk",
    icon: "🛡️",
    group: "Analiz",
    intent: "Kill-switch/canary, işlem-engeli açıklaması, korelasyon, rejim.",
  },
  {
    id: "market",
    label: "Piyasa & Veri",
    heading: "Piyasa & Veri",
    icon: "📈",
    group: "Veri & Sistem",
    intent: "Sembol grafiği, venue snapshot, order book, veri merkezi.",
  },
  {
    id: "system",
    label: "Sistem",
    heading: "Sistem",
    icon: "🧰",
    group: "Veri & Sistem",
    intent: "Olay merkezi, yedek, sağlık, kayıt defteri, testnet hesabı.",
  },
];

export function sectionById(id: AppSectionId): AppSection | undefined {
  return APP_SECTIONS.find((section) => section.id === id);
}
