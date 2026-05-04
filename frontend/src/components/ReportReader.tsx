import { ReportContentResponse } from "../api/client";

interface ReportReaderProps {
  report: ReportContentResponse | null;
  loading: boolean;
  error: string | null;
}

type MarkdownBlock =
  | { type: "heading"; level: number; text: string }
  | { type: "image"; alt: string; src: string }
  | { type: "paragraph"; text: string }
  | { type: "list"; items: string[] }
  | { type: "table"; headers: string[]; rows: string[][] };

function splitTableRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isTableSeparator(line: string): boolean {
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.replace(/\s/g, "")));
}

function isTableLine(line: string): boolean {
  return line.trim().startsWith("|") && line.trim().endsWith("|");
}

function parseMarkdown(content: string): MarkdownBlock[] {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      blocks.push({ type: "heading", level: heading[1].length, text: heading[2].trim() });
      index += 1;
      continue;
    }

    const image = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (image) {
      blocks.push({ type: "image", alt: image[1].trim(), src: image[2].trim() });
      index += 1;
      continue;
    }

    if (isTableLine(trimmed) && lines[index + 1] && isTableSeparator(lines[index + 1])) {
      const headers = splitTableRow(trimmed);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && isTableLine(lines[index])) {
        rows.push(splitTableRow(lines[index]));
        index += 1;
      }
      blocks.push({ type: "table", headers, rows });
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*]\s+/, ""));
        index += 1;
      }
      blocks.push({ type: "list", items });
      continue;
    }

    const paragraph: string[] = [];
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^(#{1,4})\s+/.test(lines[index].trim()) &&
      !/^!\[[^\]]*\]\([^)]+\)$/.test(lines[index].trim()) &&
      !(isTableLine(lines[index].trim()) && lines[index + 1] && isTableSeparator(lines[index + 1])) &&
      !/^[-*]\s+/.test(lines[index].trim())
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    blocks.push({ type: "paragraph", text: paragraph.join(" ") });
  }

  return blocks;
}

function renderBlock(block: MarkdownBlock, index: number) {
  if (block.type === "heading") {
    const baseClass = "font-semibold text-ink";
    if (block.level === 1) return <h1 key={index} className={`${baseClass} mt-1 text-2xl`}>{block.text}</h1>;
    if (block.level === 2) return <h2 key={index} className={`${baseClass} mt-7 border-b border-line pb-2 text-lg`}>{block.text}</h2>;
    return <h3 key={index} className={`${baseClass} mt-5 text-base`}>{block.text}</h3>;
  }

  if (block.type === "table") {
    return (
      <div key={index} className="mt-4 max-w-full overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-max border-collapse text-left text-sm">
          <thead className="bg-[#fff4e4] text-ink">
            <tr>
              {block.headers.map((header, cellIndex) => (
                <th key={`${header}-${cellIndex}`} className="whitespace-nowrap border-b border-line px-3 py-2 text-left font-semibold">
                  {header || "-"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="odd:bg-white even:bg-[#fffaf2]">
                {block.headers.map((_, cellIndex) => (
                  <td key={cellIndex} className="max-w-[360px] min-w-[96px] border-b border-line/70 px-3 py-2 align-top text-muted">
                    {row[cellIndex] || "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (block.type === "image") {
    return (
      <figure key={index} className="mt-5 max-w-full overflow-hidden rounded-lg border border-line bg-white p-3">
        <img src={block.src} alt={block.alt} className="h-auto max-w-full rounded-md" loading="lazy" />
        {block.alt ? <figcaption className="mt-2 text-xs text-muted">{block.alt}</figcaption> : null}
      </figure>
    );
  }

  if (block.type === "list") {
    return (
      <ul key={index} className="mt-3 list-disc space-y-2 pl-5 text-sm leading-7 text-muted">
        {block.items.map((item, itemIndex) => (
          <li key={itemIndex}>{item}</li>
        ))}
      </ul>
    );
  }

  return (
    <p key={index} className="mt-3 whitespace-pre-wrap text-sm leading-7 text-muted">
      {block.text}
    </p>
  );
}

function ReportReader({ report, loading, error }: ReportReaderProps) {
  if (loading) {
    return (
      <section className="min-w-0 rounded-lg border border-line bg-panel p-6 shadow-soft">
        <p className="text-sm text-muted">正在读取报告...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="min-w-0 rounded-lg border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        {error}
      </section>
    );
  }

  if (!report) {
    return (
      <section className="min-w-0 rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">
        选择报告后在这里阅读正文。
      </section>
    );
  }

  const blocks = parseMarkdown(report.content);

  return (
    <article className="min-w-0 max-w-full overflow-hidden rounded-lg border border-line bg-panel p-6 shadow-soft">
      <div className="border-b border-line pb-4">
        <h2 className="text-xl font-semibold text-ink">{report.title}</h2>
        <p className="mt-2 text-xs text-muted">
          {report.filename} · {new Date(report.updated_at).toLocaleString()} · {report.size_bytes.toLocaleString()} bytes
        </p>
      </div>
      <div className="mt-5 max-h-[76vh] max-w-full overflow-auto rounded-md bg-[#fffdf8] p-4">
        {blocks.map(renderBlock)}
      </div>
    </article>
  );
}

export default ReportReader;
