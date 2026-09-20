import { describe, expect, it } from "vitest";
import {
  formatDatasetBytes,
  isActiveDownloadJob,
  shortSha256,
} from "./datasetCatalog";

describe("datasetCatalog yardımcıları", () => {
  it("byte değerlerini okunabilir ve kararlı biçimde formatlar", () => {
    expect(formatDatasetBytes(512)).toBe("512 B");
    expect(formatDatasetBytes(1024)).toBe("1.0 KB");
    expect(formatDatasetBytes(1024 * 1024)).toBe("1.0 MB");
  });

  it("sha256 özetini yalnızca sunum için kısaltır", () => {
    expect(shortSha256("a".repeat(64))).toBe("aaaaaaaaaaaa…aaaaaaaa");
  });

  it("yalnızca çalışan indirme durumlarını aktif sayar", () => {
    expect(isActiveDownloadJob("QUEUED")).toBe(true);
    expect(isActiveDownloadJob("RUNNING")).toBe(true);
    expect(isActiveDownloadJob("RETRYING")).toBe(true);
    expect(isActiveDownloadJob("SUCCEEDED")).toBe(false);
    expect(isActiveDownloadJob("FAILED")).toBe(false);
    expect(isActiveDownloadJob("CANCELLED")).toBe(false);
  });
});
