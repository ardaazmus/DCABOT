import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  DcaPlaceConfirmDialog,
  DcaSessionCreateForm,
  DcaSessionDetailPanel,
  DcaSessionsPanel,
  isDcaSessionCreateResponse,
  isDcaSessionDecisionResponse,
  isDcaSessionDetailResponse,
  isDcaSessionList,
  isDcaSessionPlaceResponse,
  isDcaSessionRow,
  type DcaSessionDetail,
  type DcaSessionRow,
} from "./DcaSessionsPanel";

const active: DcaSessionRow = {
  session_id: "ses-1",
  mode: "TESTNET",
  symbol: "BTCUSDT",
  average: "97500",
  qty: "0.002",
  realized_net_after_all_costs: "1.5",
  unrealized: "0.75",
  take_profit_price: "99450",
  halted: false,
  deal_complete: false,
  bindings: [{ local_order_id: "o1", role: "BASE", venue_order_id: 77001 }],
  starting_balance: "10000",
  virtual_balance: "10001.5",
};

const detail: DcaSessionDetail = {
  session_id: "ses-1",
  mode: "TESTNET",
  symbol: "BTCUSDT",
  average: "97500",
  qty: "0.002",
  cost: "195",
  anchor: "97000",
  take_profit_price: "99450",
  entry_notional: "195",
  realized_gross: "2",
  fees: "0.4",
  funding: "0.1",
  realized_net_after_all_costs: "1.5",
  unrealized: "0.75",
  equity: "1001.5",
  peak_equity: "1002",
  max_drawdown: "0.01",
  current_drawdown: "0.0005",
  retained_profit_base: "0",
  halted: false,
  safety_stopped: false,
  deal_duration_expired: false,
  deal_complete: false,
  blockers: ["KILL_SWITCH"],
  unsettled_orders: ["o1"],
  last_policy_rejection: "cap aşımı",
  bindings: [{ local_order_id: "o1", role: "BASE", venue_order_id: 77001 }],
  starting_balance: "10000",
  virtual_balance: "10001.5",
};

const done: DcaSessionRow = {
  ...active,
  session_id: "ses-2",
  halted: false,
  deal_complete: true,
  bindings: [],
};

const halted: DcaSessionRow = {
  ...active,
  session_id: "ses-3",
  halted: true,
  deal_complete: false,
  bindings: [],
};

