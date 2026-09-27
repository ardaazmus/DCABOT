import { create } from "zustand";

export type AppLocale = "tr" | "en";

type PrefsState = {
  locale: AppLocale;
  setLocale: (locale: AppLocale) => void;
  /** Dar ekranda kenar menü çekmecesi açık mı. */
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
};

export const usePrefs = create<PrefsState>()((set) => ({
  locale: "tr",
  setLocale: (locale) => set({ locale }),
  sidebarOpen: false,
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
}));
