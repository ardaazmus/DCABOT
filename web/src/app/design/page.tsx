"use client";

import { useState } from "react";

import { ChartCard } from "@/components/chart-card";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { DataTable, type TableColumn } from "@/components/data-table";
import { EmptyState } from "@/components/empty-state";
import { Money, Price, Qty } from "@/components/money";
import { Pnl } from "@/components/pnl";
import { ProgressToTarget } from "@/components/progress-to-target";
import { Skeleton } from "@/components/skeleton";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import { parseDecimal, type DecimalString } from "@/lib/decimal";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4 border-b border-border py-8 last:border-0">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

type DealRow = {
  pair: string;
  profit: DecimalString;
  progress: DecimalString;
  status: "running" | "paused" | "stopped";
};

const DEAL_COLUMNS: TableColumn<DealRow>[] = [
  { accessorKey: "pair", header: "Parite" },
  {
    accessorKey: "profit",
    header: "Kâr (USDT)",
    cell: ({ row }) => <Pnl value={row.original.profit} suffix="USDT" />,
  },
  {
    accessorKey: "progress",
    header: "TP",
    cell: ({ row }) => <ProgressToTarget percent={row.original.progress} />,
    enableSorting: false,
  },
  {
    accessorKey: "status",
    header: "Durum",
    cell: ({ row }) => (
      <StatusBadge variant={row.original.status}>{row.original.status}</StatusBadge>
    ),
  },
];

const DEAL_ROWS: DealRow[] = [
  { pair: "BTCUSDT", profit: parseDecimal("12.5"), progress: parseDecimal("62"), status: "running" },
  { pair: "ETHUSDT", profit: parseDecimal("-3.25"), progress: parseDecimal("18.5"), status: "running" },
  { pair: "SOLUSDT", profit: parseDecimal("0"), progress: parseDecimal("0"), status: "paused" },
  { pair: "BNBUSDT", profit: parseDecimal("48.1"), progress: parseDecimal("91"), status: "running" },
  { pair: "XRPUSDT", profit: parseDecimal("-0.75"), progress: parseDecimal("44"), status: "stopped" },
  { pair: "DOGEUSDT", profit: parseDecimal("5.0"), progress: parseDecimal("30"), status: "running" },
  { pair: "ADAUSDT", profit: parseDecimal("1.2"), progress: parseDecimal("55"), status: "paused" },
  { pair: "AVAXUSDT", profit: parseDecimal("-11.4"), progress: parseDecimal("8"), status: "stopped" },
  { pair: "LINKUSDT", profit: parseDecimal("7.75"), progress: parseDecimal("70"), status: "running" },
  { pair: "ARBUSDT", profit: parseDecimal("2.3"), progress: parseDecimal("25"), status: "running" },
  { pair: "OPUSDT", profit: parseDecimal("-1.05"), progress: parseDecimal("39"), status: "paused" },
  { pair: "NEARUSDT", profit: parseDecimal("9.9"), progress: parseDecimal("83"), status: "running" },
];

