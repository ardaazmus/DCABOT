"use client";

import { useTranslations } from "next-intl";

import { BotTabs } from "@/components/bots/bot-tabs";
import { DealsTable } from "@/components/deals/deals-table";
import { Skeleton } from "@/components/skeleton";
import { useDeals } from "@/lib/api/queries";

function DealsPanel({ status, testId }: { status: "active" | "closed"; testId: string }) {
  const tb = useTranslations("bots");
  const query = useDeals(status);
  if (query.isPending) {
    return (
      <div className="flex flex-col gap-2" role="status">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (query.isError || query.data === undefined) {
    return (
      <p role="alert" className="text-sm text-loss">
        {tb("loadError")}
      </p>
    );
  }
  return (
    <DealsTable
      rows={query.data.data}
      mode={status === "active" ? "active" : "history"}
      testId={testId}
    />
  );
}

export default function DealsPage() {
  const t = useTranslations("deals");
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
      <BotTabs
        label={t("title")}
        tabs={[
          {
            id: "active",
            label: t("activeTab"),
            panel: <DealsPanel status="active" testId="deals-active" />,
          },
          {
            id: "history",
            label: t("historyTab"),
            panel: <DealsPanel status="closed" testId="deals-history" />,
          },
        ]}
      />
    </div>
  );
}
