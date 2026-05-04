import { useCallback, useEffect, useState } from "react";
import {
  deleteReport,
  fetchLatestReport,
  fetchReport,
  fetchReports,
  ReportContentResponse,
  ReportMeta
} from "../api/client";
import ReportReader from "../components/ReportReader";

interface ReportsPageProps {
  onOpenResearch?: () => void;
}

function formatSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  return `${(size / 1024).toFixed(1)} KB`;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function isMarkdownTableSeparator(line: string): boolean {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function parseMarkdownTable(lines: string[], startIndex: number): { html: string; nextIndex: number } | null {
  const header = lines[startIndex];
  const separator = lines[startIndex + 1];
  if (!header?.includes("|") || !separator || !isMarkdownTableSeparator(separator)) {
    return null;
  }

  const rows: string[][] = [];
  let index = startIndex;
  while (index < lines.length && lines[index].includes("|")) {
    if (!isMarkdownTableSeparator(lines[index])) {
      rows.push(
        lines[index]
          .trim()
          .replace(/^\|/, "")
          .replace(/\|$/, "")
          .split("|")
          .map((cell) => escapeHtml(cell.trim()))
      );
    }
    index += 1;
  }

  if (!rows.length) {
    return null;
  }

  const [head, ...body] = rows;
  const headHtml = `<thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead>`;
  const bodyHtml = `<tbody>${body
    .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
    .join("")}</tbody>`;

  return {
    html: `<div class="table-wrap"><table>${headHtml}${bodyHtml}</table></div>`,
    nextIndex: index
  };
}

function markdownToPrintableHtml(markdown: string): string {
  const lines = markdown.split(/\r?\n/);
  const blocks: string[] = [];
  let paragraph: string[] = [];

  const flushParagraph = () => {
    if (!paragraph.length) {
      return;
    }
    blocks.push(`<p>${paragraph.map(escapeHtml).join("<br />")}</p>`);
    paragraph = [];
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.trim();
    const table = parseMarkdownTable(lines, index);

    if (table) {
      flushParagraph();
      blocks.push(table.html);
      index = table.nextIndex - 1;
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      const level = Math.min(heading[1].length, 3);
      blocks.push(`<h${level}>${escapeHtml(heading[2])}</h${level}>`);
      continue;
    }

    const image = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (image) {
      flushParagraph();
      blocks.push(
        `<figure><img src="${escapeHtml(image[2].trim())}" alt="${escapeHtml(
          image[1].trim()
        )}" /><figcaption>${escapeHtml(image[1].trim())}</figcaption></figure>`
      );
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      flushParagraph();
      const items: string[] = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(`<li>${escapeHtml(lines[index].trim().replace(/^[-*]\s+/, ""))}</li>`);
        index += 1;
      }
      index -= 1;
      blocks.push(`<ul>${items.join("")}</ul>`);
      continue;
    }

    paragraph.push(line);
  }

  flushParagraph();
  return blocks.join("\n");
}

