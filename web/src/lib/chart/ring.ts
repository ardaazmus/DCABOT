/**
 * Kazanma/kaybetme halkası: SVG `pathLength={100}` ile kullanılır, bileşen
 * aritmetik yapmaz (`strokeDasharray={`${win} 100``). Yüzdeler yalnız
 * burada hesaplanır; botsuz durumda iki dilim de sıfırdır.
 */
export function winLossSlices(
  winningDeals: number,
  dealsCompleted: number,
): { win: number; loss: number; losses: number } {
  if (dealsCompleted <= 0) return { win: 0, loss: 0, losses: 0 };
  const wins = Math.min(Math.max(0, winningDeals), dealsCompleted);
  const win = Math.round((wins / dealsCompleted) * 1000) / 10;
  return { win, loss: Math.round((100 - win) * 10) / 10, losses: dealsCompleted - wins };
}
