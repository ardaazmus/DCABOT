import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const statusBadgeVariants = cva(
  "inline-flex h-5 w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap",
  {
    variants: {
      variant: {
        live: "bg-profit/12 text-profit",
        paper: "bg-entry/12 text-entry",
        testnet: "bg-accent/12 text-accent",
        running: "bg-profit/12 text-profit",
        paused: "bg-safety/15 text-safety",
        stopped: "bg-muted text-muted-foreground",
        error: "bg-loss/12 text-loss",
        warn: "bg-safety/15 text-safety",
      },
    },
    defaultVariants: {
      variant: "paper",
    },
  },
);

export type StatusBadgeVariant = VariantProps<
  typeof statusBadgeVariants
>["variant"];

export function StatusBadge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof statusBadgeVariants>) {
  return (
    <span
      className={cn(statusBadgeVariants({ variant }), className)}
      {...props}
    />
  );
}