function printReportAsPdf(report: ReportContentResponse): boolean {
  const popup = window.open("", "_blank", "width=1080,height=820");
  if (!popup) {
    return false;
  }

  const body = markdownToPrintableHtml(report.content);
  popup.document.write(`<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(report.title)}</title>
  <style>
    @page { margin: 18mm; }
    body {
      margin: 0;
      color: #1f1a17;
      background: #fffaf3;
      font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
      line-height: 1.72;
    }
    main {
      max-width: 980px;
      margin: 0 auto;
      padding: 32px;
      background: #fffdf8;
    }
    .meta {
      margin: 6px 0 24px;
      color: #74685c;
      font-size: 12px;
    }
    h1, h2, h3 {
      color: #1f1a17;
      line-height: 1.35;
      page-break-after: avoid;
    }
    h1 { font-size: 28px; margin: 0 0 8px; }
    h2 { font-size: 20px; margin: 28px 0 12px; border-bottom: 1px solid #eadfce; padding-bottom: 8px; }
    h3 { font-size: 16px; margin: 22px 0 10px; }
    p { margin: 10px 0; white-space: pre-wrap; }
    ul { margin: 10px 0 10px 22px; padding: 0; }
    .table-wrap {
      margin: 16px 0 22px;
      max-width: 100%;
      overflow-x: auto;
      page-break-inside: avoid;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      background: #fff;
    }
    th, td {
      border: 1px solid #eadfce;
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
    }
    th {
      background: #f7efe4;
      color: #4d3a2a;
      font-weight: 700;
      white-space: nowrap;
      word-break: keep-all;
    }
    td {
      max-width: 260px;
    }
    figure {
      margin: 18px 0 24px;
      padding: 10px;
      border: 1px solid #eadfce;
      border-radius: 10px;
      background: #fff;
      page-break-inside: avoid;
    }
    figure img {
      display: block;
      width: 100%;
      height: auto;
      border-radius: 8px;
    }
    figcaption {
      margin-top: 8px;
      color: #74685c;
      font-size: 12px;
      text-align: center;
    }
    @media print {
      body { background: #fff; }
      main { padding: 0; background: #fff; }
      .no-print { display: none; }
    }
  </style>
</head>
<body>
  <main>
    <h1>${escapeHtml(report.title)}</h1>
    <div class="meta">${escapeHtml(report.filename)} · ${escapeHtml(
      new Date(report.updated_at).toLocaleString()
    )} · ${formatSize(report.size_bytes)}</div>
    ${body}
  </main>
  <script>
    window.addEventListener("load", function () {
      window.focus();
      window.print();
    });
  </script>
</body>
</html>`);
  popup.document.close();
  return true;
}

