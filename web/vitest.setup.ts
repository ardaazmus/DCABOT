import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";

// Vitest globals kapalıyken Testing Library otomatik temizlik kurmaz.
afterEach(() => {
  cleanup();
});
