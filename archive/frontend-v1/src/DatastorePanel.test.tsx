import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DatastorePanel, manifestText } from "./DatastorePanel";
import type { DatasetSummary } from "./datasetCatalog";

const datasets: DatasetSummary[] = [
  { dataset_id: "ds-1", dataset_type: "kline_csv_zip", instrument: "BTCUSDT", interval: "1h", period_start: "2026-01-01", period_end: "2026-01-31", status: "VERIFIED", artifact: { sha256: "a".repeat(64), byte_size: 2048 } },
  { dataset_id: "ds-2", dataset_type: "kline_csv_zip", instrument: "ETHUSDT", interval: "1h", period_start: "2026-01-01", period_end: "2026-01-31", status: "MISSING", artifact: null },
];

describe("AA.6 datastore manifestosu", () => {
  it("manifesto metni sunucu alanlarından kurulur", () => {
    const text = manifestText(datasets[0]);
    expect(text).toContain("dataset_id: ds-1");
    expect(text).toContain(`artifact_sha256: ${"a".repeat(64)}`);
    expect(text).toContain("byte_size: 2048");
    expect(text).toContain("status: VERIFIED");
  });

  it("satırlar artifact + durumu verbatim dizer", () => {
    render(<DatastorePanel datasets={datasets} status="ready" error="" activeJob={null} />);
    expect(screen.getByText("ds-1")).toBeInTheDocument();
    expect(screen.getByText("BTCUSDT 1h")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Manifesto" })).toHaveLength(2);
  });

  it("aktif iş + boş + hata durumları", () => {
    const { unmount } = render(
      <DatastorePanel datasets={datasets} status="ready" error="" activeJob={{ job_id: "j1", dataset_id: "ds-2", status: "RUNNING", attempt: 1, max_attempts: 3, bytes_downloaded: 10, total_bytes: 100, cache_hit: null, error_code: null, error_message: null }} />,
    );
    expect(screen.getByText("j1")).toBeInTheDocument();
    unmount();
    const { unmount: unmount2 } = render(<DatastorePanel datasets={[]} status="ready" error="" activeJob={null} />);
    expect(screen.getByText("Kayıtlı dataset tanımı yok.")).toBeInTheDocument();
    unmount2();
    render(<DatastorePanel datasets={[]} status="error" error="katalog 500" activeJob={null} />);
    expect(screen.getByRole("alert")).toHaveTextContent("katalog 500");
  });
});