function ReportsPage({ onOpenResearch }: ReportsPageProps) {
  const [reports, setReports] = useState<ReportMeta[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [selected, setSelected] = useState<ReportContentResponse | null>(null);
  const [listLoading, setListLoading] = useState(false);
  const [readerLoading, setReaderLoading] = useState(false);
  const [deletingFilename, setDeletingFilename] = useState<string | null>(null);
  const [exportingFilename, setExportingFilename] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [readerError, setReaderError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadReports = useCallback(async () => {
    setListLoading(true);
    setError(null);
    try {
      const response = await fetchReports();
      setReports(response.reports);
      setWarnings(response.warnings);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "报告列表接口暂时不可用。");
    } finally {
      setListLoading(false);
    }
  }, []);

  const openReport = useCallback(async (filename: string) => {
    setReaderLoading(true);
    setReaderError(null);
    setNotice(null);
    try {
      setSelected(await fetchReport(filename));
    } catch (exc) {
      setReaderError(exc instanceof Error ? exc.message : "报告内容读取失败。");
    } finally {
      setReaderLoading(false);
    }
  }, []);

  const openLatestReport = useCallback(async () => {
    setReaderLoading(true);
    setReaderError(null);
    setNotice(null);
    try {
      setSelected(await fetchLatestReport());
    } catch (exc) {
      setReaderError(exc instanceof Error ? exc.message : "最新报告读取失败。");
    } finally {
      setReaderLoading(false);
    }
  }, []);

  const handleDelete = useCallback(
    async (report: ReportMeta) => {
      const confirmed = window.confirm(`确认删除报告“${report.title}”？\n\n文件：${report.filename}\n删除后无法从报告库恢复。`);
      if (!confirmed) {
        return;
      }

      setDeletingFilename(report.filename);
      setError(null);
      setNotice(null);
      try {
        await deleteReport(report.filename);
        if (selected?.filename === report.filename) {
          setSelected(null);
        }
        setNotice(`已删除报告：${report.title}`);
        await loadReports();
      } catch (exc) {
        setError(exc instanceof Error ? exc.message : "删除报告失败。");
      } finally {
        setDeletingFilename(null);
      }
    },
    [loadReports, selected?.filename]
  );

  const handleExportPdf = useCallback(async (report: ReportMeta | ReportContentResponse) => {
    setExportingFilename(report.filename);
    setError(null);
    setNotice(null);
    try {
      const fullReport = "content" in report ? report : await fetchReport(report.filename);
      const opened = printReportAsPdf(fullReport);
      if (!opened) {
        setError("浏览器阻止了打印窗口，请允许弹窗后重试。");
        return;
      }
      setNotice("已打开打印窗口，请在系统打印对话框中选择“另存为 PDF”并选择保存位置。");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "导出 PDF 失败。");
    } finally {
      setExportingFilename(null);
    }
  }, []);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  return (
    <div className="w-full min-w-0 max-w-full overflow-x-hidden space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-medium text-brand">Reports</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">报告库</h1>
          <p className="mt-3 text-sm leading-7 text-muted">
            管理本地 data/reports 目录中的 Markdown 研究报告，支持阅读、删除和导出 PDF。
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button className="secondary-button" onClick={openLatestReport} disabled={readerLoading}>
            查看最新报告
          </button>
          <button className="secondary-button" onClick={loadReports} disabled={listLoading}>
            {listLoading ? "刷新中..." : "刷新列表"}
          </button>
          {selected ? (
            <button
              className="primary-button"
              onClick={() => void handleExportPdf(selected)}
              disabled={exportingFilename === selected.filename}
            >
              {exportingFilename === selected.filename ? "准备导出..." : "导出当前报告 PDF"}
            </button>
          ) : null}
        </div>
      </div>

      {notice ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {notice}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </div>
      ) : null}

      {warnings.length ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {reports.length === 0 && !listLoading ? (
        <div className="rounded-lg border border-dashed border-line bg-panel p-8 text-center text-sm text-muted">
          <p>还没有生成报告。你可以前往研究生成页面生成第一份报告。</p>
          {onOpenResearch ? (
            <button className="primary-button mt-4" onClick={onOpenResearch}>
              前往研究生成
            </button>
          ) : null}
        </div>
      ) : (
        <div className="grid min-w-0 max-w-full gap-5 lg:grid-cols-[minmax(300px,380px)_minmax(0,1fr)]">
          <section className="min-w-0 rounded-lg border border-line bg-panel shadow-soft">
            <div className="border-b border-line px-4 py-3 text-sm font-semibold text-ink">
              本地报告
            </div>
            <div className="max-h-[72vh] divide-y divide-line overflow-auto">
              {reports.map((report, index) => {
                const isSelected = selected?.filename === report.filename;
                const isDeleting = deletingFilename === report.filename;
                const isExporting = exportingFilename === report.filename;

                return (
                  <article
                    key={report.filename}
                    className={`px-4 py-4 transition hover:bg-[#f8efe4] ${
                      isSelected ? "bg-[#fff4e6]" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <button
                        className="min-w-0 flex-1 text-left"
                        onClick={() => void openReport(report.filename)}
                      >
                        <p className="text-sm font-semibold leading-6 text-ink">{report.title}</p>
                        <p className="mt-1 break-all text-xs leading-5 text-muted">{report.filename}</p>
                      </button>
                      {index === 0 ? (
                        <span className="shrink-0 rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800">
                          最新报告
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-xs text-muted">
                      {new Date(report.updated_at).toLocaleString()} · {formatSize(report.size_bytes)}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        className="secondary-button px-3 py-1.5 text-xs"
                        onClick={() => void openReport(report.filename)}
                      >
                        阅读
                      </button>
                      <button
                        className="secondary-button px-3 py-1.5 text-xs"
                        onClick={() => void handleExportPdf(report)}
                        disabled={isExporting}
                      >
                        {isExporting ? "准备中..." : "导出 PDF"}
                      </button>
                      <button
                        className="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-medium text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => void handleDelete(report)}
                        disabled={isDeleting}
                      >
                        {isDeleting ? "删除中..." : "删除"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
          <ReportReader report={selected} loading={readerLoading} error={readerError} />
        </div>
      )}
    </div>
  );
}

export default ReportsPage;
