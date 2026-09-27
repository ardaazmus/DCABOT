"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { DataTable, type TableColumn } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { EnumValue } from "@/components/enum-value";
import { Money } from "@/components/money";
import { Skeleton } from "@/components/skeleton";
import { StatusBadge } from "@/components/status-badge";
import { ApiHttpError } from "@/lib/api/client";
import { useTestnetAccount, useTestnetOrders } from "@/lib/api/queries";
import type { TestnetOrders } from "@/lib/api/schemas";
import { isDecimalString, type DecimalString } from "@/lib/decimal";

function toDecimal(text: string): DecimalString | undefined {
  return isDecimalString(text) ? text : undefined;
}

type BalanceRow = { asset: string; free: DecimalString | undefined; locked: DecimalString | undefined };
type OrderRow = TestnetOrders["orders"][number];

export default function ConnectionPage() {
  const ts = useTranslations("settings");
  const tm = useTranslations("market");
  const account = useTestnetAccount();
  const [ordersOpen, setOrdersOpen] = useState(false);
  const orders = useTestnetOrders(ordersOpen && account.data !== undefined);

  const unconfigured =
    account.error instanceof ApiHttpError &&
    account.error.problem?.code === "TESTNET_CREDENTIAL_NOT_CONFIGURED";

  const balanceColumns: TableColumn<BalanceRow>[] = [
    { accessorKey: "asset", header: ts("asset") },
    {
      accessorKey: "free",
      header: ts("free"),
      cell: ({ row }) => <Money value={row.original.free} suffix={row.original.asset} />,
      enableSorting: false,
    },
    {
      accessorKey: "locked",
      header: ts("locked"),
      cell: ({ row }) => <Money value={row.original.locked} suffix={row.original.asset} />,
      enableSorting: false,
    },
  ];

  const orderColumns: TableColumn<OrderRow>[] = [
    { accessorKey: "symbol", header: tm("pair") },
    {
      accessorKey: "side",
      header: ts("orderSide"),
      cell: ({ row }) => <EnumValue code={row.original.side} />,
      enableSorting: false,
    },
    {
      accessorKey: "type",
      header: ts("orderType"),
      cell: ({ row }) => <EnumValue code={row.original.type} />,
      enableSorting: false,
    },
    {
      accessorKey: "status",
      header: ts("orderStatus"),
      cell: ({ row }) => <EnumValue code={row.original.status} />,
      enableSorting: false,
    },
    {
      accessorKey: "price",
      header: ts("orderPrice"),
      cell: ({ row }) => <Money value={toDecimal(row.original.price)} />,
      enableSorting: false,
    },
    {
      accessorKey: "orig_qty",
      header: ts("orderQty"),
      cell: ({ row }) => <Money value={toDecimal(row.original.orig_qty)} />,
      enableSorting: false,
    },
    {
      accessorKey: "executed_qty",
      header: ts("orderExecuted"),
      cell: ({ row }) => <Money value={toDecimal(row.original.executed_qty)} />,
      enableSorting: false,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">{ts("testnetTitle")}</h2>
        {account.isPending ? (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : unconfigured ? (
          <EmptyState title={ts("unconfigured")} description={ts("unconfiguredHint")} />
        ) : account.isError || account.data === undefined ? (
          <p role="alert" className="text-sm text-loss">
            {account.error instanceof Error ? account.error.message : ts("unconfigured")}
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-muted-foreground">{ts("canTrade")}:</span>
              <StatusBadge variant={account.data.can_trade ? "live" : "stopped"}>
                {account.data.can_trade ? ts("yes") : ts("no")}
              </StatusBadge>
              <span className="font-mono text-xs text-muted-foreground">
                {account.data.account_type} · {account.data.environment}
              </span>
            </div>
            <h3 className="text-base font-semibold">{ts("balances")}</h3>
            <DataTable
              columns={balanceColumns}
              data={account.data.balances.map((balance) => ({
                asset: balance.asset,
                free: toDecimal(balance.free),
                locked: toDecimal(balance.locked),
              }))}
              emptyTitle={ts("balances")}
              pageSize={25}
            />
          </>
        )}
      </section>

      {account.data === undefined ? null : (
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">{ts("orders")}</h3>
            <button
              type="button"
              aria-expanded={ordersOpen}
              onClick={() => setOrdersOpen((open) => !open)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium hover:bg-muted"
            >
              {ordersOpen ? ts("hideOrders") : ts("showOrders")}
            </button>
          </div>
          {ordersOpen ? (
            orders.isPending ? (
              <Skeleton className="h-40 w-full" />
            ) : orders.isError || orders.data === undefined ? (
              <p role="alert" className="text-sm text-loss">
                {orders.error instanceof Error ? orders.error.message : ts("unconfigured")}
              </p>
            ) : (
              <DataTable
                columns={orderColumns}
                data={orders.data.orders}
                emptyTitle={ts("orders")}
                pageSize={25}
              />
            )
          ) : null}
        </section>
      )}
    </div>
  );
}
