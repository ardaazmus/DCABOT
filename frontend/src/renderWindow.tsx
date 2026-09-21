import { useEffect, useState } from "react";

/**
 * Faz 11 madde 7: uzun listelerde pencere-render. İlk sayfa sınırlı
 * çizilir, kalanı kullanıcı isteğiyle genişler; ilk yük maliyeti
 * sınırlanır, veri kaybı olmaz (canlı sayaç toplamı gösterir).
 */

export function useWindowedList<T>(items: readonly T[], pageSize: number) {
  const [pages, setPages] = useState(1);
  useEffect(() => {
    setPages(1);
  }, [items]);
  const shown = Math.min(pages * pageSize, items.length);
  return {
    visible: items.slice(0, shown),
    shown,
    total: items.length,
    hasMore: shown < items.length,
    showMore: () => setPages((p) => p + 1),
  };
}

export function WindowExpander({ shown, total, onMore }: {
  shown: number;
  total: number;
  onMore: () => void;
}) {
  return (
    <button type="button" className="secondary-button" onClick={onMore}>
      Daha fazla göster ({shown.toLocaleString("tr-TR")}/{total.toLocaleString("tr-TR")})
    </button>
  );
}
