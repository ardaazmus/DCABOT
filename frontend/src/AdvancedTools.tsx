import type { ReactNode } from "react";

/**
 * Faz 12.2: "Botlar & Stratejiler" ana ekranını sade tutan, varsayılan
 * kapalı gelişmiş-araç grubu (3Commas/Pionex deseni: araştırma araçları
 * ayrı, ana akış sade). İçerik DOM'dadır, yalnız görsel olarak katlıdır.
 */
export function AdvancedTools({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="advanced-tools">
      <summary className="advanced-tools-summary">{title}</summary>
      <div className="advanced-tools-body">{children}</div>
    </details>
  );
}
