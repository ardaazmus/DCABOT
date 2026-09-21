export type PaperPosition = { symbol: string; qty: string };

export type PaperOrder = {
  client_order_id: string;
  symbol: string;
  side: string;
  order_type: string;
  qty: string;
  limit_price: string | null;
  filled_qty: string;
  status: string;
};

export type PaperFill = {
  fill_id: string;
  client_order_id: string;
  event_id: string;
  symbol: string;
  side: string;
  price: string;
  qty: string;
  notional: string;
};

export type PaperMark = { symbol: string; price: string; event_id: string };

export type PaperSnapshot = {
  session_id: string;
  status: string;
  cash: string;
  positions: PaperPosition[];
  orders: PaperOrder[];
  fills: PaperFill[];
  marks: PaperMark[];
};

import { WindowExpander, useWindowedList } from "./renderWindow";

export type PaperPrint = {
  event_id: string;
  symbol: string;
  price: string;
  qty: string;
};

export type PaperOrderDraft = {
  symbol: string;
  side: string;
  qty: string;
  clientOrderId: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function isPaperSnapshot(value: unknown): value is PaperSnapshot {
  if (!isRecord(value)) return false;
  if (typeof value.session_id !== "string") return false;
  if (typeof value.status !== "string") return false;
  if (typeof value.cash !== "string") return false;
  if (!Array.isArray(value.positions) || !Array.isArray(value.orders)) return false;
  if (!Array.isArray(value.fills) || !Array.isArray(value.marks)) return false;
  const positionsOk = value.positions.every(
    (p: unknown) => isRecord(p) && typeof p.symbol === "string" && typeof p.qty === "string",
  );
  const ordersOk = value.orders.every(
    (o: unknown) =>
      isRecord(o) &&
      typeof o.client_order_id === "string" &&
      typeof o.symbol === "string" &&
      typeof o.side === "string" &&
      typeof o.order_type === "string" &&
      typeof o.qty === "string" &&
      (o.limit_price === null || typeof o.limit_price === "string") &&
      typeof o.filled_qty === "string" &&
      typeof o.status === "string",
  );
  const fillsOk = value.fills.every(
    (f: unknown) =>
      isRecord(f) &&
      typeof f.fill_id === "string" &&
      typeof f.client_order_id === "string" &&
      typeof f.event_id === "string" &&
      typeof f.symbol === "string" &&
      typeof f.side === "string" &&
      typeof f.price === "string" &&
      typeof f.qty === "string" &&
      typeof f.notional === "string",
  );
  const marksOk = value.marks.every(
    (m: unknown) =>
      isRecord(m) &&
      typeof m.symbol === "string" &&
      typeof m.price === "string" &&
      typeof m.event_id === "string",
  );
  return positionsOk && ordersOk && fillsOk && marksOk;
}

export function isPaperPrints(value: unknown): value is PaperPrint[] {
  return (
    Array.isArray(value) &&
    value.every(
      (p: unknown) =>
        isRecord(p) &&
        typeof p.event_id === "string" &&
        typeof p.symbol === "string" &&
        typeof p.price === "string" &&
        typeof p.qty === "string",
    )
  );
}

export function PaperPanel({
  snapshot,
  prints,
  busy,
  error,
  orderDraft,
  onActivate,
  onRefresh,
  onOrderDraftChange,
  onPlace,
  onFill,
}: {
  snapshot: PaperSnapshot | null;
  prints: PaperPrint[];
  busy: boolean;
  error: string;
  orderDraft: PaperOrderDraft;
  onActivate: () => void;
  onRefresh: () => void;
  onOrderDraftChange: (draft: PaperOrderDraft) => void;
  onPlace: () => void;
  onFill: (clientOrderId: string, eventId: string) => void;
}) {
  if (snapshot === null) {
    return (
      <section className="panel paper-panel" aria-labelledby="paper-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">PAPER TRADING</p>
            <h2 id="paper-title">Paper trading</h2>
          </div>
        </div>
        <p className="helper-text">
          Gerçek public piyasa verisiyle sanal para üzerinden deneme yapılır; credential gerekmez, gerçek emir verilmez.
        </p>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <button className="primary-button" type="button" disabled={busy} onClick={onActivate}>
          {busy ? "Açılıyor…" : "Paper session aç"}
        </button>
      </section>
    );
  }

  const windowedPrints = useWindowedList(prints, 50);

  const openOrder = snapshot.orders.find(
    (o) => o.status === "SIMULATED_NEW" || o.status === "SIMULATED_PARTIAL",
  );

  return (
    <section className="panel paper-panel" aria-labelledby="paper-title">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">PAPER TRADING</p>
          <h2 id="paper-title">Paper trading</h2>
        </div>
        <span className="state-label ready">{snapshot.status}</span>
      </div>
      <div className="paper-facts">
        <span>
          Nakit (sanal para): <strong>{snapshot.cash} USDT</strong>
        </span>
        <span>Oturum: {snapshot.session_id.slice(0, 12)}…</span>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}

      <h3 className="paper-subheading">Piyasa baskıları</h3>
      <button className="secondary-button" type="button" disabled={busy} onClick={onRefresh}>
        {busy ? "Yenileniyor…" : "Piyasayı yenile"}
      </button>
      {prints.length > 0 && (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>Olay</th>
                <th>Sembol</th>
                <th>Fiyat</th>
                <th>Miktar</th>
                <th>Doldur</th>
              </tr>
            </thead>
            <tbody>
              {windowedPrints.visible.map((print) => (
                <tr key={print.event_id}>
                  <td>{print.event_id}</td>
                  <td>{print.symbol}</td>
                  <td>{print.price}</td>
                  <td>{print.qty}</td>
                  <td>
                    <button
                      className="catalog-secondary-button paper-fill-button"
                      type="button"
                      disabled={busy || !openOrder}
                      title={openOrder ? `Açık emir ${openOrder.client_order_id} bu baskıdan doldurulur` : "Önce açık bir sanal emir verin"}
                      onClick={() => openOrder && onFill(openOrder.client_order_id, print.event_id)}
                    >
                      {print.event_id} doldur
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {windowedPrints.hasMore && <WindowExpander shown={windowedPrints.shown} total={windowedPrints.total} onMore={windowedPrints.showMore} />}
        </div>
      )}

      <h3 className="paper-subheading">Sanal emir</h3>
      <div className="paper-order-form">
        <label className="field">
          <span className="field-label">Sembol</span>
          <span className="input-wrap">
            <input
              aria-label="Sembol"
              value={orderDraft.symbol}
              onChange={(event) => onOrderDraftChange({ ...orderDraft, symbol: event.target.value })}
            />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Yön (BUY/SELL)</span>
          <span className="input-wrap">
            <input
              aria-label="Yön"
              value={orderDraft.side}
              onChange={(event) => onOrderDraftChange({ ...orderDraft, side: event.target.value })}
            />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Miktar</span>
          <span className="input-wrap">
            <input
              aria-label="Miktar"
              value={orderDraft.qty}
              onChange={(event) => onOrderDraftChange({ ...orderDraft, qty: event.target.value })}
            />
          </span>
        </label>
        <label className="field">
          <span className="field-label">Emir ID</span>
          <span className="input-wrap">
            <input
              aria-label="Emir ID"
              value={orderDraft.clientOrderId}
              onChange={(event) => onOrderDraftChange({ ...orderDraft, clientOrderId: event.target.value })}
            />
          </span>
        </label>
      </div>
      <button className="primary-button" type="button" disabled={busy} onClick={onPlace}>
        Sanal emir ver
      </button>

      <h3 className="paper-subheading">Emirler</h3>
      {snapshot.orders.length === 0 ? (
        <div className="empty-state">Henüz sanal emir yok.</div>
      ) : (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Sembol</th>
                <th>Yön</th>
                <th>Miktar</th>
                <th>Dolan</th>
                <th>Durum</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.orders.map((order) => (
                <tr key={order.client_order_id}>
                  <td>{order.client_order_id}</td>
                  <td>{order.symbol}</td>
                  <td>{order.side}</td>
                  <td>{order.qty}</td>
                  <td>{order.filled_qty}</td>
                  <td>{order.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3 className="paper-subheading">Pozisyonlar</h3>
      {snapshot.positions.length === 0 ? (
        <div className="empty-state">Açık pozisyon yok.</div>
      ) : (
        <div className="table-wrap paper-result">
          <table>
            <thead>
              <tr>
                <th>Sembol</th>
                <th>Miktar</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.positions.map((position) => (
                <tr key={position.symbol}>
                  <td>{position.symbol}</td>
                  <td>{position.qty}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="table-note">
        <span className="note-icon">↳</span> Tüm bakiyeler sanal paradır; dolumlar yalnız sunucunun gördüğü gerçek baskılardan yapılır.
      </div>
    </section>
  );
}
