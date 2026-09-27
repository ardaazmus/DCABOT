import fc from "fast-check";
import { describe, expect, it } from "vitest";

import golden from "../../tests/fixtures/decimal/half_even_golden.json";
import {
  DecimalFormatError,
  type DecimalString,
  compareDecimal,
  formatDecimal,
  isDecimalString,
  parseDecimal,
  signOf,
} from "./decimal";

const d = (value: string) => parseDecimal(value);

const decimalArb = fc
  .tuple(
    fc.boolean(),
    fc.bigInt({ min: 0n, max: 10n ** 15n }),
    fc.string({ unit: fc.constantFrom(..."0123456789"), maxLength: 14 }),
  )
  .map(([negative, integer, fraction]) => {
    const body = integer.toString() + (fraction ? `.${fraction}` : "");
    const isZero = /^[0.]*$/.test(body);
    return (negative && !isZero ? `-${body}` : body) as DecimalString;
  });

function exactRational(value: string): { num: bigint; den: bigint } {
  const negative = value.startsWith("-");
  const [integer, fraction = ""] = (negative ? value.slice(1) : value).split(".");
  const num = BigInt(integer + fraction) * (negative ? -1n : 1n);
  return { num, den: 10n ** BigInt(fraction.length) };
}

describe("parseDecimal", () => {
  it("accepts backend exact text and rejects everything else", () => {
    for (const ok of ["0", "12", "-3.5", "0.00000001", "84506.01"]) expect(isDecimalString(ok)).toBe(true);
    for (const bad of ["", "1e3", "+1", "01", ".5", "5.", "-0", "1,5", " 1", "NaN", 1.5, null]) {
      expect(isDecimalString(bad)).toBe(false);
      expect(() => parseDecimal(bad)).toThrow(DecimalFormatError);
    }
  });
});

describe("formatDecimal", () => {
  it("matches the backend's ROUND_HALF_EVEN text() on every golden vector", () => {
    expect(golden.cases.length).toBeGreaterThanOrEqual(1000);
    for (const { value, places, expected } of golden.cases) {
      expect(formatDecimal(d(value), { maxFractionDigits: places, grouping: false, locale: "en" }), `${value}@${places}`).toBe(expected);
    }
  });

  it("keeps half-even parity when the rounded digit is a stripped zero", () => {
    expect(formatDecimal(d("1.05"), { maxFractionDigits: 1, locale: "en" })).toBe("1");
    expect(formatDecimal(d("1.15"), { maxFractionDigits: 1, locale: "en" })).toBe("1.2");
    expect(formatDecimal(d("-2.5"), { maxFractionDigits: 0, locale: "en" })).toBe("-2");
  });

  it("uses Turkish separators and optional sign", () => {
    expect(formatDecimal(d("1234567.891"), { maxFractionDigits: 2 })).toBe("1.234.567,89");
    expect(formatDecimal(d("-0.5"), { minFractionDigits: 2 })).toBe("-0,50");
    expect(formatDecimal(d("38.4"), { signDisplay: "always", minFractionDigits: 2 })).toBe("+38,40");
    expect(formatDecimal(d("-0.004"), { maxFractionDigits: 2, signDisplay: "always" })).toBe("0");
  });

  it("property: without rounding, ungrouped en output is the input minus trailing zeros", () => {
    fc.assert(
      fc.property(decimalArb, (value) => {
        const expected = value.includes(".") ? value.replace(/\.?0+$/, "") : value;
        const normalized = /^-?0$/.test(expected) ? "0" : expected;
        expect(formatDecimal(value, { grouping: false, locale: "en" })).toBe(normalized);
      }),
    );
  });

  it("property: rounding error is at most half a unit and ties go to even", () => {
    fc.assert(
      fc.property(decimalArb, fc.integer({ min: 0, max: 10 }), (value, places) => {
        const out = formatDecimal(value, { maxFractionDigits: places, grouping: false, locale: "en" });
        const a = exactRational(value);
        const b = exactRational(out);
        const diff = (a.num * b.den - b.num * a.den) * 10n ** BigInt(places);
        const twice = 2n * (diff < 0n ? -diff : diff);
        const half = a.den * b.den;
        expect(twice <= half).toBe(true);
        if (twice === half) {
          const [integer, fraction = ""] = out.replace("-", "").split(".");
          const units = BigInt(integer + fraction.padEnd(places, "0"));
          expect(units % 2n).toBe(0n);
        }
      }),
    );
  });

  it("property: tr and en differ only in separators", () => {
    fc.assert(
      fc.property(decimalArb, (value) => {
        const tr = formatDecimal(value, { maxFractionDigits: 4 });
        const en = formatDecimal(value, { maxFractionDigits: 4, locale: "en" });
        expect(tr.replace(/\./g, "_").replace(",", ".").replace(/_/g, ",")).toBe(en);
      }),
    );
  });
});

describe("compareDecimal", () => {
  it("property: agrees with exact rational ordering", () => {
    fc.assert(
      fc.property(decimalArb, decimalArb, (a, b) => {
        const x = exactRational(a);
        const y = exactRational(b);
        const lhs = x.num * y.den;
        const rhs = y.num * x.den;
        const expected = lhs < rhs ? -1 : lhs > rhs ? 1 : 0;
        expect(compareDecimal(a, b)).toBe(expected);
      }),
    );
  });

  it("gives PnL sign", () => {
    expect(signOf(d("-0.01"))).toBe(-1);
    expect(signOf(d("0.000"))).toBe(0);
    expect(signOf(d("214.6"))).toBe(1);
  });
});
