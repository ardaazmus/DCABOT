import { describe, expect, it } from "vitest";

import css from "./styles.css?raw";

/**
 * F30: WCAG kontrast kapısı. styles.css token bloklarını ayrıştırır,
 * var() referanslarını çözümler ve çekirdek metin/zemin çiftlerinin
 * her iki temada da AA eşiğini geçtiğini sabitler.
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
  if (name.startsWith("primitive-") || name === "primitive-white") {
    primitives.set(name, value);
  }
}
if (!primitives.has("primitive-white")) primitives.set("primitive-white", "#ffffff");

const dark = themeBlock(':root, :root[data-theme="dark"]');
const light = themeBlock(':root[data-theme="light"]');

function resolveColor(theme: Map<string, string>, name: string): string {
  const value = theme.get(name);
  if (value === undefined) throw new Error(`missing token ${name}`);
  const ref = value.match(/^var\(--([a-z0-9-]+)\)$/);
  if (ref) {
    if (ref[1].startsWith("primitive-")) {
      const primitive = primitives.get(ref[1]);
      if (primitive === undefined) throw new Error(`missing primitive ${ref[1]}`);
      return primitive;
    }
    return resolveColor(theme, ref[1]);
  }
  return value;
}

function luminance(hex: string): number {
  let code = hex.trim().replace(/^#/, "");
  if (code.length === 3) code = code
    .split("")
    .map((c) => c + c)
    .join("");
  const channels = [0, 2, 4].map((i) => parseInt(code.slice(i, i + 2), 16) / 255);
  const linear = channels.map((c) =>
    c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4),
  );
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

function ratio(foreground: string, background: string): number {
  const high = Math.max(luminance(foreground), luminance(background));
  const low = Math.min(luminance(foreground), luminance(background));
  return (high + 0.05) / (low + 0.05);
}

const TEXT_PAIRS: [string, string][] = [
  ["color-text", "color-bg-body"],
  ["color-text-strong", "color-bg-body"],
  ["color-text-soft", "color-bg-body"],
  ["color-text-muted", "color-bg-body"],
  ["color-text-faint", "color-bg-body"],
  ["color-text", "color-bg-sidebar"],
  ["color-nav-idle", "color-bg-sidebar"],
  ["color-nav-active-text", "color-nav-active-bg"],
  ["color-text", "color-bg-input"],
  ["color-text", "color-bg-table-head"],
  ["color-accent-text", "color-bg-body"],
  ["color-danger", "color-bg-body"],
  ["color-success", "color-bg-body"],
  ["color-warning", "color-bg-body"],
  ["color-text-on-accent", "color-accent"],
];

describe("theme contrast (F30)", () => {
  it.each([["dark", dark], ["light", light]] as const)(
    "%s çekirdek metin çiftleri AA (4.5) geçer",
    (_name, theme) => {
      for (const [fg, bg] of TEXT_PAIRS) {
        const measured = ratio(resolveColor(theme, fg), resolveColor(theme, bg));
        expect(measured, `${fg} / ${bg}`).toBeGreaterThanOrEqual(4.5);
      }
    },
  );

  it.each([["dark", dark], ["light", light]] as const)(
    "%s odak rengi non-text (3.0) geçer",
    (_name, theme) => {
      const measured = ratio(
        resolveColor(theme, "color-focus"),
        resolveColor(theme, "color-bg-body"),
      );
      expect(measured).toBeGreaterThanOrEqual(3.0);
    },
  );

  it("açık tema exact paleti donduruldu (beklenmedik renk değişimi yok)", () => {
    expect(light.get("color-bg-body")).toBe("#f1f4f9");
    expect(light.get("color-text")).toBe("#15212e");
    expect(light.get("color-accent")).toBe("#0f63c4");
    expect(light.get("color-success")).toBe("#0d7a4c");
    expect(light.get("color-danger")).toBe("#b3261e");
    expect(light.get("color-warning")).toBe("#8a5d00");
  });
});
