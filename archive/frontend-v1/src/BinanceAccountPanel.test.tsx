import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  BinanceAccountPanel,
  isBinanceAccountSnapshot,
  isBinanceOpenOrdersSnapshot,
  isTestnetCredentialNotConfigured,
  type BinanceAccountSnapshot,
  type BinanceOpenOrdersSnapshot,
} from "./BinanceAccountPanel";

const account: BinanceAccountSnapshot = {
  environment: "BINANCE_SPOT_TESTNET",
  account_type: "SPOT",
  can_trade: true,
  can_withdraw: false,
  can_deposit: true,
  permissions: ["SPOT"],
  update_time_ms: 1700000000000,
  balances_count: 2,
  balances: [
    { asset: "BTC", free: "0.5", locked: "0.1" },
    { asset: "USDT", free: "1000", locked: "0" },
  ],
  response_sha256: "abc123",
  observed_at_us: 1700000000000000,
  read_only: true,
  credential_required: true,
};

const orders: BinanceOpenOrdersSnapshot = {
  environment: "BINANCE_SPOT_TESTNET",
  orders: [
    {
      symbol: "BTCUSDT", order_id: 42, client_order_id: "client-1",
      side: "BUY", type: "LIMIT", status: "NEW",
      price: "50000", orig_qty: "0.1", executed_qty: "0",
      time_ms: 1700000000000, update_time_ms: 1700000001000,
    },
  ],
  count: 1,
  read_only: true,
  credential_required: true,
};

describe("BinanceAccountPanel ready", () => {
  it("bakiye ve açık emir tablolarını, TESTNET rozetini ve salt-okunur sınır notunu gösterir", () => {
    render(<BinanceAccountPanel account={account} orders={orders} status="ready" error="" onRetry={() => {}} />);

    expect(screen.getByText("TESTNET")).toBeInTheDocument();
    expect(screen.getByText("CONNECTED_READ_ONLY")).toBeInTheDocument();
    expect(screen.getByText("BTC")).toBeInTheDocument();
    expect(screen.getByText("1000")).toBeInTheDocument();
    expect(screen.getByText("BTCUSDT")).toBeInTheDocument();
    expect(screen.getByText("BUY")).toBeInTheDocument();
    expect(screen.getByText(/Bu ekran salt okunurdur/)).toBeInTheDocument();
    expect(screen.getByText(/gerçek emir vermez/)).toBeInTheDocument();
    expect(screen.getByText(/sanal bakiyesidir/)).toBeInTheDocument();
  });

  it("bakiye listesi boşsa boş-durum mesajı gösterir", () => {
    const emptyAccount: BinanceAccountSnapshot = { ...account, balances: [], balances_count: 120 };
    render(<BinanceAccountPanel account={emptyAccount} orders={orders} status="ready" error="" onRetry={() => {}} />);

    expect(screen.getByText("Sıfır olmayan bakiye yok.")).toBeInTheDocument();
    expect(screen.queryByText("Açık emir yok.")).not.toBeInTheDocument();
  });

  it("açık emir listesi boşsa boş-durum mesajı gösterir", () => {
    const emptyOrders: BinanceOpenOrdersSnapshot = { ...orders, orders: [], count: 0 };
    render(<BinanceAccountPanel account={account} orders={emptyOrders} status="ready" error="" onRetry={() => {}} />);

    expect(screen.getByText("Açık emir yok.")).toBeInTheDocument();
    expect(screen.queryByText("Sıfır olmayan bakiye yok.")).not.toBeInTheDocument();
  });
});

describe("BinanceAccountPanel durumları", () => {
  it("not_configured sakin bir bilgi kartı gösterir, alarm vermez", () => {
    render(<BinanceAccountPanel account={null} orders={null} status="not_configured" error="" onRetry={() => {}} />);

    expect(screen.getByText("Testnet hesabı henüz yapılandırılmadı.")).toBeInTheDocument();
    expect(screen.getByText("NOT_CONFIGURED")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("error alarm gösterir ve Tekrar dene onRetry çağırır", () => {
    const onRetry = vi.fn();
    render(<BinanceAccountPanel account={null} orders={null} status="error" error="bağlantı koptu" onRetry={onRetry} />);

    const alert = screen.getByRole("alert");
    expect(within(alert).getByText("bağlantı koptu")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tekrar dene" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("loading okuma mesajı gösterir", () => {
    render(<BinanceAccountPanel account={null} orders={null} status="loading" error="" onRetry={() => {}} />);

    expect(screen.getByRole("status")).toHaveTextContent("Testnet hesap ve açık emirler okunuyor…");
  });
});

describe("BinanceAccountPanel type guard'ları", () => {
  it("geçerli snapshot'ları kabul eder, bozuk gövdeleri reddeder", () => {
    expect(isBinanceAccountSnapshot(account)).toBe(true);
    expect(isBinanceOpenOrdersSnapshot(orders)).toBe(true);
    expect(isBinanceAccountSnapshot({ ...account, environment: "ELSEWHERE" })).toBe(false);
    expect(isBinanceAccountSnapshot({ ...account, balances: [{ asset: "BTC" }] })).toBe(false);
    expect(isBinanceOpenOrdersSnapshot({ ...orders, orders: [{ symbol: "BTCUSDT" }] })).toBe(false);
    expect(isBinanceOpenOrdersSnapshot(null)).toBe(false);
  });

  it("credential kurulum eksikliği gövdesini tanır", () => {
    expect(isTestnetCredentialNotConfigured({ code: "TESTNET_CREDENTIAL_NOT_CONFIGURED", detail: "x" })).toBe(true);
    expect(isTestnetCredentialNotConfigured({ code: "OTHER", detail: "x" })).toBe(false);
    expect(isTestnetCredentialNotConfigured(null)).toBe(false);
  });
});
