"use client";

import { Menu } from "lucide-react";
import { useTranslations } from "next-intl";

import { CommandPalette } from "@/components/shell/command-palette";
import { ConnectionDot } from "@/components/shell/connection-dot";
import { KillSwitchBadge } from "@/components/shell/kill-switch-badge";
import { LocaleToggle } from "@/components/shell/locale-toggle";
import { ModeBadge } from "@/components/shell/mode-badge";
import { Notifications } from "@/components/shell/notifications";
import { ThemeToggle } from "@/components/shell/theme-toggle";
import { usePrefs } from "@/lib/store";

export function Topbar() {
  const t = useTranslations("nav");
  const setSidebarOpen = usePrefs((state) => state.setSidebarOpen);
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-card px-3 md:px-4">
      <button
        type="button"
        aria-label={t("open")}
        onClick={() => setSidebarOpen(true)}
        className="flex size-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground lg:hidden"
      >
        <Menu className="size-4" aria-hidden="true" />
      </button>
      <ModeBadge />
      <KillSwitchBadge />
      <ConnectionDot />
      <div className="flex-1" />
      <CommandPalette />
      <ThemeToggle />
      <LocaleToggle />
      <Notifications />
    </header>
  );
}
