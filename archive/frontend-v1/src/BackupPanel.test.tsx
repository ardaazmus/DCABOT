import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  BackupPanel,
  type BackupManifestView,
  type BackupVerdictView,
} from "./BackupPanel";

const backups: BackupManifestView[] = [
  {
    store: "historical_runs",
    backup_file: "historical_runs-1000.sqlite3",
    manifest_file: "historical_runs-1000.manifest.json",
    bytes: 1234,
    sha256: "ab",
    created_us: 1000,
  },
];

const verdict: BackupVerdictView = {
  backup_file: "historical_runs-1000.sqlite3",
  verdict: "VERIFIED",
  application_id: 1,
  user_version: 2,
};

function renderPanel(overrides = {}) {
  const handlers = {
    onTake: vi.fn(),
    onVerify: vi.fn(),
    onRefresh: vi.fn(),
    ...overrides,
  };
  render(
    <BackupPanel
      backups={backups}
      verdict={verdict}
      busy={false}
      error=""
      {...handlers}
    />,
  );
  return handlers;
}

describe("BackupPanel", () => {
  it("liste ve kararı gösterir", () => {
    renderPanel();
    expect(screen.getByText("historical_runs-1000.sqlite3")).toBeInTheDocument();
    expect(screen.getByText(/sqlite3: VERIFIED/)).toBeInTheDocument();
    expect(screen.getByText(/Restore otomatik değildir/)).toBeInTheDocument();
  });

  it("alma ve doğrulama handler çağırır", () => {
    const handlers = renderPanel();
    fireEvent.change(screen.getByLabelText("Store"), { target: { value: "two_leg_journal" } });
    fireEvent.click(screen.getByRole("button", { name: /Backup al/ }));
    expect(handlers.onTake).toHaveBeenCalledWith("two_leg_journal");
    fireEvent.change(screen.getByLabelText("Backup dosyası"), {
      target: { value: "historical_runs-1000.sqlite3" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^Doğrula$/ }));
    expect(handlers.onVerify).toHaveBeenCalledWith("historical_runs-1000.sqlite3");
    fireEvent.click(screen.getByRole("button", { name: /Listeyi yenile/ }));
    expect(handlers.onRefresh).toHaveBeenCalledTimes(1);
  });
});
