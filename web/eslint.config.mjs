import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    ".next-e2e/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "test-results/**",
    "playwright-report/**",
  ]),
  // Sayı kuralı (W-F0): parseFloat her yerde yasak; Number() yalnız
  // grafik pikseli için src/lib/chart/** altında serbest.
  {
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='parseFloat']",
          message:
            "parseFloat yasak: para/fiyat metni DecimalString olarak taşınır, src/lib/decimal.ts ile biçimlendirilir.",
        },
        {
          selector: "CallExpression[callee.name='Number']",
          message:
            "Number() yalnız src/lib/chart/** altında (grafik pikseli için) serbest.",
        },
      ],
    },
  },
  {
    files: ["src/lib/chart/**"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='parseFloat']",
          message:
            "parseFloat yasak: para/fiyat metni DecimalString olarak taşınır, src/lib/decimal.ts ile biçimlendirilir.",
        },
      ],
    },
  },
]);

export default eslintConfig;
