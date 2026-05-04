import { ReactNode } from "react";

interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  emptyText?: string;
}

function DataTable<T>({ rows, columns, emptyText = "暂无数据" }: DataTableProps<T>) {
  if (!rows.length) {
    return <div className="rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">{emptyText}</div>;
  }

  return (
    <div className="overflow-auto rounded-lg border border-line bg-panel">
      <table className="min-w-full divide-y divide-line text-sm">
        <thead className="bg-[#f8efe4] text-xs text-muted">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className="whitespace-nowrap px-3 py-2 text-left font-semibold">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row, index) => (
            <tr key={index} className="hover:bg-[#fff8ee]">
              {columns.map((column) => (
                <td key={column.key} className="whitespace-nowrap px-3 py-2 text-ink">
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
