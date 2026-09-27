"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { StatusBadge } from "@/components/status-badge";
import {
  useTelegramConfigure,
  useTelegramEnabled,
  useTelegramForget,
  useTelegramStatus,
  useTelegramTest,
} from "@/lib/api/queries";

/**
 * Telegram ayar kartı: token kasaya yazılır, ekrana asla geri gelmez.
 * Durum rozeti + chat kimliği + test/aç-kapa/unut eylemleri.
 */
export function TelegramSettingsCard() {
  const t = useTranslations("notifications");
  const status = useTelegramStatus();
  const configure = useTelegramConfigure();
  const test = useTelegramTest();
  const toggle = useTelegramEnabled();
  const forget = useTelegramForget();
  const [token, setToken] = useState("");
  const [chatId, setChatId] = useState("");
  const data = status.data?.data;

  function save() {
    configure.mutate(
      { token: token.trim(), chat_id: chatId.trim(), enabled: true },
      { onSuccess: () => setToken("") },
    );
  }

  return (
    <section
      data-testid="telegram-settings"
      aria-label={t("telegramTitle")}
      className="flex flex-col gap-3 rounded-xl border border-border p-4"
    >
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-base font-semibold">{t("telegramTitle")}</h2>
        {status.isPending ? null : data ? (
          <StatusBadge variant={data.configured && data.enabled ? "running" : "stopped"}>
            {data.vault !== "OK"
              ? t("telegramVaultDown")
              : data.configured
                ? `${t("telegramConnected")}${data.enabled ? "" : " · ⏸"}`
                : t("telegramNotConfigured")}
          </StatusBadge>
        ) : null}
      </div>
      <p className="text-sm text-muted-foreground">{t("telegramHint")}</p>
      {data?.vault !== "OK" && !status.isPending ? (
        <p role="alert" className="text-sm text-muted-foreground">
          {t("telegramVaultDown")}
        </p>
      ) : (
        <>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">{t("telegramToken")}</span>
            <input
              type="password"
              autoComplete="off"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              placeholder="123456:ABC…"
              data-testid="telegram-token"
              className="rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium">{t("telegramChat")}</span>
            <input
              type="text"
              inputMode="numeric"
              value={chatId}
              placeholder={data?.chat_id !== "" ? data?.chat_id : t("telegramChatHint")}
              onChange={(event) => setChatId(event.target.value)}
              data-testid="telegram-chat"
              className="rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={save}
              disabled={configure.isPending || token.trim() === "" || chatId.trim() === ""}
              data-testid="telegram-save"
              className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent/90 disabled:opacity-40"
            >
              {t("telegramSave")}
            </button>
            {data?.configured === true ? (
              <>
                <button
                  type="button"
                  onClick={() => test.mutate()}
                  disabled={test.isPending}
                  data-testid="telegram-test"
                  className="rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-40"
                >
                  {t("telegramTest")}
                </button>
                <button
                  type="button"
                  onClick={() => toggle.mutate({ enabled: !(data?.enabled ?? false) })}
                  disabled={toggle.isPending}
                  data-testid="telegram-toggle"
                  className="rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-40"
                >
                  {data?.enabled === true ? t("telegramDisable") : t("telegramEnable")}
                </button>
                <button
                  type="button"
                  onClick={() => forget.mutate()}
                  disabled={forget.isPending}
                  data-testid="telegram-forget"
                  className="rounded-md border border-input px-3 py-1.5 text-sm font-medium text-destructive hover:bg-muted disabled:opacity-40"
                >
                  {t("telegramForget")}
                </button>
              </>
            ) : null}
          </div>
          {configure.isError ? (
            <p role="alert" data-testid="telegram-error" className="text-sm text-destructive">
              {configure.error instanceof Error ? configure.error.message : ""}
            </p>
          ) : null}
          {test.isSuccess ? (
            <p data-testid="telegram-test-ok" className="text-sm text-muted-foreground">
              {t("telegramTestOk")} (#{test.data.data.message_id})
            </p>
          ) : null}
          {test.isError ? (
            <p role="alert" className="text-sm text-destructive">
              {test.error instanceof Error ? test.error.message : ""}
            </p>
          ) : null}
          {data?.last_error != null ? (
            <p className="font-mono text-xs text-muted-foreground">
              {t("telegramLastError")}: {data.last_error}
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}
