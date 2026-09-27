"use client";

import { useTranslations } from "next-intl";

import { PRESET_IDS, type PresetId } from "@/lib/bots";
import { cn } from "@/lib/utils";

/** Hazır ayar seçici; sihirbaz ve backtest aynı bileşeni kullanır. */
export function PresetPicker({
  preset,
  onPreset,
}: {
  preset: PresetId;
  onPreset: (id: Exclude<PresetId, "custom">) => void;
}) {
  const t = useTranslations("wizard");
  return (
    <fieldset>
      <legend className="text-sm font-medium">{t("presetLabel")}</legend>
      <div className="mt-2 flex flex-wrap gap-2" role="radiogroup" aria-label={t("presetLabel")}>
        {PRESET_IDS.map((id) => (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={preset === id}
            onClick={() => onPreset(id)}
            className={cn(
              "rounded-md border px-4 py-2 text-sm font-medium",
              preset === id
                ? "border-accent bg-accent/12 text-accent"
                : "border-input hover:bg-muted",
            )}
          >
            {t(
              id === "conservative"
                ? "presetConservative"
                : id === "balanced"
                  ? "presetBalanced"
                  : "presetAggressive",
            )}
          </button>
        ))}
        <span
          aria-label={t("presetCustom")}
          data-state={preset === "custom" ? "on" : "off"}
          className={cn(
            "rounded-md border px-4 py-2 text-sm",
            preset === "custom"
              ? "border-accent bg-accent/12 text-accent"
              : "border-input text-muted-foreground",
          )}
        >
          {t("presetCustom")}
        </span>
      </div>
    </fieldset>
  );
}
