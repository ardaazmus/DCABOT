"use client";

import { useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

/** Bot detayı sekmeleri (Genel/Deal'ler/İstatistik/Olay kaydı). */
export function BotTabs({
  tabs,
  label = "Bot",
}: {
  tabs: readonly { id: string; label: string; panel: ReactNode }[];
  label?: string;
}) {
  const [active, setActive] = useState(tabs[0]?.id ?? "");
  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];
  return (
    <div className="flex flex-col gap-4">
      <div role="tablist" aria-label={label} className="flex gap-1 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={tab.id === current?.id}
            onClick={() => setActive(tab.id)}
            className={cn(
              "-mb-px border-b-2 px-3 py-2 text-sm font-medium",
              tab.id === current?.id
                ? "border-accent text-accent"
                : "border-transparent text-muted-foreground",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div role="tabpanel">{current?.panel}</div>
    </div>
  );
}
