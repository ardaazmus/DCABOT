import { NextIntlClientProvider } from "next-intl";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import tr from "@/messages/tr.json";
import { EventsFeed } from "./events-feed";

describe("olay akışı", () => {
  it("özetleri zamanla gösterir", () => {
    render(
      <NextIntlClientProvider locale="tr" messages={tr} timeZone="Europe/Istanbul">
        <EventsFeed
          events={[
            { seq: 1, kind: "DEAL_STARTED", ref: "a:1", summary: "A #1 başladı", time_us: 1_000_000 },
            { seq: 2, kind: "BOT_STARTED", ref: "a", summary: "A başlatıldı", time_us: 2_000_000 },
          ]}
        />
      </NextIntlClientProvider>,
    );
    expect(screen.getByText("Olay akışı")).toBeDefined();
    expect(screen.getByText("A #1 başladı")).toBeDefined();
    expect(screen.getByText("A başlatıldı")).toBeDefined();
  });

  it("olay yoksa gizlenir", () => {
    const { container } = render(
      <NextIntlClientProvider locale="tr" messages={tr}>
        <EventsFeed events={[]} />
      </NextIntlClientProvider>,
    );
    expect(container.textContent).toBe("");
  });
});
