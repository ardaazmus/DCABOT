import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  Banner,
  ConfirmDialog,
  NotificationCenter,
  NotificationStore,
  ToastStack,
} from "./notifications";

describe("NotificationStore", () => {
  it("push/dismiss/clear + 20 FIFO sınırı", () => {
    const store = new NotificationStore();
    const first = store.push("bir");
    store.push("iki", "success");
    expect(store.snapshot()).toHaveLength(2);
    store.dismiss(first.id);
    expect(store.snapshot().map((n) => n.text)).toEqual(["iki"]);
    for (let i = 0; i < 25; i++) store.push(`n${i}`);
    expect(store.snapshot()).toHaveLength(20);
    expect(store.snapshot()[0].text).toBe("n5");
    store.clear();
    expect(store.snapshot()).toHaveLength(0);
  });

  it("abone olmadan snapshot okunur", () => {
    const store = new NotificationStore();
    const seen: number[] = [];
    const off = store.subscribe(() => seen.push(store.snapshot().length));
    store.push("x");
    off();
    store.push("y");
    expect(seen).toEqual([1]);
  });
});

describe("ToastStack", () => {
  it("bildirimleri gösterir ve kapatır", () => {
    const store = new NotificationStore();
    render(<ToastStack store={store} />);
    expect(document.querySelector(".toast-stack")).toBeNull();
    act(() => { store.push("kayıt tamam", "success"); });
    expect(screen.getByText("kayıt tamam")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Bildirimi kapat" }));
    expect(screen.queryByText("kayıt tamam")).not.toBeInTheDocument();
  });
});

describe("Banner", () => {
  it("kritik bandı alert rolüyle gösterir", () => {
    render(<Banner tone="critical">Akış koptu</Banner>);
    expect(screen.getByRole("alert")).toHaveTextContent("Akış koptu");
  });
});

describe("NotificationCenter", () => {
  it("rozet okunmadıyı sayar, açınca sıfırlar", () => {
    const store = new NotificationStore();
    render(<NotificationCenter store={store} />);
    act(() => { store.push("a"); store.push("b"); });
    expect(screen.getByRole("button", { name: /2 okunmadı/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /okunmadı/ }));
    expect(screen.getByRole("dialog", { name: "Bildirim geçmişi" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Bildirim merkezi" })).toBeInTheDocument();
  });
});

describe("ConfirmDialog", () => {
  it("onay/iptal/Escape akışı", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <ConfirmDialog title="Toplu gönderim" summary="3 deal'e event gider." confirmLabel="Gönder" busy={false} onConfirm={onConfirm} onCancel={onCancel} />,
    );
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Gönder" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Vazgeç" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledTimes(2);
  });
});
