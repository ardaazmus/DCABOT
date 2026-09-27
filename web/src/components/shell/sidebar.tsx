"use client";

import { Bot, FlaskConical, Globe, LayoutDashboard, Repeat, Settings } from "lucide-react";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { usePrefs } from "@/lib/store";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/", key: "dashboard", Icon: LayoutDashboard },
  { href: "/bots", key: "bots", Icon: Bot },
  { href: "/deals", key: "deals", Icon: Repeat },
  { href: "/backtest", key: "backtest", Icon: FlaskConical },
  { href: "/market", key: "market", Icon: Globe },
  { href: "/settings", key: "settings", Icon: Settings },
] as const;

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  const t = useTranslations("nav");
  const pathname = usePathname();
  return (
    <nav aria-label={t("label")} className="flex flex-col gap-1 p-3">
      {ITEMS.map(({ href, key, Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm",
              active
                ? "bg-accent/12 font-semibold text-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <Icon
              className={cn("size-4 shrink-0", active && "text-accent")}
              aria-hidden="true"
            />
            {t(key)}
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  const t = useTranslations("nav");
  const sidebarOpen = usePrefs((state) => state.sidebarOpen);
  const setSidebarOpen = usePrefs((state) => state.setSidebarOpen);
  const close = () => setSidebarOpen(false);

  return (
    <>
      {/* Masaüstü (>=1024 px): sabit kenar menü. */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card lg:flex">
        <div className="flex h-14 items-center px-6">
          <span className="text-base font-bold tracking-tight">DCABOT</span>
        </div>
        <Nav />
      </aside>

      {/* Dar ekran: açılır çekmece. */}
      {sidebarOpen ? (
        <div className="lg:hidden" role="dialog" aria-modal="true" aria-label={t("label")}>
          <button
            type="button"
            aria-label={t("close")}
            onClick={close}
            className="fixed inset-0 z-40 cursor-default bg-black/60"
          />
          <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-card">
            <div className="flex h-14 items-center justify-between px-4">
              <span className="text-base font-bold tracking-tight">DCABOT</span>
              <button
                type="button"
                onClick={close}
                className="rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-muted"
              >
                {t("close")}
              </button>
            </div>
            <Nav onNavigate={close} />
          </aside>
        </div>
      ) : null}
    </>
  );
}
