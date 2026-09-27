"use client";

import {
  createPaginatedRowModel,
  createSortedRowModel,
  rowPaginationFeature,
  rowSortingFeature,
  tableFeatures,
  useTable,
  type ColumnDef,
  type RowData,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { EmptyState } from "@/components/empty-state";
import { cn } from "@/lib/utils";

const features = tableFeatures({
  rowSortingFeature,
  sortedRowModel: createSortedRowModel(),
  rowPaginationFeature,
  paginatedRowModel: createPaginatedRowModel(),
});

export type TableColumn<TData extends RowData> = ColumnDef<
  typeof features,
  TData
>;

export function DataTable<TData extends RowData>({
  columns,
  data,
  emptyTitle,
  emptyDescription,
  pageSize = 10,
  paginationLabels,
  onRowClick,
}: {
  columns: TableColumn<TData>[];
  data: TData[];
  emptyTitle: string;
  emptyDescription?: string;
  pageSize?: number;
  paginationLabels?: { previous: string; next: string; of: string };
  /** Satır tıklaması (klavye erişimi için hücrede ayrıca bağlantı gerekir). */
  onRowClick?: (row: TData) => void;
}) {
  const table = useTable({
    features,
    columns,
    data,
    initialState: { pagination: { pageIndex: 0, pageSize } },
  });

  if (data.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  const labels = paginationLabels ?? {
    previous: "Önceki",
    next: "Sonraki",
    of: "/",
  };
  const pageCount = table.getPageCount();
  const pageIndex = table.state.pagination.pageIndex;

  function sortIcon(columnId: string) {
    const direction = table.getColumn(columnId)?.getIsSorted();
    if (direction === "asc")
      return <ArrowUp className="size-3" aria-hidden="true" />;
    if (direction === "desc")
      return <ArrowDown className="size-3" aria-hidden="true" />;
    return <ChevronsUpDown className="size-3 opacity-50" aria-hidden="true" />;
  }

  const clickable = onRowClick !== undefined;
  function handleRowClick(row: TData) {
    onRowClick?.(row);
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Masaüstü: tablo. */}
      <div className="hidden overflow-x-auto rounded-lg border border-border md:block">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((group) => (
              <tr key={group.id} className="border-b border-border bg-muted/50">
                {group.headers.map((header) => (
                  <th
                    key={header.id}
                    scope="col"
                    className="px-3 py-2 text-left font-medium text-muted-foreground"
                  >
                    {header.column.getCanSort() ? (
                      <button
                        type="button"
                        onClick={header.column.getToggleSortingHandler()}
                        className="inline-flex items-center gap-1 hover:text-foreground"
                      >
                        <table.FlexRender header={header} />
                        {sortIcon(header.column.id)}
                      </button>
                    ) : (
                      <table.FlexRender header={header} />
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={clickable ? () => handleRowClick(row.original) : undefined}
                className={cn(
                  "border-b border-border last:border-0 hover:bg-muted/30",
                  clickable && "cursor-pointer",
                )}
              >
                {row.getAllCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2">
                    <table.FlexRender cell={cell} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobil: kart listesi (aynı sayfa, aynı sıralama). */}
      <ol className="flex flex-col gap-2 md:hidden">
        {table.getRowModel().rows.map((row) => (
          <li
            key={row.id}
            onClick={clickable ? () => handleRowClick(row.original) : undefined}
            className={cn(
              "flex flex-col gap-1 rounded-lg border border-border p-3",
              clickable && "cursor-pointer",
            )}
          >
            {row.getAllCells().map((cell) => (
              <div key={cell.id} className="flex justify-between gap-4 text-sm">
                <span className="text-muted-foreground">
                  {typeof cell.column.columnDef.header === "string"
                    ? cell.column.columnDef.header
                    : cell.column.id}
                </span>
                <span className="text-right">
                  <table.FlexRender cell={cell} />
                </span>
              </div>
            ))}
          </li>
        ))}
      </ol>

      {pageCount <= 1 ? null : (
        <nav
          aria-label="Sayfalama"
          className="flex items-center justify-end gap-2 text-sm"
        >
          <button
            type="button"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className={cn(
              "rounded-md border border-input px-3 py-1.5",
              table.getCanPreviousPage() ? "hover:bg-muted" : "opacity-50",
            )}
          >
            {labels.previous}
          </button>
          <span className="font-mono text-muted-foreground">
            {pageIndex + 1} {labels.of} {pageCount}
          </span>
          <button
            type="button"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className={cn(
              "rounded-md border border-input px-3 py-1.5",
              table.getCanNextPage() ? "hover:bg-muted" : "opacity-50",
            )}
          >
            {labels.next}
          </button>
        </nav>
      )}
    </div>
  );
}
