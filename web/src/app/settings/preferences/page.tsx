"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePrefs, type AppLocale } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function PreferencesPage() {
  const ts = useTranslations("settings");
  const { resolvedTheme, setTheme } = useTheme();
  const locale = usePrefs((state) => state.locale);
  const setLocale = usePrefs((state) => state.setLocale);

  function themeButton(theme: "dark" | "light", label: string) {
    const selected = (resolvedTheme ?? "dark") === theme;
    return (
      <button
        key={theme}
        type="button"
        aria-pressed={selected}
        onClick={() => setTheme(theme)}
        className={cn(
          "rounded-md px-3 py-1.5 text-sm font-medium",
          selected ? "bg-accent/12 text-accent" : "text-muted-foreground hover:bg-muted",
        )}
      >
        {label}
      </button>
    );
  }

  function localeButton(value: AppLocale, label: string) {
    const selected = locale === value;
    return (
      <button
        key={value}
        type="button"
        aria-pressed={selected}
        onClick={() => setLocale(value)}
        className={cn(
          "rounded-md px-3 py-1.5 font-mono text-sm font-medium",
          selected ? "bg-accent/12 text-accent" : "text-muted-foreground hover:bg-muted",
        )}
      >
        {label}
      </button>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h2>{ts("tabPreferences")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <span className="w-24 text-sm text-muted-foreground">{ts("themeLabel")}</span>
          <div className="flex gap-1">
            {themeButton("dark", ts("themeDark"))}
            {themeButton("light", ts("themeLight"))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="w-24 text-sm text-muted-foreground">{ts("languageLabel")}</span>
          <div className="flex gap-1">
            {localeButton("tr", "Türkçe")}
            {localeButton("en", "English")}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
