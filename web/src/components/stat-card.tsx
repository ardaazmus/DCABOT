import type { ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  subline,
  chart,
  className,
}: {
  label: string;
  value: ReactNode;
  subline?: ReactNode;
  /** Mini grafik yuvası (örn. kıvılcım çizgisi). */
  chart?: ReactNode;
  className?: string;
}) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-sm font-normal text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        <div className={cn("font-mono text-2xl font-semibold")}>{value}</div>
        {subline === undefined ? null : (
          <div className="text-sm text-muted-foreground">{subline}</div>
        )}
        {chart === undefined ? null : <div className="mt-2">{chart}</div>}
      </CardContent>
    </Card>
  );
}