describe("DcaSessionsPanel", () => {
  it("AA.4a: satırlar gerçek değerlerle dizilir", () => {
    render(<DcaSessionsPanel sessions={[active, done]} busy={false} error="" onRefresh={vi.fn()} />);
    expect(screen.getByText("2 oturum")).toBeInTheDocument();
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(within(rows[1]).getByText("BTCUSDT")).toBeInTheDocument();
    expect(within(rows[1]).getByText("Aktif")).toBeInTheDocument();
    expect(within(rows[2]).getByText("Tamamlandı")).toBeInTheDocument();
    expect(within(rows[1]).getByText("99450")).toBeInTheDocument();
  });

  it("AA.4a: durum-eşleme (halted) ve boş-bağlantı", () => {
    render(<DcaSessionsPanel sessions={[halted]} busy={false} error="" onRefresh={vi.fn()} />);
    const table = screen.getByRole("table");
    const row = within(table).getAllByRole("row")[1];
    expect(within(row).getByText("Durduruldu")).toBeInTheDocument();
    expect(within(row).getByText("—")).toBeInTheDocument();
  });

  it("AA.4a: boş liste, hata ve yenileme", () => {
    const onRefresh = vi.fn();
    const { unmount } = render(<DcaSessionsPanel sessions={[]} busy={false} error="" onRefresh={onRefresh} />);
    expect(screen.getByText("Kayıtlı DCA oturumu yok. Oturum oluşturma ayrı bir dilimde bağlanacak.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Oturumları yenile" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
    unmount();
    render(<DcaSessionsPanel sessions={[]} busy={true} error="okunamadı" onRefresh={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent("okunamadı");
    expect(screen.getByRole("button", { name: "Okunuyor…" })).toBeDisabled();
  });

  it("AA.4-create: form kimlik-alanlarıyla gönderir", () => {
    const onCreate = vi.fn();
    render(<DcaSessionCreateForm defaultSymbol="BTCUSDT" baseReady={true} busy={false} error="" createdId={null} onCreate={onCreate} />);
    fireEvent.click(screen.getByRole("button", { name: "Oturumu aç" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Oturum kimliği boş olamaz.");
    expect(onCreate).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Oturum kimliği"), { target: { value: "ses-9" } });
    fireEvent.change(screen.getByLabelText("Bot kimliği (opsiyonel)"), { target: { value: "bot-1" } });
    fireEvent.change(screen.getByLabelText("botUSD (sanal bakiye, opsiyonel)"), { target: { value: "abc" } });
    fireEvent.click(screen.getByRole("button", { name: "Oturumu aç" }));
    expect(screen.getByRole("alert")).toHaveTextContent("botUSD pozitif exact-ondalık olmalıdır");
    expect(onCreate).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("botUSD (sanal bakiye, opsiyonel)"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Oturumu aç" }));
    expect(screen.getByRole("alert")).toHaveTextContent("botUSD pozitif exact-ondalık olmalıdır");
    fireEvent.change(screen.getByLabelText("botUSD (sanal bakiye, opsiyonel)"), { target: { value: "10000" } });
    fireEvent.click(screen.getByRole("button", { name: "Oturumu aç" }));
    expect(onCreate).toHaveBeenCalledWith({ session_id: "ses-9", symbol: "BTCUSDT", bot_id: "bot-1", starting_balance: "10000", mode: "TESTNET" });
  });

  it("AA.4-create: mod-seçici PAPER gövdeye geçer (varsayılan TESTNET)", () => {
    const onCreate = vi.fn();
    render(<DcaSessionCreateForm defaultSymbol="BTCUSDT" baseReady={true} busy={false} error="" createdId={null} onCreate={onCreate} />);
    expect(screen.getByLabelText("Oturum modu")).toHaveValue("TESTNET");
    fireEvent.change(screen.getByLabelText("Oturum kimliği"), { target: { value: "ses-p" } });
    fireEvent.change(screen.getByLabelText("Oturum modu"), { target: { value: "PAPER" } });
    fireEvent.click(screen.getByRole("button", { name: "Oturumu aç" }));
    expect(onCreate).toHaveBeenCalledWith({ session_id: "ses-p", symbol: "BTCUSDT", bot_id: "", starting_balance: "", mode: "PAPER" });
  });

  it("AA.4-create: taban-bekleme, hata ve başarı", () => {
    const { unmount } = render(<DcaSessionCreateForm defaultSymbol="BTCUSDT" baseReady={false} busy={false} error="" createdId={null} onCreate={vi.fn()} />);
    expect(screen.getByText("Taban config bekleniyor — paper.json okununca form açılır.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Oturumu aç" })).not.toBeInTheDocument();
    unmount();
    render(<DcaSessionCreateForm defaultSymbol="BTCUSDT" baseReady={true} busy={false} error="kimlik çakışması" createdId="ses-9" onCreate={vi.fn()} />);
    expect(screen.getByText("Oturum açıldı: ses-9")).toBeInTheDocument();
  });

  it("AA.4-create: oluşturma-guardı", () => {
    expect(isDcaSessionCreateResponse({ data: { session_id: "ses-1" } })).toBe(true);
    expect(isDcaSessionCreateResponse({ data: {} })).toBe(false);
    expect(isDcaSessionCreateResponse({})).toBe(false);
  });

  it("AA.4a: guard sözleşmesi", () => {
    expect(isDcaSessionRow(active)).toBe(true);
    expect(isDcaSessionRow({ ...active, bindings: [{ local_order_id: "o1", role: "BASE" }] })).toBe(false);
    expect(isDcaSessionRow({ ...active, halted: "no" })).toBe(false);
    expect(isDcaSessionList({ data: [active, done] })).toBe(true);
    expect(isDcaSessionList({ data: [active, { ...done, qty: 2 }] })).toBe(false);
    expect(isDcaSessionList({})).toBe(false);
  });

  it("AA.4b: satır-seçimi oturum-kimliğini iletir, seçili satır işaretlenir", () => {
    const onSelect = vi.fn();
    render(<DcaSessionsPanel sessions={[active, done]} busy={false} error="" selectedId="ses-1" onRefresh={vi.fn()} onSelect={onSelect} />);
    const first = screen.getByRole("button", { name: "ses-1" });
    expect(first).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: "ses-2" })).not.toHaveAttribute("aria-current");
    fireEvent.click(screen.getByRole("button", { name: "ses-2" }));
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith("ses-2");
  });

  it("AA.4b: detay raporu + öneri dizilir, yenile/kapat iletilir", () => {
    const onClose = vi.fn();
    const onRefresh = vi.fn();
    render(
      <DcaSessionDetailPanel
        sessionId="ses-1"
        detail={detail}
        decision={{ role: "SAFETY:1", qty: "0.001", limit_price: "87300", notional: "87.3" }}
        decisionLoaded={true}
        busy={false}
        error=""
        syncBusyRole={null}
        syncError=""
        syncNotice=""
        placeBusy={false}
        placeError=""
        placeNotice=""
        paperFillBusy={false}
        paperFillError=""
        paperFillNotice=""
        onClose={onClose}
        onRefresh={onRefresh}
        onSync={vi.fn()}
        onPlace={vi.fn()}
        onPaperFill={vi.fn()}
      />,
    );
    expect(screen.getByText("97500")).toBeInTheDocument();
    expect(screen.getByText("99450")).toBeInTheDocument();
    expect(screen.getByText("KILL_SWITCH")).toBeInTheDocument();
    expect(screen.getByText("cap aşımı")).toBeInTheDocument();
    expect(screen.getByText("77001")).toBeInTheDocument();
    expect(screen.getByText("SAFETY:1")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Detayı yenile" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Kapat" }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("AA.4b: öneri-yok/yükleniyor durumlarında place kapalı, öneride açık", () => {
    const onPlace = vi.fn();
    const base = {
      sessionId: "ses-1",
      detail,
      busy: false,
      error: "",
      syncBusyRole: null as string | null,
      syncError: "",
      syncNotice: "",
      placeBusy: false,
      placeError: "",
      placeNotice: "",
      paperFillBusy: false,
      paperFillError: "",
      paperFillNotice: "",
      onClose: vi.fn(),
      onRefresh: vi.fn(),
      onSync: vi.fn(),
      onPlace,
      onPaperFill: vi.fn(),
    };
    const { unmount } = render(<DcaSessionDetailPanel {...base} decision={null} decisionLoaded={false} />);
    expect(screen.getByText("Öneri okunuyor…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Emir gönder (onaylı)" })).toBeDisabled();
    unmount();
    const second = render(<DcaSessionDetailPanel {...base} decision={null} decisionLoaded={true} />);
    expect(screen.getByText("Motorun sıradaki önerisi yok — gönderilecek emir yok.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Emir gönder (onaylı)" })).toBeDisabled();
    second.unmount();
    render(<DcaSessionDetailPanel {...base} decision={{ role: "BASE", qty: "0.002", limit_price: "97000", notional: "194" }} decisionLoaded={true} />);
    fireEvent.click(screen.getByRole("button", { name: "Emir gönder (onaylı)" }));
    expect(onPlace).toHaveBeenCalledTimes(1);
  });

  it("AA.4c: sync satır-başına rolü iletir, meşgulken kilitlenir", () => {
    const onSync = vi.fn();
    const { unmount } = render(
      <DcaSessionDetailPanel
        sessionId="ses-1"
        detail={detail}
        decision={null}
        decisionLoaded={true}
        busy={false}
        error=""
        syncBusyRole={null}
        syncError=""
        syncNotice="okundu"
        placeBusy={false}
        placeError=""
        placeNotice=""
        paperFillBusy={false}
        paperFillError=""
        paperFillNotice=""
        onClose={vi.fn()}
        onRefresh={vi.fn()}
        onSync={onSync}
        onPlace={vi.fn()}
        onPaperFill={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Eşitle" }));
    expect(onSync).toHaveBeenCalledWith("BASE");
    expect(screen.getByText("okundu")).toBeInTheDocument();
    unmount();
    render(
      <DcaSessionDetailPanel
        sessionId="ses-1"
        detail={detail}
        decision={null}
        decisionLoaded={true}
        busy={false}
        error=""
        syncBusyRole="BASE"
        syncError="başarısız"
        syncNotice=""
        placeBusy={false}
        placeError=""
        placeNotice=""
        paperFillBusy={false}
        paperFillError=""
        paperFillNotice=""
        onClose={vi.fn()}
        onRefresh={vi.fn()}
        onSync={vi.fn()}
        onPlace={vi.fn()}
        onPaperFill={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Eşitleniyor…" })).toBeDisabled();
    expect(screen.getByText("başarısız")).toBeInTheDocument();
  });

  it("AA.4c: diyalog TESTNET + dondurulmuş-parametre gösterir, girdi-içermez", () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(
      <DcaPlaceConfirmDialog
        sessionId="ses-1"
        symbol="BTCUSDT"
        draft={{ role: "SAFETY:1", qty: "0.001", limit_price: "87300", notional: "87.3" }}
        busy={false}
        error=""
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(screen.getByText("TESTNET")).toBeInTheDocument();
    expect(screen.getByText("SAFETY:1")).toBeInTheDocument();
    expect(screen.getByText("0.001")).toBeInTheDocument();
    expect(screen.getByText("87300")).toBeInTheDocument();
    expect(screen.getByText("87.3")).toBeInTheDocument();
    expect(screen.getByText("Limit fiyat (önizleme)")).toBeInTheDocument();
    expect(screen.getByText("Notional (önizleme)")).toBeInTheDocument();
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
    expect(screen.queryAllByRole("checkbox")).toHaveLength(0);
    expect(screen.queryAllByRole("spinbutton")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Vazgeç" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Onayla ve gönder" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("AA.4c: null-önizlemede sunucu-hesaplar metni aynen durur", () => {
    render(
      <DcaPlaceConfirmDialog
        sessionId="ses-1"
        symbol="BTCUSDT"
        draft={{ role: "BASE", qty: "0.002", limit_price: null, notional: null }}
        busy={false}
        error=""
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText(/uydurma değer yazılmadı/)).toBeInTheDocument();
    expect(screen.getByText("Sunucu hesaplar — UI finansal hesap yapmaz.")).toBeInTheDocument();
  });

  it("AA.4c: diyalog meşgulken kilitlenir, hatayı içinde gösterir", () => {
    render(
      <DcaPlaceConfirmDialog
        sessionId="ses-1"
        symbol="BTCUSDT"
        draft={{ role: "BASE", qty: "0.002", limit_price: "97000", notional: "194" }}
        busy={true}
        error="gate kapalı"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Gönderiliyor…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Vazgeç" })).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent("gate kapalı");
  });

  it("AA.4b/AA.4c: guard sözleşmeleri (detay/öneri/place)", () => {
    expect(isDcaSessionDetailResponse({ data: detail })).toBe(true);
    expect(isDcaSessionDetailResponse({ data: { ...detail, qty: 2 } })).toBe(false);
    expect(isDcaSessionDetailResponse({ data: { ...detail, blockers: "yok" } })).toBe(false);
    expect(isDcaSessionDetailResponse({ data: { ...detail, last_policy_rejection: 7 } })).toBe(false);
    expect(isDcaSessionDetailResponse({})).toBe(false);
    expect(isDcaSessionDecisionResponse({ data: null })).toBe(true);
    expect(isDcaSessionDecisionResponse({ data: { role: "BASE", qty: "0.002", limit_price: "97000", notional: "194" } })).toBe(true);
    expect(isDcaSessionDecisionResponse({ data: { role: "BASE", qty: "0.002", limit_price: null, notional: null } })).toBe(true);
    expect(isDcaSessionDecisionResponse({ data: { role: "BASE", qty: "0.002" } })).toBe(false);
    expect(isDcaSessionDecisionResponse({ data: { role: "BASE", qty: "0.002", limit_price: 97000, notional: "194" } })).toBe(false);
    expect(isDcaSessionDecisionResponse({ data: { role: "BASE" } })).toBe(false);
    expect(isDcaSessionDecisionResponse({ data: "yok" })).toBe(false);
    expect(isDcaSessionPlaceResponse({ data: { session_id: "ses-1", venue_order_id: 77002, venue_status: "NEW" } })).toBe(true);
    expect(isDcaSessionPlaceResponse({ data: { session_id: "ses-1", venue_order_id: "77002", venue_status: "NEW" } })).toBe(false);
    expect(isDcaSessionPlaceResponse({ data: { session_id: "ses-1", venue_order_id: 77002 } })).toBe(false);
    expect(isDcaSessionRow({ ...active, bindings: [{ local_order_id: "o1", role: "BASE", venue_order_id: "v1" }] })).toBe(false);
  });

  it("Paper-spot: liste sanal-bakiye sütununu dizer, nullda tire", () => {
    const plain = { ...active, session_id: "ses-9", starting_balance: null, virtual_balance: null };
    render(<DcaSessionsPanel sessions={[active, plain]} busy={false} error="" onRefresh={vi.fn()} />);
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    expect(within(rows[0]).getByText("Sanal Bakiye")).toBeInTheDocument();
    expect(within(rows[1]).getByText("10001.5")).toBeInTheDocument();
    expect(within(rows[2]).getAllByText("—").length).toBeGreaterThanOrEqual(1);
  });

  it("Paper-spot: detay bakiye-satırlarını koşullu dizer", () => {
    const base = {
      sessionId: "ses-1",
      busy: false,
      error: "",
      syncBusyRole: null as string | null,
      syncError: "",
      syncNotice: "",
      placeBusy: false,
      placeError: "",
      placeNotice: "",
      paperFillBusy: false,
      paperFillError: "",
      paperFillNotice: "",
      onClose: vi.fn(),
      onRefresh: vi.fn(),
      onSync: vi.fn(),
      onPlace: vi.fn(),
      onPaperFill: vi.fn(),
    };
    const { unmount } = render(
      <DcaSessionDetailPanel {...base} detail={detail} decision={null} decisionLoaded={true} />,
    );
    expect(screen.getByText("Başlangıç bakiyesi (botUSD)")).toBeInTheDocument();
    expect(screen.getByText("10000")).toBeInTheDocument();
    expect(screen.getByText("Sanal bakiye")).toBeInTheDocument();
    unmount();
    render(
      <DcaSessionDetailPanel
        {...base}
        detail={{ ...detail, starting_balance: null, virtual_balance: null }}
        decision={null}
        decisionLoaded={true}
      />,
    );
    expect(screen.queryByText("Başlangıç bakiyesi (botUSD)")).not.toBeInTheDocument();
    expect(screen.queryByText("Sanal bakiye")).not.toBeInTheDocument();
  });

  it("Paper-spot: paper-fill PAPER-rozetli, önerisiz-kapalı, diyaloğsuz-çağırır", () => {
    const onPaperFill = vi.fn();
    const base = {
      sessionId: "ses-1",
      detail,
      busy: false,
      error: "",
      syncBusyRole: null as string | null,
      syncError: "",
      syncNotice: "",
      placeBusy: false,
      placeError: "",
      placeNotice: "",
      paperFillBusy: false,
      paperFillError: "doldurulamadı",
      paperFillNotice: "",
      onClose: vi.fn(),
      onRefresh: vi.fn(),
      onSync: vi.fn(),
      onPlace: vi.fn(),
      onPaperFill,
    };
    const { unmount } = render(<DcaSessionDetailPanel {...base} decision={null} decisionLoaded={true} />);
    expect(screen.getByText("PAPER")).toBeInTheDocument();
    expect(screen.getAllByText("TESTNET")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Paper Fill" })).toBeDisabled();
    expect(screen.getByText("doldurulamadı")).toBeInTheDocument();
    unmount();
    render(
      <DcaSessionDetailPanel
        {...base}
        paperFillError=""
        paperFillNotice="dolduruldu"
        decision={{ role: "BASE", qty: "0.002", limit_price: "97000", notional: "194" }}
        decisionLoaded={true}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Paper Fill" }));
    expect(onPaperFill).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(screen.getByText("dolduruldu")).toBeInTheDocument();
  });

  it("Paper-spot: guard bakiye-alanlarını doğrular", () => {
    expect(isDcaSessionDetailResponse({ data: { ...detail, virtual_balance: 7 } })).toBe(false);
    expect(isDcaSessionDetailResponse({ data: { ...detail, starting_balance: null, virtual_balance: null } })).toBe(true);
    expect(isDcaSessionRow({ ...active, virtual_balance: 10001.5 })).toBe(false);
  });

  it("Paper-spot: liste mod-sütunu oturum-rozeti dizer", () => {
    const paper = { ...active, session_id: "ses-p", mode: "PAPER" as const };
    render(<DcaSessionsPanel sessions={[active, paper]} busy={false} error="" onRefresh={vi.fn()} />);
    const table = screen.getByRole("table");
    const rows = within(table).getAllByRole("row");
    expect(within(rows[0]).getByText("Mod")).toBeInTheDocument();
    expect(within(rows[1]).getByText("TESTNET")).toBeInTheDocument();
    expect(within(rows[2]).getByText("PAPER")).toBeInTheDocument();
  });

  it("Paper-spot: detay başlık-rozeti + PAPER kapıları (place/sync kapalı, fill açık)", () => {
    const onPlace = vi.fn();
    const onPaperFill = vi.fn();
    const base = {
      sessionId: "ses-p",
      busy: false,
      error: "",
      syncBusyRole: null as string | null,
      syncError: "",
      syncNotice: "",
      placeBusy: false,
      placeError: "",
      placeNotice: "",
      paperFillBusy: false,
      paperFillError: "",
      paperFillNotice: "",
      onClose: vi.fn(),
      onRefresh: vi.fn(),
      onSync: vi.fn(),
      onPlace,
      onPaperFill,
    };
    render(
      <DcaSessionDetailPanel
        {...base}
        detail={{ ...detail, session_id: "ses-p", mode: "PAPER" }}
        decision={{ role: "BASE", qty: "0.002", limit_price: "97000", notional: "194" }}
        decisionLoaded={true}
      />,
    );
    expect(screen.getByText("PAPER oturumda testnet emri verilemez (sunucu 409 ile reddeder) — sanal dolum için Paper Fill kullanın.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Emir gönder (onaylı)" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Eşitle" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Paper Fill" }));
    expect(onPaperFill).toHaveBeenCalledTimes(1);
    expect(onPlace).not.toHaveBeenCalled();
  });

  it("Paper-spot: guard mod-alanını doğrular", () => {
    expect(isDcaSessionRow({ ...active, mode: "MAINNET" })).toBe(false);
    expect(isDcaSessionRow({ ...active, mode: undefined })).toBe(false);
    expect(isDcaSessionDetailResponse({ data: { ...detail, mode: "PAPER" } })).toBe(true);
    expect(isDcaSessionDetailResponse({ data: { ...detail, mode: "SPOT" } })).toBe(false);
  });
});
