"use client";

import { Moon, Sun } from "lucide-react";
import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const t = useTranslations("topbar");
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme !== "light";
  return (
    <button
      type="button"
      aria-label={t("theme")}
      title={t("theme")}
      onClick={() => setTheme(dark ? "light" : "dark")}
      className="flex size-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"
    >
      {dark ? (
        <Sun className="size-4" aria-hidden="true" />
      ) : (
        <Moon className="size-4" aria-hidden="true" />
      )}
    </button>
  );
}
