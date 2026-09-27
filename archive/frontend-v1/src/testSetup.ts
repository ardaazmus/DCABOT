import "@testing-library/jest-dom/vitest";
import "vitest-canvas-mock";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// jsdom has no ResizeObserver; TradingChart (Faz 16.1, lightweight-charts)
// needs one for its `autoSize` option. Minimal no-op polyfill for tests only.
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

afterEach(() => cleanup());
