import { describe, expect, it } from "vitest";

import { enumLabel, hasEnumLabel } from "./enum-labels";

describe("enum sözlüğü", () => {
  it("bilinen kodları çevirir", () => {
    expect(enumLabel("CANARY_NOGO", "tr")).toBe("Canary geçemedi");
    expect(enumLabel("SUCCEEDED", "tr")).toBe("Tamamlandı");
    expect(enumLabel("SUCCEEDED", "en")).toBe("Completed");
  });

  it("bot durum ve modlarını çevirir", () => {
    expect(enumLabel("STOPPED", "tr")).toBe("Durdu");
    expect(enumLabel("PAUSED", "tr")).toBe("Duraklatıldı");
    expect(enumLabel("ERROR", "tr")).toBe("Hata");
    expect(enumLabel("STOPPED", "en")).toBe("Stopped");
    expect(enumLabel("PAPER", "tr")).toBe("Paper");
  });

  it("bilinmeyen kodu ham döndürür", () => {
    expect(enumLabel("YARIN_EKLENECEK", "tr")).toBe("YARIN_EKLENECEK");
    expect(hasEnumLabel("YARIN_EKLENECEK")).toBe(false);
    expect(hasEnumLabel("VERIFIED")).toBe(true);
  });
});
