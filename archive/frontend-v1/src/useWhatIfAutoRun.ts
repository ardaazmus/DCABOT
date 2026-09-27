import { useEffect, useRef, useState } from "react";

// B.5 (=17.11) What-If: koşu planı değişince tarihsel simülasyonu otomatik
// tetikleyen debounce katmanı. Yalnız zamanlama yapar; hesap, kayıt veya
// kayıt kararı içermez. Her plan anahtarı için en fazla bir kez ateşlenir,
// hata sonrası aynı anahtarla yeniden denemez (manuel buton her zaman açık).
export const WHAT_IF_AUTO_RUN_DELAY_MS = 800;

export function useWhatIfAutoRun({
  enabled,
  planKey,
  delayMs = WHAT_IF_AUTO_RUN_DELAY_MS,
  onAutoRun,
}: {
  enabled: boolean;
  planKey: string | null;
  delayMs?: number;
  onAutoRun: () => void;
}): { pending: boolean } {
  const [pending, setPending] = useState(false);
  const firedKeyRef = useRef<string | null>(null);
  const onAutoRunRef = useRef(onAutoRun);
  onAutoRunRef.current = onAutoRun;

  useEffect(() => {
    if (!enabled || planKey === null || firedKeyRef.current === planKey) {
      setPending(false);
      return;
    }
    setPending(true);
    const timer = window.setTimeout(() => {
      firedKeyRef.current = planKey;
      setPending(false);
      onAutoRunRef.current();
    }, delayMs);
    return () => {
      window.clearTimeout(timer);
      setPending(false);
    };
  }, [enabled, planKey, delayMs]);

  return { pending };
}