export default function DesignPage() {
  const [confirmPlain, setConfirmPlain] = useState(false);
  const [confirmReason, setConfirmReason] = useState(false);
  const [range, setRange] = useState("7d");
  const [confirmed, setConfirmed] = useState("");

  return (
    <div className="mx-auto flex max-w-5xl flex-col">
      <h1 className="text-2xl font-semibold tracking-tight">Bileşen galerisi</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Örnek veriler durağan metinlerdir; bu sayfa backend&apos;e bağlanmaz.
      </p>

      <Section title="Anlamsal renkler">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-md bg-profit px-3 py-1.5 text-sm font-medium text-white">profit</span>
          <span className="rounded-md bg-loss px-3 py-1.5 text-sm font-medium text-white">loss</span>
          <span className="rounded-md bg-safety px-3 py-1.5 text-sm font-medium text-black">safety</span>
          <span className="rounded-md bg-entry px-3 py-1.5 text-sm font-medium text-white">entry</span>
          <span className="rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-accent-foreground">accent</span>
        </div>
      </Section>

      <Section title="Money / Price / Qty">
        <div className="flex flex-col gap-2 text-sm">
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Money</span>
            <Money value={parseDecimal("1234.5")} suffix="USDT" />
          </div>
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Price</span>
            <Price value={parseDecimal("67412.25")} suffix="USDT" />
          </div>
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Qty</span>
            <Qty value={parseDecimal("0.0025")} suffix="BTC" />
          </div>
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Tanımsız</span>
            <Money value={undefined} suffix="USDT" />
          </div>
        </div>
      </Section>

      <Section title="PnL">
        <div className="flex flex-col gap-2 text-sm">
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Pozitif</span>
            <Pnl value={parseDecimal("12.5")} suffix="USDT" />
            <Pnl value={parseDecimal("3.2")} variant="percent" />
          </div>
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Negatif</span>
            <Pnl value={parseDecimal("-3.25")} suffix="USDT" />
            <Pnl value={parseDecimal("-1.1")} variant="percent" />
          </div>
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Sıfır</span>
            <Pnl value={parseDecimal("0")} suffix="USDT" />
            <Pnl value={parseDecimal("0")} variant="percent" />
          </div>
          <div className="flex gap-6">
            <span className="w-16 text-muted-foreground">Tanımsız</span>
            <Pnl value={null} />
          </div>
        </div>
      </Section>

      <Section title="StatCard">
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard
            label="Toplam kâr"
            value={<Pnl value={parseDecimal("128.4")} suffix="USDT" />}
            subline="Son 30 gün"
          />
          <StatCard
            label="Aktif deal"
            value={<span>3</span>}
            subline="2 bot"
            chart={
              <svg viewBox="0 0 120 28" className="h-7 w-full" aria-hidden="true">
                <polyline
                  points="0,22 20,18 40,20 60,12 80,14 100,6 120,8"
                  fill="none"
                  stroke="var(--profit)"
                  strokeWidth="2"
                />
              </svg>
            }
          />
          <StatCard label="Bağlı sermaye" value={<Money value={parseDecimal("500")} suffix="USDT" />} />
        </div>
      </Section>

      <Section title="Rozetler">
        <div className="flex flex-wrap gap-2">
          <StatusBadge variant="live">live</StatusBadge>
          <StatusBadge variant="paper">paper</StatusBadge>
          <StatusBadge variant="testnet">testnet</StatusBadge>
          <StatusBadge variant="running">running</StatusBadge>
          <StatusBadge variant="paused">paused</StatusBadge>
          <StatusBadge variant="stopped">stopped</StatusBadge>
          <StatusBadge variant="error">error</StatusBadge>
          <StatusBadge variant="warn">warn</StatusBadge>
        </div>
      </Section>

      <Section title="TP ilerlemesi">
        <div className="flex max-w-md flex-col gap-3">
          <ProgressToTarget percent={parseDecimal("62")} label="TP'ye" />
          <ProgressToTarget percent={parseDecimal("0")} label="TP'ye" />
          <ProgressToTarget percent={parseDecimal("100")} label="TP'ye" />
          <ProgressToTarget percent={parseDecimal("150")} label="TP'ye" />
        </div>
      </Section>

      <Section title="ChartCard">
        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Portföy değeri"
            ranges={[
              { id: "7d", label: "7G" },
              { id: "30d", label: "30G" },
              { id: "all", label: "Tümü" },
            ]}
            activeRange={range}
            onRangeChange={setRange}
          >
            <svg viewBox="0 0 300 120" className="h-48 w-full" role="img" aria-label="Örnek alan grafiği">
              <path
                d="M0,100 L40,90 L80,94 L120,70 L160,76 L200,50 L240,56 L300,24 L300,120 L0,120 Z"
                fill="var(--accent)"
                opacity="0.18"
              />
              <path
                d="M0,100 L40,90 L80,94 L120,70 L160,76 L200,50 L240,56 L300,24"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="2"
              />
            </svg>
          </ChartCard>
          <ChartCard title="Yükleniyor" state="loading" />
          <ChartCard title="Hata" state="error" error="Grafik alınamadı." />
          <ChartCard title="Boş" state="empty" />
        </div>
      </Section>

      <Section title="DataTable">
        <DataTable
          columns={DEAL_COLUMNS}
          data={DEAL_ROWS}
          emptyTitle="Henüz deal yok"
          emptyDescription="İlk bot çalışmaya başlayınca deal'ler burada listelenecek."
          pageSize={10}
        />
      </Section>

      <Section title="DataTable (boş)">
        <DataTable
          columns={DEAL_COLUMNS}
          data={[]}
          emptyTitle="Henüz deal yok"
          emptyDescription="İlk bot çalışmaya başlayınca deal'ler burada listelenecek."
        />
      </Section>

      <Section title="EmptyState">
        <EmptyState
          title="İlk botunu kur"
          description="Bir parite seç, tutarı yaz, gerisini bot halletsin."
          actionLabel="Piyasaya göz at"
          actionHref="/market"
        />
      </Section>

      <Section title="ConfirmDialog">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setConfirmPlain(true)}
            className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            Yalın onay aç
          </button>
          <button
            type="button"
            onClick={() => setConfirmReason(true)}
            className="rounded-md border border-input bg-background px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            Gerekçeli onay aç
          </button>
          {confirmed === "" ? null : (
            <span className="text-sm text-muted-foreground">Onaylandı: {confirmed}</span>
          )}
        </div>
        <ConfirmDialog
          open={confirmPlain}
          onOpenChange={setConfirmPlain}
          title="Bot durdurulsun mu?"
          description="Çalışan bot durur, açık deal'ler olduğu gibi kalır. Bu işlem geri alınamaz."
          confirmLabel="Durdur"
          cancelLabel="Vazgeç"
          onConfirm={() => {
            setConfirmed("gerekçesiz");
            setConfirmPlain(false);
          }}
        />
        <ConfirmDialog
          open={confirmReason}
          onOpenChange={setConfirmReason}
          title="Kill switch açılsın mı?"
          description="Tüm işlemler durur. Bu işlem geri alınamaz."
          confirmLabel="Aç"
          cancelLabel="Vazgeç"
          reasonLabel="Gerekçe (isteğe bağlı)"
          reasonPlaceholder="Neden durduruyorsun?"
          onConfirm={(reason) => {
            setConfirmed(reason === undefined || reason === "" ? "gerekçesiz" : reason);
            setConfirmReason(false);
          }}
        />
      </Section>

      <Section title="Skeleton">
        <div className="flex max-w-md flex-col gap-2">
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-1/2" />
        </div>
      </Section>
    </div>
  );
}
