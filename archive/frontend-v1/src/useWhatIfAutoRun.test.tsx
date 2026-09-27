import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useWhatIfAutoRun, WHAT_IF_AUTO_RUN_DELAY_MS } from "./useWhatIfAutoRun";

function Harness({ enabled, planKey, onAutoRun }: { enabled: boolean; planKey: string | null; onAutoRun: () => void }) {
  const { pending } = useWhatIfAutoRun({ enabled, planKey, onAutoRun });
  return <p>{pending ? "bekliyor" : "boşta"}</p>;
}

describe("useWhatIfAutoRun (B.5 What-If)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("anahtar kapalıyken plan hazır olsa bile tetiklemez", () => {
    const onAutoRun = vi.fn();
    render(<Harness enabled={false} planKey="ds|pr|hash" onAutoRun={onAutoRun} />);

    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS + 1000);
    });

    expect(onAutoRun).not.toHaveBeenCalled();
    expect(screen.getByText("boşta")).toBeInTheDocument();
  });

  it("gecikme dolmadan tetiklemez, dolunca tam bir kez tetikler", () => {
    const onAutoRun = vi.fn();
    render(<Harness enabled planKey="ds|pr|hash" onAutoRun={onAutoRun} />);

    expect(screen.getByText("bekliyor")).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS - 1);
    });
    expect(onAutoRun).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(onAutoRun).toHaveBeenCalledTimes(1);
    expect(screen.getByText("boşta")).toBeInTheDocument();
  });

  it("hızlı plan değişimlerinde debounce uygular: yalnız son anahtar için tek çağrı", () => {
    const onAutoRun = vi.fn();
    const { rerender } = render(<Harness enabled planKey="ds|pr|hash-1" onAutoRun={onAutoRun} />);

    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS - 100);
    });
    rerender(<Harness enabled planKey="ds|pr|hash-2" onAutoRun={onAutoRun} />);
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS - 100);
    });
    expect(onAutoRun).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(onAutoRun).toHaveBeenCalledTimes(1);
  });

  it("aynı anahtar yeniden render edilse bile ikinci kez tetiklemez", () => {
    const onAutoRun = vi.fn();
    const { rerender } = render(<Harness enabled planKey="ds|pr|hash" onAutoRun={onAutoRun} />);
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS);
    });
    expect(onAutoRun).toHaveBeenCalledTimes(1);

    rerender(<Harness enabled planKey="ds|pr|hash" onAutoRun={onAutoRun} />);
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS * 2);
    });
    expect(onAutoRun).toHaveBeenCalledTimes(1);
  });

  it("plan anahtarı null olursa bekleyen tetikleme iptal olur", () => {
    const onAutoRun = vi.fn();
    const { rerender } = render(<Harness enabled planKey="ds|pr|hash" onAutoRun={onAutoRun} />);
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS - 100);
    });

    rerender(<Harness enabled planKey={null} onAutoRun={onAutoRun} />);
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS);
    });

    expect(onAutoRun).not.toHaveBeenCalled();
    expect(screen.getByText("boşta")).toBeInTheDocument();
  });

  it("unmount bekleyen tetiklemeyi iptal eder", () => {
    const onAutoRun = vi.fn();
    const { unmount } = render(<Harness enabled planKey="ds|pr|hash" onAutoRun={onAutoRun} />);
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS - 100);
    });

    unmount();
    act(() => {
      vi.advanceTimersByTime(WHAT_IF_AUTO_RUN_DELAY_MS);
    });

    expect(onAutoRun).not.toHaveBeenCalled();
  });
});
