export type AppSectionId = "overview" | "bots" | "market" | "events" | "settings";

export type AppSection = {
  id: AppSectionId;
  label: string;
  heading: string;
  icon: string;
  intent: string;
};

/** Faz 11 tasarım kararı madde 1-2: kalıcı 5-bölüm sol nav (M3 sınırı). */
export const APP_SECTIONS: AppSection[] = [
  {
    id: "overview",
    label: "Genel Bakış",
    heading: "Genel Bakış",
    icon: "▦",
    intent: "Botların ve portföyün özet görünümü (Faz 10/F28'de bağlanacak).",
  },
  {
    id: "bots",
    label: "Botlar & Stratejiler",
    heading: "Botlar & Stratejiler",
    icon: "▣",
    intent: "Bot stüdyosu: kurulum, ladder planı, ekonomik özet.",
  },
  {
    id: "market",
    label: "Piyasa & Veri",
    heading: "Piyasa & Veri",
    icon: "◫",
    intent: "Veri katalogu, kalite merkezi ve public snapshot (taşınma Faz 11'de).",
  },
  {
    id: "events",
    label: "Olaylar & Denetim",
    heading: "Olaylar & Denetim",
    icon: "◷",
    intent: "Kaydedilmiş koşular, karşılaştırma ve denetim izi.",
  },
  {
    id: "settings",
    label: "Ayarlar",
    heading: "Ayarlar",
    icon: "⚙",
    intent: "Bağlantı sihirbazı ve uygulama ayarları (Faz 10/F37'de bağlanacak).",
  },
];

export function sectionById(id: AppSectionId): AppSection | undefined {
  return APP_SECTIONS.find((section) => section.id === id);
}
