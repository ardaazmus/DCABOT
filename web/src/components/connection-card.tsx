"use client";

import { useTranslations } from "next-intl";

import { StatusBadge } from "@/components/status-badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiContractError } from "@/lib/api/client";
import { useCapabilities, useHealth } from "@/lib/api/queries";

function errorText(error: unknown, offline: string, contract: string): string {
  // Bu kart "bağlı mı?" sorusunu yanıtlar: geçerli veri yoksa bağlı değiliz.
  // (Proxy arkasında backend-kapalı ile backend-500 ayırt edilemez; ikisi de
  // "ulaşılamadı" demektir. Yalnız sözleşme ihlali ayrı metni hak eder.)
  if (error instanceof ApiContractError) return contract;
  return offline;
}

/** W-F0 bağlantı kartı; Ayarlar > Sistem bölümünde yaşar. */
export function ConnectionCard() {
  const t = useTranslations("status");
  const health = useHealth();
  const capabilities = useCapabilities();

  const loading = health.isPending || capabilities.isPending;
  const error = health.error ?? capabilities.error;

  async function retry() {
    await Promise.all([health.refetch(), capabilities.refetch()]);
  }

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>
          <h2 className="text-lg font-semibold">{t("title")}</h2>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && !error ? (
          <p role="status">{t("loading")}</p>
        ) : error ? (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <StatusBadge variant="error">{t("disconnected")}</StatusBadge>
            </div>
            <p role="alert">{errorText(error, t("offline"), t("contractError"))}</p>
            <button
              type="button"
              onClick={() => void retry()}
              className="w-fit rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted"
            >
              {t("retry")}
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <StatusBadge variant="live">{t("connected")}</StatusBadge>
            </div>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted-foreground">{t("health")}</dt>
              <dd>{health.data?.status ?? "—"}</dd>
              <dt className="text-muted-foreground">{t("mode")}</dt>
              <dd>{health.data?.mode ?? "—"}</dd>
              <dt className="text-muted-foreground">{t("executionMode")}</dt>
              <dd>{capabilities.data?.execution_mode ?? "—"}</dd>
              <dt className="text-muted-foreground">{t("dataMode")}</dt>
              <dd>{capabilities.data?.data_mode ?? "—"}</dd>
            </dl>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
