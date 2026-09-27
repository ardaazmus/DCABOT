/**
 * Display-only decimal handling for exact server strings (Claude, Faz W).
 *
 * Money, prices and quantities arrive as exact decimal text from the backend
 * and stay text. Nothing here does financial arithmetic; it only validates,
 * compares and formats. Rounding is ROUND_HALF_EVEN on the magnitude, the
 * same rule as the backend's `dcabot.domain.numbers.text()` — a golden-vector
 * test pins the two together.
 */

declare const decimalBrand: unique symbol;
export type DecimalString = string & { readonly [decimalBrand]: true };

const PATTERN = /^-?(0|[1-9][0-9]*)(\.[0-9]+)?$/;
const MAX_LENGTH = 80;

export class DecimalFormatError extends Error {
  constructor(value: unknown) {
    super(`Geçersiz ondalık metin: ${String(value).slice(0, 40)}`);
    this.name = "DecimalFormatError";
  }
}

export function isDecimalString(value: unknown): value is DecimalString {
  return typeof value === "string" && value.length <= MAX_LENGTH && PATTERN.test(value) && value !== "-0";
}

export function parseDecimal(value: unknown): DecimalString {
  if (!isDecimalString(value)) throw new DecimalFormatError(value);
  return value;
}

type Parts = { negative: boolean; integer: string; fraction: string };

function split(value: DecimalString): Parts {
  const negative = value.startsWith("-");
  const [integer, fraction = ""] = (negative ? value.slice(1) : value).split(".");
  return { negative, integer: integer ?? "0", fraction };
}

function roundHalfEven(parts: Parts, places: number): Parts {
  if (parts.fraction.length <= places) return parts;
  const kept = parts.fraction.slice(0, places);
  const rest = parts.fraction.slice(places);
  let units = BigInt(parts.integer + kept);
  const first = rest.charCodeAt(0) - 48;
  const tailNonZero = /[1-9]/.test(rest.slice(1));
  const roundUp = first > 5 || (first === 5 && (tailNonZero || units % 2n === 1n));
  if (roundUp) units += 1n;
  const digits = units.toString().padStart(places + 1, "0");
  const integer = places === 0 ? digits : digits.slice(0, digits.length - places);
  const fraction = places === 0 ? "" : digits.slice(digits.length - places);
  return { negative: parts.negative, integer, fraction };
}

function group(integer: string, separator: string): string {
  return integer.replace(/\B(?=(\d{3})+(?!\d))/g, separator);
}

export type FormatOptions = {
  /** Round half-even to at most this many fraction digits; omit for exact. */
  maxFractionDigits?: number;
  /** Pad with zeros up to this many fraction digits. */
  minFractionDigits?: number;
  /** Thousands grouping (default true). */
  grouping?: boolean;
  locale?: "tr" | "en";
  /** "always" prefixes "+" on positive values (PnL). Zero never gets a sign. */
  signDisplay?: "auto" | "always";
};

export function formatDecimal(value: DecimalString, options: FormatOptions = {}): string {
  const { maxFractionDigits, minFractionDigits = 0, grouping = true, locale = "tr", signDisplay = "auto" } = options;
  if (maxFractionDigits !== undefined && (!Number.isInteger(maxFractionDigits) || maxFractionDigits < 0)) {
    throw new RangeError("maxFractionDigits must be a non-negative integer");
  }
  if (!Number.isInteger(minFractionDigits) || minFractionDigits < 0) {
    throw new RangeError("minFractionDigits must be a non-negative integer");
  }
  let parts = split(parseDecimal(value));
  if (maxFractionDigits !== undefined) parts = roundHalfEven(parts, maxFractionDigits);
  let fraction = parts.fraction.replace(/0+$/, "");
  if (fraction.length < minFractionDigits) fraction = fraction.padEnd(minFractionDigits, "0");
  const isZero = /^0*$/.test(parts.integer) && /^0*$/.test(fraction);
  const integer = parts.integer.replace(/^0+(?=\d)/, "");
  const [groupSeparator, decimalSeparator] = locale === "tr" ? [".", ","] : [",", "."];
  const body = (grouping ? group(integer, groupSeparator) : integer) + (fraction ? decimalSeparator + fraction : "");
  if (isZero) return body;
  if (parts.negative) return `-${body}`;
  return signDisplay === "always" ? `+${body}` : body;
}

function scaled(parts: Parts, scale: number): bigint {
  const magnitude = BigInt(parts.integer + parts.fraction.padEnd(scale, "0"));
  return parts.negative ? -magnitude : magnitude;
}

/** Exact ordering of two decimal strings: -1, 0 or 1. */
export function compareDecimal(a: DecimalString, b: DecimalString): -1 | 0 | 1 {
  const left = split(parseDecimal(a));
  const right = split(parseDecimal(b));
  const scale = Math.max(left.fraction.length, right.fraction.length);
  const x = scaled(left, scale);
  const y = scaled(right, scale);
  return x < y ? -1 : x > y ? 1 : 0;
}

/** Sign for PnL colouring: -1 loss, 0 flat, 1 profit. */
export function signOf(value: DecimalString): -1 | 0 | 1 {
  return compareDecimal(value, "0" as DecimalString);
}
