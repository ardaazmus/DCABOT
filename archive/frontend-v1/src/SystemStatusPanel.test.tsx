import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  isSystemStatusResponse,
  SystemStatusPanel,
  type SystemStatusView,
} from "./SystemStatusPanel";

const status: SystemStatusView = {
  status: "ok",
  data_dir: { path: "/data", exists: true },
  disk: { free_bytes: 1000, total_bytes: 2000 },
  backups: { count: 3, latest_created_us: null },
};

describe("AA.12 sistem & yedekler", () => {
  it("guard sözleşmesi", () => {
    expect(isSystemStatusResponse({ data: status })).toBe(true);
    expect(isSystemStatusResponse({ data: { ...status, disk: { free_bytes: "1", total_bytes: 2 } } })).toBe(false);
    expect(isSystemStatusResponse({ data: { ...status, backups: { count: 1 } } })).toBe(false);
    expect(isSystemStatusResponse({})).toBe(false);
  });

  it("gerçek değerler aynen dizilir", () => {
    render(<SystemStatusPanel status={status} busy={false} error="" onRefresh={() => {}} />);
    expect(screen.getByText("/data")).toBeInTheDocument();
    expect(screen.getByText("1.000 / 2.000 bayt")).toBeInTheDocument();
    expect(screen.getByText("yedek yok")).toBeInTheDocument();
  });

  it("boş + hata durumları", () => {
    const { unmount } = render(<SystemStatusPanel status={null} busy={false} error="" onRefresh={() => {}} />);
    expect(screen.getByText("Sağlık-yoklaması henüz yapılmadı.")).toBeInTheDocument();
    unmount();
    render(<SystemStatusPanel status={null} busy={false} error="uç 500" onRefresh={() => {}} />);
    expect(screen.getByRole("alert")).toHaveTextContent("uç 500");
  });
});
