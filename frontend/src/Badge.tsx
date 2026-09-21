export type BadgeTone = "ok" | "warn" | "neutral" | "closed";

/**
 * Faz 15.5: DCABOT-native güven rozetleri için tek görsel bileşen.
 * Etiket/tooltip çağırandan gelir (i18n kararı çağıran dosyaya aittir);
 * rozet yalnız gerçekten doğrulanmış durumu gösterir, kendi başına
 * bir iddia üretmez.
 */
export function Badge({ tone, label, title }: { tone: BadgeTone; label: string; title?: string }) {
  return (
    <span className={`badge badge-${tone}`} title={title}>
      {label}
    </span>
  );
}
