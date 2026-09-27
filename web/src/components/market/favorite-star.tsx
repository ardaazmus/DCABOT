"use client";

import { Star } from "lucide-react";
import { useTranslations } from "next-intl";

import { useFavorites } from "@/lib/favorites";
import { cn } from "@/lib/utils";

export function FavoriteStar({ symbol }: { symbol: string }) {
  const t = useTranslations("market");
  const symbols = useFavorites((state) => state.symbols);
  const toggle = useFavorites((state) => state.toggle);
  const active = symbols.includes(symbol);
  return (
    <button
      type="button"
      aria-pressed={active}
      aria-label={active ? t("removeFavorite") : t("addFavorite")}
      title={active ? t("removeFavorite") : t("addFavorite")}
      onClick={(event) => {
        event.stopPropagation();
        toggle(symbol);
      }}
      className="flex size-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
    >
      <Star
        className={cn("size-4", active && "fill-safety text-safety")}
        aria-hidden="true"
      />
    </button>
  );
}
