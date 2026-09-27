"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { EnumValue } from "@/components/enum-value";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCanary, useKillSwitch, useRiskExplain } from "@/lib/api/queries";
import { hasEnumLabel } from "@/lib/enum-labels";
import { cn } from "@/lib/utils";

type ExplainMode = "bot" | "session" | "deal";

function SeverityBadge({ severity }: { severity: string }) {
  const variant =
    severity === "BLOCKER" ? "error" : severity === "INFO" ? "paper" : "warn";
  return (
    <StatusBadge variant={variant} title={hasEnumLabel(severity) ? severity : undefined}>
      <EnumValue code={severity} />
    </StatusBadge>
  );
}

export default function RiskPage() {
  const ts = useTranslations("settings");
  const canary = useCanary();
  const killSwitch = useKillSwitch();
  const explain = useRiskExplain();
  const [confirmOpen, setConfirmOpen] = useState<"on" | "off" | null>(null);
  const [mode, setMode] = useState<ExplainMode>("bot");
  const [botId, setBotId] = useState("");
  const [symbol, setSymbol] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [dealId, setDealId] = useState("");

  const engaged = canary.data?.data.kill_switch_engaged;

  function submitExplain() {
    if (mode === "bot") {
      void explain.mutate({ bot_id: botId.trim(), symbol: symbol.trim().toUpperCase() || undefined });
    } else if (mode === "session") {
      void explain.mutate({ session_id: sessionId.trim() });
    } else {
      void explain.mutate({ deal_id: dealId.trim() });
    }
  }

  const explainReady =
    mode === "bot"
      ? botId.trim() !== ""
      : mode === "session"
        ? sessionId.trim() !== ""
        : dealId.trim() !== "";

  const modes: { id: ExplainMode; label: string }[] = [
    { id: "bot", label: ts("modeBot") },
    { id: "session", label: ts("modeSession") },
    { id: "deal", label: ts("modeDeal") },
  ];

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle>
            <h2>{ts("killTitle")}</h2>
          </CardTitle>
          {canary.isPending ? (
            <Skeleton className="h-5 w-20" />
          ) : engaged === undefined ? (
            <StatusBadge variant="warn">{ts("killOff")}</StatusBadge>
          ) : (
            <StatusBadge variant={engaged ? "error" : "stopped"}>
              {engaged ? ts("killOn") : ts("killOff")}
            </StatusBadge>
          )}
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div>
            <button
              type="button"
              disabled={engaged === undefined || killSwitch.isPending}
              onClick={() => setConfirmOpen(engaged ? "off" : "on")}
              className={cn(
                "rounded-md px-4 py-2 text-sm font-medium",
                engaged
                  ? "border border-input bg-background hover:bg-muted"
                  : "bg-loss text-white hover:bg-loss/90",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            >
              {engaged ? ts("killClose") : ts("killOpen")}
            </button>
          </div>
          {killSwitch.isError ? (
            <p role="alert" className="text-sm text-loss">
              {killSwitch.error.message}
            </p>
          ) : null}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={confirmOpen === "on"}
        onOpenChange={(open) => setConfirmOpen(open ? "on" : null)}
        title={ts("killConfirmOpenTitle")}
        description={ts("killConfirmOpenDesc")}
        confirmLabel={ts("confirm")}
        cancelLabel={ts("cancel")}
        reasonLabel={ts("reasonLabel")}
        reasonPlaceholder={ts("reasonPlaceholder")}
        reasonRequired
        onConfirm={(reason) => {
          if (reason !== undefined) {
            killSwitch.mutate(
              { engaged: true, reason },
              { onSuccess: () => setConfirmOpen(null) },
            );
          }
        }}
      />
      <ConfirmDialog
        open={confirmOpen === "off"}
        onOpenChange={(open) => setConfirmOpen(open ? "off" : null)}
        title={ts("killConfirmCloseTitle")}
        description={ts("killConfirmCloseDesc")}
        confirmLabel={ts("confirm")}
        cancelLabel={ts("cancel")}
        onConfirm={() => {
          killSwitch.mutate(
            { engaged: false },
            { onSuccess: () => setConfirmOpen(null) },
          );
        }}
      />

      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{ts("canaryTitle")}</h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {canary.isPending ? (
            <Skeleton className="h-16 w-full" />
          ) : canary.isError || canary.data === undefined ? (
            <p role="alert" className="text-sm text-loss">
              {canary.error instanceof Error ? canary.error.message : ""}
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <StatusBadge
                  variant={canary.data.data.verdict === "CANARY_GO" ? "live" : "warn"}
                >
                  <EnumValue code={canary.data.data.verdict} />
                </StatusBadge>
                <span className="text-muted-foreground">
                  {ts("approval")}:{" "}
                  {canary.data.data.approval_present ? ts("yes") : ts("no")}
                </span>
              </div>
              <div>
                <h3 className="text-sm font-semibold">{ts("canaryReasons")}</h3>
                <ul className="mt-1 flex flex-col gap-1 text-sm">
                  {canary.data.data.reasons.map((reason) => (
                    <li key={reason} className="font-mono text-xs">
                      <EnumValue code={reason} />
                    </li>
                  ))}
                </ul>
              </div>
              <p className="text-xs text-muted-foreground">{ts("thresholdNote")}</p>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            <h2>{ts("explainTitle")}</h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div role="group" aria-label={ts("explainTitle")} className="flex gap-1">
            {modes.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={mode === item.id}
                onClick={() => {
                  setMode(item.id);
                  explain.reset();
                }}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium",
                  mode === item.id
                    ? "bg-accent/12 text-accent"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
          {mode === "bot" ? (
            <div className="flex flex-col gap-2 sm:flex-row">
              <label className="flex flex-1 flex-col gap-1 text-sm">
                <span className="font-medium">{ts("botId")}</span>
                <input
                  type="text"
                  value={botId}
                  onChange={(event) => setBotId(event.target.value)}
                  className="h-9 rounded-md border border-input bg-background px-3 font-mono text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </label>
              <label className="flex flex-1 flex-col gap-1 text-sm">
                <span className="font-medium">{ts("explainSymbol")}</span>
                <input
                  type="text"
                  value={symbol}
                  onChange={(event) => setSymbol(event.target.value)}
                  placeholder="BTCUSDT"
                  className="h-9 rounded-md border border-input bg-background px-3 font-mono text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </label>
            </div>
          ) : mode === "session" ? (
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">{ts("sessionId")}</span>
              <input
                type="text"
                value={sessionId}
                onChange={(event) => setSessionId(event.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 font-mono text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          ) : (
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">{ts("dealId")}</span>
              <input
                type="text"
                value={dealId}
                onChange={(event) => setDealId(event.target.value)}
                className="h-9 rounded-md border border-input bg-background px-3 font-mono text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </label>
          )}
          <div>
            <button
              type="button"
              disabled={!explainReady || explain.isPending}
              onClick={submitExplain}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {ts("ask")}
            </button>
          </div>
          {explain.isError ? (
            <p role="alert" className="text-sm text-loss">
              {explain.error.message}
            </p>
          ) : null}
          {explain.data !== undefined ? (
            <div className="flex flex-col gap-2">
              <StatusBadge variant={explain.data.data.blocked ? "error" : "live"}>
                {explain.data.data.blocked ? ts("blocked") : ts("notBlocked")}
              </StatusBadge>
              <ul className="flex flex-col gap-2">
                {explain.data.data.reasons.map((reason, index) => (
                  <li key={`${reason.code}-${index}`} className="flex items-start gap-2 text-sm">
                    <SeverityBadge severity={reason.severity} />
                    <span title={reason.code}>{reason.message}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
