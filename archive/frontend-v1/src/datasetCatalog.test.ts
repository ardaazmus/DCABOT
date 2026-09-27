import { describe, expect, it } from "vitest";
import {
  formatDatasetBytes,
  isActiveDownloadJob,
  isEquityCurve,
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

  it("equity eğrisini string-listesi olarak doğrular", () => {
    expect(isEquityCurve(["100", "99.5", "-3"])).toBe(true);
    expect(isEquityCurve([])).toBe(true);
    expect(isEquityCurve(["100", 99])).toBe(false);
    expect(isEquityCurve("100")).toBe(false);
    expect(isEquityCurve(null)).toBe(false);
    expect(isEquityCurve(undefined)).toBe(false);
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
