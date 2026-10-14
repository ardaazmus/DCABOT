"use client";

import { useTranslations } from "next-intl";
import { useMemo } from "react";

import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MatrixCell } from "@/lib/api/schemas";
import { useBots, useCorrelationMatrix } from "@/lib/api/queries";
import { botMatrixSymbols, matrixLookup } from "@/lib/correlation";
import { cn } from "@/lib/utils";

function CellValue({ cell }: { cell: MatrixCell | undefined }) {
  if (cell === undefined || cell.verdict === "INSUFFICIENT") {
    return (
      <span className="font-mono text-muted-foreground" title={cell?.detail ?? undefined}>
        —
      </span>
    );
  }
  return (
    <span
      className={cn(
        "font-mono",
        cell.verdict === "BREACH" ? "font-semibold text-loss" : "text-profit",
      )}
      title={`${cell.samples} mum`}
    >
      {cell.coefficient ?? "—"}
    </span>
  );
}

/**
 * Bot korelasyon matrisi: botların işlem yaptığı sembollerin
 * hizalanmış 1s kapanışları üstünde ikili korelasyon. Kırmızı =
 * eşik üstü (yeni deal için risk artırıcı), gri = yetersiz veri.
 * Katsayılar görüntü amaçlı float; hüküm tam-sayı karşılaştırmadır.
 */
export function BotCorrelation() {
  const t = useTranslations("dashboard");
  const bots = useBots();
  const { symbols, truncated } = useMemo(
    () => botMatrixSymbols(bots.data?.data ?? []),
    [bots.data],
  );
  const matrix = useCorrelationMatrix(symbols.length >= 2 ? symbols : null);
  const lookup = useMemo(
    () => matrixLookup(matrix.data?.data.cells ?? []),
    [matrix.data],
  );

  return (
    <Card data-testid="dashboard-correlation">
      <CardHeader>
        <CardTitle>
          <h2>{t("correlationTitle")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {bots.isPending || matrix.isPending ? (
          <Skeleton className="h-32 w-full" />
        ) : bots.isError ? null : symbols.length < 2 ? (
          <EmptyState title={t("correlationEmpty")} />
        ) : matrix.isError || matrix.data === undefined ? (
          <p role="alert" className="text-sm text-loss">
            {t("loadError")}
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-center text-xs">
                <thead>
                  <tr>
                    <th scope="col" className="p-1" />
                    {matrix.data.data.symbols.map((symbol) => (
                      <th key={symbol} scope="col" className="p-1 font-mono font-medium">
                        {symbol}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.data.data.symbols.map((row) => (
                    <tr key={row}>
                      <th scope="row" className="p-1 text-left font-mono font-medium">
                        {row}
                      </th>
                      {matrix.data.data.symbols.map((column) =>
                        row === column ? (
                          <td key={column} className="p-1 text-muted-foreground">
                            —
                          </td>
                        ) : (
                          <td
                            key={column}
                            className={cn(
                              "p-1",
                              lookup.get(`${row} ${column}`)?.verdict === "BREACH" && "bg-loss/10",
                            )}
                          >
                            <CellValue cell={lookup.get(`${row} ${column}`)} />
                          </td>
                        ),
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted-foreground">
              {t("correlationNote", {
                threshold: matrix.data.data.threshold,
                window: matrix.data.data.window,
                overlap: matrix.data.data.overlap_bars,
              })}
              {truncated ? ` ${t("correlationTruncated")}` : ""}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
