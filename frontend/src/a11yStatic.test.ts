import { describe, expect, it } from "vitest";

import css from "./styles.css?raw";
import html from "../index.html?raw";

/**
 * F30: statik erişilebilirlik kapısı. Klavye odağı, viewport ve dil
 * bildiriminin varlığını sabitler. NVDA/JAWS/HCM insan kapısıdır (NOT_RUN).
 */
describe("a11y static (F30)", () => {
  it("görünür odak halkası kuralı tanımlı", () => {
    expect(css).toContain(":focus-visible");
    expect(css).toContain("--component-focus-ring");
  });

  it("viewport ve dil bildirimi mevcut", () => {
    expect(html).toContain('name="viewport"');
    expect(html).toContain('lang="tr"');
  });

  it("responsive kırılımlar tanımlı", () => {
    expect(css).toContain("@media (max-width: 900px)");
    expect(css).toContain("@media (max-width: 720px)");
  });
});
