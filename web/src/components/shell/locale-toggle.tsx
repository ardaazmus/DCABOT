"use client";

import { useTranslations } from "next-intl";

import { usePrefs } from "@/lib/store";

export function LocaleToggle() {
  const t = useTranslations("topbar");
  const locale = usePrefs((state) => state.locale);
  const setLocale = usePrefs((state) => state.setLocale);
  return (
    <button
      type="button"
      aria-label={t("language")}
      title={t("language")}
      onClick={() => setLocale(locale === "tr" ? "en" : "tr")}
      className="flex h-9 items-center justify-center rounded-lg px-2 font-mono text-xs font-semibold text-muted-foreground hover:bg-muted hover:text-foreground"
    >
      {locale === "tr" ? "TR" : "EN"}
    </button>
  );
}
