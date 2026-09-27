"use client";

import { Dialog } from "@base-ui/react/dialog";
import { Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useExchangeSymbols } from "@/lib/api/queries";
import {
  filterCommands,
  type CommandItem,
} from "@/lib/command-filter";
import { cn } from "@/lib/utils";

const PAGE_KEYS = ["dashboard", "bots", "deals", "backtest", "market", "settings"] as const;
const PAGE_HREFS: Record<(typeof PAGE_KEYS)[number], string> = {
  dashboard: "/",
  bots: "/bots",
  deals: "/deals",
  backtest: "/backtest",
  market: "/market",
  settings: "/settings",
};

export function CommandPalette() {
  const t = useTranslations("palette");
  const tNav = useTranslations("nav");
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const symbols = useExchangeSymbols(open);

  const pages: CommandItem[] = useMemo(
    () =>
      PAGE_KEYS.map((key) => ({
        id: `page:${key}`,
        label: tNav(key),
        hint: PAGE_HREFS[key],
      })),
    [tNav],
  );

  const symbolItems: CommandItem[] = useMemo(
    () =>
      (symbols.data?.symbols ?? []).map((entry) => ({
        id: `symbol:${entry.symbol}`,
        label: entry.symbol,
        hint: entry.status,
      })),
    [symbols.data],
  );

  const pageResults = useMemo(
    () => filterCommands(pages, query, 6),
    [pages, query],
  );
  const symbolResults = useMemo(
    () => filterCommands(symbolItems, query, 8),
    [symbolItems, query],
  );
  const results = useMemo(
    () => [...pageResults, ...symbolResults],
    [pageResults, symbolResults],
  );

  function setPaletteOpen(next: boolean) {
    if (next) {
      setQuery("");
      setActive(0);
    }
    setOpen(next);
  }

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (!open) {
          setQuery("");
          setActive(0);
        }
        setOpen(!open);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  function go(item: CommandItem) {
    setOpen(false);
    if (item.id.startsWith("page:")) {
      router.push(item.hint ?? "/");
    } else {
      router.push(`/market/${item.label}`);
    }
  }

  function onInputKey(event: React.KeyboardEvent) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((value) => Math.min(results.length - 1, value + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((value) => Math.max(0, value - 1));
    } else if (event.key === "Enter") {
      const item = results[active];
      if (item !== undefined) go(item);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setPaletteOpen(true)}
        aria-label={t("open")}
        title={t("open")}
        className="flex h-9 items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm text-muted-foreground hover:bg-muted"
      >
        <Search className="size-4" aria-hidden="true" />
        <span className="hidden xl:inline">{t("placeholder")}</span>
        <kbd className="hidden rounded border border-border bg-muted px-1 font-mono text-xs md:inline">
          Ctrl K
        </kbd>
      </button>
      <Dialog.Root open={open} onOpenChange={setPaletteOpen}>
        <Dialog.Portal>
          <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/60" />
          <Dialog.Popup
            aria-label={t("title")}
            className="fixed top-[15%] left-1/2 z-50 w-full max-w-lg -translate-x-1/2 rounded-xl border border-border bg-card text-card-foreground"
          >
            <div className="flex items-center gap-2 border-b border-border px-4">
              <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <input
                type="text"
                role="combobox"
                aria-expanded="true"
                aria-controls="command-list"
                aria-activedescendant={results[active]?.id}
                aria-label={t("placeholder")}
                placeholder={t("placeholder")}
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setActive(0);
                }}
                onKeyDown={onInputKey}
                autoFocus
                className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              />
            </div>
            <ol id="command-list" role="listbox" aria-label={t("title")} className="max-h-80 overflow-y-auto p-2">
              {results.length === 0 ? (
                <li className="px-3 py-6 text-center text-sm text-muted-foreground">
                  {symbols.isPending && query.trim() !== ""
                    ? t("loading")
                    : t("noResults")}
                </li>
              ) : (
                results.map((item, index) => (
                  <li
                    key={item.id}
                    id={item.id}
                    role="option"
                    aria-selected={index === active}
                    onMouseMove={() => setActive(index)}
                    onClick={() => go(item)}
                    className={cn(
                      "flex cursor-pointer items-center justify-between gap-4 rounded-lg px-3 py-2 text-sm",
                      index === active && "bg-accent/12",
                    )}
                  >
                    <span>{item.label}</span>
                    {item.hint === undefined ? null : (
                      <span className="font-mono text-xs text-muted-foreground">
                        {item.hint}
                      </span>
                    )}
                  </li>
                ))
              )}
            </ol>
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
