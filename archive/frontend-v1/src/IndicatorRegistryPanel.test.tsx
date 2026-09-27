import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  IndicatorRegistryPanel,
  isIndicatorRegistryResponse,
} from "./IndicatorRegistryPanel";

describe("AA.8b kayıt defteri", () => {
  it("guard sözleşmesi", () => {
    expect(isIndicatorRegistryResponse({ data: { indicators: ["adx", "ema"] } })).toBe(true);
    expect(isIndicatorRegistryResponse({ data: { indicators: ["adx", 3] } })).toBe(false);
    expect(isIndicatorRegistryResponse({ data: {} })).toBe(false);
    expect(isIndicatorRegistryResponse({})).toBe(false);
  });

  it("liste verbatim dizilir", () => {
    render(<IndicatorRegistryPanel names={["adx", "ema"]} busy={false} error="" onRefresh={() => {}} />);
    expect(screen.getByText("adx")).toBeInTheDocument();
    expect(screen.getByText("ema")).toBeInTheDocument();
    expect(screen.getByText("2 kayıt")).toBeInTheDocument();
  });

  it("boş + hata durumları", () => {
    const { unmount } = render(<IndicatorRegistryPanel names={[]} busy={false} error="" onRefresh={() => {}} />);
    expect(screen.getByText("Kayıt defteri boş döndü.")).toBeInTheDocument();
    unmount();
    render(<IndicatorRegistryPanel names={[]} busy={false} error="uç 502" onRefresh={() => {}} />);
    expect(screen.getByRole("alert")).toHaveTextContent("uç 502");
  });
});
