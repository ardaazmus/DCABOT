import { describe, expect, it } from "vitest";

import css from "./styles.css?raw";

/**
 * Faz 17 A.2: qwen görsel-dil kapısı. Koyu tema tokenlarının qwen paletine
 * (RG-QWEN-HTML) taşındığını, fontların tanımlandığını ve bileşen
 * kurallarında ham hex kalmadığını sabitler. Açık tema dondurulmuştur
 * (themeContrast.test.ts) — bu dosya ona dokunmaz.
 */

function themeBlock(selectorStart: string): Map<string, string> {
  const start = css.indexOf(selectorStart);
  if (start < 0) throw new Error(`missing block ${selectorStart}`);
  const body = css.slice(start, css.indexOf("}", start));
  const entries: [string, string][] = [...body.matchAll(/--([a-z0-9-]+):\s*([^;]+);/g)].map(
    (m) => [m[1], m[2].trim()],
  );
  return new Map(entries);
}

const primitives = new Map<string, string>();
for (const [name, value] of themeBlock(":root {")) {
  if (name.startsWith("primitive-")) primitives.set(name, value);
}

const dark = themeBlock(':root, :root[data-theme="dark"]');

function resolve(name: string): string {
  const value = dark.get(name);
  if (value === undefined) throw new Error(`missing token ${name}`);
  const ref = value.match(/^var\(--([a-z0-9-]+)\)$/);
  if (ref) {
    const primitive = primitives.get(ref[1]);
    if (primitive === undefined) throw new Error(`missing primitive ${ref[1]}`);
    return primitive;
  }
  return value;
}

const PINNED: [string, string][] = [
  ["color-bg-body", "#06080d"],
  ["color-bg-sidebar", "#0a0f18"],
  ["color-bg-input", "#0a0f18"],
  ["color-bg-table-head", "#0e1522"],
  ["color-accent", "#fbbf24"],
  ["color-accent-hover", "#fcd34d"],
  ["color-accent-text", "#fcd34d"],
  ["color-brand", "#fbbf24"],
  ["color-focus", "#fbbf24"],
  ["color-success", "#34d399"],
  ["color-success-strong", "#6ee7b7"],
  ["color-danger", "#fb7185"],
  ["color-danger-bright", "#fda4af"],
  ["color-warning", "#fbbf24"],
  ["color-warning-deep", "#f59e0b"],
  ["color-nav-active-bg", "#2c281a"],
  ["color-nav-active-text", "#fcd34d"],
  ["color-nav-idle", "#94a3b8"],
  ["color-nav-inset", "#fbbf24"],
  ["color-text", "#e2e8f0"],
  ["color-text-strong", "#f1f5f9"],
  ["color-text-soft", "#cbd5e1"],
  ["color-text-muted", "#94a3b8"],
  ["color-text-faint", "#7d8ba3"],
  ["color-text-on-accent", "#06080d"],
  ["color-toggle-off", "#26334a"],
  ["color-toggle-on-bg", "rgba(52,211,153,.4)"],
  ["color-toggle-on-border", "#34d399"],
  ["color-toggle-knob", "#94a3b8"],
  ["color-grid-line", "rgba(251,191,36,.035)"],
];

describe("qwen token geçişi (Faz 17 A.2)", () => {
  it("koyu tema çekirdek tokenları qwen paletine çözülür", () => {
    for (const [token, expected] of PINNED) {
      expect(resolve(token), token).toBe(expected);
    }
  });

  it("koyu temada mavi accent kalıntısı yok (amber/emerald/cyan/rose)", () => {
    for (const token of ["color-accent", "color-accent-text", "color-brand", "color-focus", "color-success", "color-danger"]) {
      expect(resolve(token), token).not.toMatch(/^(#1373df|#2ecc9a|#e05f5f|#42a5ff)$/);
    }
  });

  it("qwen fontları tanımlı (Space Grotesk + JetBrains Mono)", () => {
    expect(css).toContain('"Space Grotesk"');
    expect(css).toContain('"JetBrains Mono"');
  });

  it("bg-grid dokusu yalnız koyu temada aktif", () => {
    expect(css).toContain(':root:not([data-theme="light"]) body { background-image:');
    expect(css).toContain("background-size: 44px 44px;");
  });

  it("qwen rozet sınıfları tanımlı (simbadge/livebadge)", () => {
    expect(css).toContain(".simbadge {");
    expect(css).toContain(".livebadge {");
  });

  it("token bloğu dışında ham hex yok (A.2 kabul kriteri)", () => {
    const end = css.indexOf("/* === TOKEN BLOCK END === */");
    expect(end).toBeGreaterThan(0);
    const componentRules = css.slice(end);
    expect(componentRules).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
