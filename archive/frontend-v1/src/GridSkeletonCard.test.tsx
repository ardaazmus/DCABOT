import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { GridSkeletonCard } from "./GridSkeletonCard";

describe("AA.11 grid iskeleti", () => {
  it("dürüst yok-notu + derin-bağlantı düğmesi", () => {
    const onOpenMargin = vi.fn();
    render(<GridSkeletonCard onOpenMargin={onOpenMargin} />);
    expect(screen.getByText("motor yok")).toBeInTheDocument();
    expect(screen.getByText(/grid motoru bu sürümde yok/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Marjin projeksiyonunu aç" }));
    expect(onOpenMargin).toHaveBeenCalledTimes(1);
  });
});
