import Link from "next/link";

import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  className,
}: {
  /** Davet cümlesi ("Veri yok" gibi özür dili yok). */
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  className?: string;
}) {
  const action =
    actionLabel === undefined ? null : actionHref !== undefined ? (
      <Link
        href={actionHref}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90"
      >
        {actionLabel}
      </Link>
    ) : (
      <button
        type="button"
        onClick={onAction}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90"
      >
        {actionLabel}
      </button>
    );
  return (
    <div
      className={cn(
        "flex flex-col items-start gap-2 py-8",
        className,
      )}
    >
      <p className="text-base font-medium">{title}</p>
      {description === undefined ? null : (
        <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      )}
      {action === null ? null : <div className="mt-2">{action}</div>}
    </div>
  );
}
