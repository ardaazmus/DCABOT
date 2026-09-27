import { create } from "zustand";

const STORAGE_KEY = "dcabot.favorites.v1";

function loadFavorites(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === null) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((entry): entry is string => typeof entry === "string");
  } catch {
    return [];
  }
}

function saveFavorites(symbols: readonly string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols));
  } catch {
    // Yok sayılır: depo bellek içinde çalışmaya devam eder.
  }
}

type FavoritesState = {
  symbols: string[];
  toggle: (symbol: string) => void;
};

export const useFavorites = create<FavoritesState>()((set) => ({
  symbols: loadFavorites(),
  toggle: (symbol) =>
    set((state) => {
      const symbols = state.symbols.includes(symbol)
        ? state.symbols.filter((entry) => entry !== symbol)
        : [...state.symbols, symbol];
      saveFavorites(symbols);
      return { symbols };
    }),
}));

export function isFavorite(symbols: readonly string[], symbol: string): boolean {
  return symbols.includes(symbol);
}
