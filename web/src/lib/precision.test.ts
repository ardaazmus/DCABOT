import { describe, expect, it } from "vitest";

import { decimalsFromStep } from "./precision";

describe("adım metninden basamak sayısı", () => {
  it("tick örnekleri", () => {
    expect(decimalsFromStep("0.01")).toBe(2);
    expect(decimalsFromStep("1")).toBe(0);
    expect(decimalsFromStep("0.00001")).toBe(5);
  });

  it("sondaki sıfırlar sayılmaz", () => {
    expect(decimalsFromStep("0.0100")).toBe(2);
    expect(decimalsFromStep("1.000")).toBe(0);
  });

  it("geçersiz metin 0 verir", () => {
    expect(decimalsFromStep("")).toBe(0);
    expect(decimalsFromStep("abc")).toBe(0);
    expect(decimalsFromStep("-0.01")).toBe(2);
  });
});
