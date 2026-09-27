import type { Metadata } from "next";
import type { ReactNode } from "react";
import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell } from "@/components/shell/app-shell";

export const metadata: Metadata = {
  title: "DCABOT",
  description: "DCA trading bot arayüzü",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="tr" suppressHydrationWarning className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
