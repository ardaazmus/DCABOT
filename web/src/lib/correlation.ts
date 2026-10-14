import type { Bot, MatrixCell } from "@/lib/api/schemas";
import { isGridStrategy } from "@/lib/api/schemas";

/** Matris için bot sembolleri: tekil, sıralı, en fazla 10. */
export function botMatrixSymbols(bots: readonly Bot[]): {
  symbols: string[];
  truncated: boolean;
} {
  const all = new Set<string>();
  for (const bot of bots) {
    all.add(bot.symbol);
    if (!isGridStrategy(bot.strategy) && bot.strategy.symbols !== null) {
      for (const symbol of bot.strategy.symbols) all.add(symbol);
    }
  }
  const sorted = [...all].sort();
  return { symbols: sorted.slice(0, 10), truncated: sorted.length > 10 };
}

/** Üst-üçgen hücreleri tam matrise yansıtır (salt transpoz, hesap yok). */
export function matrixLookup(cells: readonly MatrixCell[]): Map<string, MatrixCell> {
  const lookup = new Map<string, MatrixCell>();
  for (const cell of cells) {
    lookup.set(`${cell.x} ${cell.y}`, cell);
    lookup.set(`${cell.y} ${cell.x}`, cell);
  }
  return lookup;
}
