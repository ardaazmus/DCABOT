import { useEffect, useState, useSyncExternalStore } from "react";

/**
 * Faz 11 madde 6: 5 kanallı bildirim mimarisi.
 * toast (geçici) · banner (kritik kalıcı) · section mesajı (panellerin
 * mevcut inline error'ı) · bildirim merkezi+rozet (geçmiş) · onay
 * diyaloğu (çoklu/yıkıcı işlem özeti).
 */

export type NoticeKind = "info" | "success" | "error";

export type Notice = {
  id: number;
  kind: NoticeKind;
  text: string;
};

const MAX_NOTICES = 20;

export class NotificationStore {
  private notices: Notice[] = [];
  private listeners = new Set<() => void>();
  private nextId = 1;

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  snapshot = (): readonly Notice[] => this.notices;

  private emit() {
    for (const listener of this.listeners) listener();
  }

  push(text: string, kind: NoticeKind = "info"): Notice {
    const notice = { id: this.nextId++, kind, text };
    this.notices = [...this.notices, notice].slice(-MAX_NOTICES);
    this.emit();
    return notice;
  }

  dismiss(id: number) {
    if (!this.notices.some((n) => n.id === id)) return;
    this.notices = this.notices.filter((n) => n.id !== id);
    this.emit();
  }

  clear() {
    if (this.notices.length === 0) return;
    this.notices = [];
    this.emit();
  }
}

export function useNotices(store: NotificationStore): readonly Notice[] {
  return useSyncExternalStore(store.subscribe, store.snapshot, store.snapshot);
}

function ToastItem({ store, notice }: { store: NotificationStore; notice: Notice }) {
  useEffect(() => {
    if (notice.kind === "error") return;
    const timer = window.setTimeout(() => store.dismiss(notice.id), 6000);
    return () => window.clearTimeout(timer);
  }, [store, notice.id, notice.kind]);

  return (
    <div className={`toast toast-${notice.kind}`} role="status">
      <span>{notice.text}</span>
      <button type="button" aria-label="Bildirimi kapat" onClick={() => store.dismiss(notice.id)}>×</button>
    </div>
  );
}

export function ToastStack({ store }: { store: NotificationStore }) {
  const notices = useNotices(store);
  if (notices.length === 0) return null;
  return (
    <div className="toast-stack" aria-live="polite">
      {notices.map((notice) => (
        <ToastItem key={notice.id} store={store} notice={notice} />
      ))}
    </div>
  );
}

export function Banner({ tone, children }: { tone: "critical" | "warning"; children: React.ReactNode }) {
  return (
    <div className={`app-banner app-banner-${tone}`} role="alert">
      {children}
    </div>
  );
}

export function NotificationCenter({ store }: { store: NotificationStore }) {
  const notices = useNotices(store);
  const [open, setOpen] = useState(false);
  const [seen, setSeen] = useState(0);
  const unread = notices.filter((n) => n.id > seen).length;

  function toggle() {
    if (!open) setSeen(notices.length > 0 ? notices[notices.length - 1].id : seen);
    setOpen((v) => !v);
  }

  return (
    <div className="notice-center">
      <button type="button" className="notice-bell" aria-label={`Bildirim merkezi${unread > 0 ? `, ${unread} okunmadı` : ""}`} aria-expanded={open} onClick={toggle}>
        <span aria-hidden="true">◔</span>
        {unread > 0 && <span className="notice-badge">{unread}</span>}
      </button>
      {open && (
        <div className="notice-panel" role="dialog" aria-label="Bildirim geçmişi">
          {notices.length === 0 ? (
            <p className="helper-text">Bildirim yok.</p>
          ) : (
            <ul>
              {[...notices].reverse().map((n) => (
                <li key={n.id} className={`notice-history-${n.kind}`}>{n.text}</li>
              ))}
            </ul>
          )}
          <button type="button" className="secondary-button" onClick={() => store.clear()}>Temizle</button>
        </div>
      )}
    </div>
  );
}

export function ConfirmDialog({ title, summary, confirmLabel, busy, onConfirm, onCancel }: {
  title: string;
  summary: string;
  confirmLabel: string;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel]);

  return (
    <div className="confirm-overlay">
      <div className="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-summary">
        <h2 id="confirm-title">{title}</h2>
        <p id="confirm-summary">{summary}</p>
        <div className="wizard-nav">
          <button type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Vazgeç</button>
          <button type="button" className="primary-button" disabled={busy} onClick={onConfirm} autoFocus>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}
