"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const TABS = [
  { href: "/settings/connection", key: "tabConnection" },
  { href: "/settings/risk", key: "tabRisk" },
  { href: "/settings/data", key: "tabData" },
  { href: "/settings/system", key: "tabSystem" },
  { href: "/settings/preferences", key: "tabPreferences" },
] as const;

export default function SettingsLayout({ children }: { children: ReactNode }) {
  const t = useTranslations("nav");
  const ts = useTranslations("settings");
  const pathname = usePathname();
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("settings")}</h1>
      <nav aria-label={t("settings")} className="flex flex-wrap gap-1 border-b border-border pb-3">
        {TABS.map((tab) => {
          const active = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium",
                active ? "bg-accent/12 text-accent" : "text-muted-foreground hover:bg-muted",
              )}
            >
              {ts(tab.key)}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
