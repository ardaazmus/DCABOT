import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  KillSwitchBanner,
  RiskPanel,
  type CanaryStatusView,
  type RiskExplainView,
} from "./RiskPanel";

const explanation: RiskExplainView = {
  blocked: true,
  reasons: [
    { code: "PAIR_BLOCKED", severity: "BLOCKER", message: "Pair blacklistte." },
  ],
};

const canary: CanaryStatusView = {
  verdict: "CANARY_NOGO",
  reasons: ["CANARY_APPROVAL_MISSING", "SPEC_NOT_ACTIVE"],
  kill_switch_engaged: false,
  approval_present: false,
  spec_status: "MISSING",
  paper_fill_count: 0,
  observed_at: "2026-09-22T00:00:00+00:00",
};

function canaryProps(overrides: {
  canary?: CanaryStatusView | null;
  canaryBusy?: boolean;
  canaryError?: string;
  onRefreshCanary?: () => void;
  onSetKillSwitch?: (engaged: boolean, reason: string) => void;
} = {}) {
  return {
    canary: overrides.canary ?? null,
    canaryBusy: overrides.canaryBusy ?? false,
    canaryError: overrides.canaryError ?? "",
    onRefreshCanary: overrides.onRefreshCanary ?? vi.fn(),
    onSetKillSwitch: overrides.onSetKillSwitch ?? vi.fn(),
  };
}

describe("RiskPanel", () => {
  it("engeli ve nedenleri gösterir", () => {
    render(<RiskPanel explanation={explanation} busy={false} error="" onExplain={vi.fn()} {...canaryProps()} />);
    expect(screen.getByText("VAR")).toBeInTheDocument();
    expect(screen.getByText("Pair blacklistte.")).toBeInTheDocument();
    expect(screen.getByText(/hiçbir kararı değiştirmez/)).toBeInTheDocument();
  });

  it("açıklama isteği payload üretir", () => {
    const onExplain = vi.fn();
    render(<RiskPanel explanation={null} busy={false} error="" onExplain={onExplain} {...canaryProps()} />);
    fireEvent.change(screen.getByLabelText("Bot (opsiyonel)"), { target: { value: "b1" } });
    fireEvent.change(screen.getByLabelText("Sembol (opsiyonel)"), { target: { value: "LUNAUSDT" } });
    fireEvent.click(screen.getByRole("button", { name: /Açıkla/ }));
    expect(onExplain).toHaveBeenCalledWith({ bot_id: "b1", symbol: "LUNAUSDT" });
  });
});

describe("KillSwitchBanner (AA.10a)", () => {
  it("devredeyken kritik-bant + yenile-düğmesi çıkar", () => {
    const onRefresh = vi.fn();
    render(<KillSwitchBanner canary={{ ...canary, kill_switch_engaged: true }} busy={false} onRefresh={onRefresh} />);
    expect(screen.getByRole("alert")).toHaveTextContent("KILL-SWITCH DEVREDE");
    fireEvent.click(screen.getByRole("button", { name: "Durumu yenile" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("kapalı/okunmamışken gizlenir, meşgulken kilitlenir", () => {
    const { unmount } = render(<KillSwitchBanner canary={canary} busy={false} onRefresh={vi.fn()} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    unmount();
    const second = render(<KillSwitchBanner canary={null} busy={false} onRefresh={vi.fn()} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    second.unmount();
    render(<KillSwitchBanner canary={{ ...canary, kill_switch_engaged: true }} busy={true} onRefresh={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Okunuyor…" })).toBeDisabled();
  });
});

describe("RiskPanel canary (B.3)", () => {
  it("karar + nedenler + anahtar durumunu gösterir", () => {
    render(<RiskPanel explanation={null} busy={false} error="" onExplain={vi.fn()} {...canaryProps({ canary })} />);
    expect(screen.getByText("CANARY_NOGO")).toBeInTheDocument();
    expect(screen.getByText("SPEC_NOT_ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("kapalı")).toBeInTheDocument();
    expect(screen.getByText("MISSING")).toBeInTheDocument();
  });

  it("devredeki anahtarı vurgular", () => {
    render(
      <RiskPanel
        explanation={null}
        busy={false}
        error=""
        onExplain={vi.fn()}
        {...canaryProps({ canary: { ...canary, kill_switch_engaged: true, reasons: ["KILL_SWITCH_ENGAGED"] } })}
      />,
    );
    expect(screen.getByText("AÇIK (devrede)")).toBeInTheDocument();
    expect(screen.getByText("KILL_SWITCH_ENGAGED")).toBeInTheDocument();
  });

  it("okunmadıysa yönlendirme çıkar, Yenile çağırır", () => {
    const onRefreshCanary = vi.fn();
    render(<RiskPanel explanation={null} busy={false} error="" onExplain={vi.fn()} {...canaryProps({ onRefreshCanary })} />);
    expect(screen.getByText(/Durum henüz okunmadı/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Yenile" }));
    expect(onRefreshCanary).toHaveBeenCalledTimes(1);
  });

  it("anahtar düğmeleri gerekçeyle handler çağırır", () => {
    const onSetKillSwitch = vi.fn();
    render(<RiskPanel explanation={null} busy={false} error="" onExplain={vi.fn()} {...canaryProps({ canary, onSetKillSwitch })} />);
    fireEvent.change(screen.getByLabelText("Gerekçe (açma için zorunlu)"), { target: { value: "deneme" } });
    fireEvent.click(screen.getByRole("button", { name: "Anahtarı aç" }));
    expect(onSetKillSwitch).toHaveBeenCalledWith(true, "deneme");
    fireEvent.click(screen.getByRole("button", { name: "Anahtarı kapat" }));
    expect(onSetKillSwitch).toHaveBeenCalledWith(false, "");
  });

  it("meşgulken canary düğmeleri kilitlidir", () => {
    render(<RiskPanel explanation={null} busy={false} error="" onExplain={vi.fn()} {...canaryProps({ canaryBusy: true })} />);
    expect(screen.getByRole("button", { name: "Yenile" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Anahtarı aç" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Anahtarı kapat" })).toBeDisabled();
  });
});
