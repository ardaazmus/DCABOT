"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { ThemeProvider } from "next-themes";
import { useEffect, useState, type ReactNode } from "react";

import en from "@/messages/en.json";
import tr from "@/messages/tr.json";
import { EventStreamLink } from "@/lib/api/useEventStream";
import { usePrefs, type AppLocale } from "@/lib/store";

const MESSAGES: Record<AppLocale, typeof tr> = { tr, en };

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  });
}

function LocaleProvider({ children }: { children: ReactNode }) {
  const locale = usePrefs((state) => state.locale);
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);
  return (
    <NextIntlClientProvider
      locale={locale}
      messages={MESSAGES[locale]}
      timeZone="Europe/Istanbul"
    >
      {children}
    </NextIntlClientProvider>
  );
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      {/* timeZone: next-intl ENVIRONMENT_FALLBACK uyarısını önleyen genel varsayılan. */}
      <LocaleProvider>
        <QueryClientProvider client={queryClient}>
          <EventStreamLink />
          {children}
        </QueryClientProvider>
      </LocaleProvider>
    </ThemeProvider>
  );
}
