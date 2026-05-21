import { ReactNode } from "react";

interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

interface Props<T> {
  rows: T[];
  columns: Column<T>[];
  emptyText?: string;
}

export default function DataTable<T>({ rows, columns, emptyText = "暂无数据" }: Props<T>) {
  if (!rows.length) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--border-card)] bg-[var(--bg-card)] p-8 text-center text-sm text-[var(--ink-muted)]">
        {emptyText}
      </div>
    );
  }

  return (
    <div className="overflow-auto rounded-xl border border-[var(--border-card)]">
      <table className="fin-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col.key}>{col.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
