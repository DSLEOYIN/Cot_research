import { Fragment, ReactNode } from 'react';
import { DataTable } from './DataTable';
import { ChartData, EChartsPanel } from './EChartsPanel';

type Props = {
  content: string;
};

function renderInlineMarkdown(text: string): ReactNode[] {
  const parts = text.split('**');
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return <strong key={index}>{part}</strong>;
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}

function renderLine(line: string, index: number) {
  if (line.startsWith('### ')) {
    return <h3 key={index}>{renderInlineMarkdown(line.replace(/^###\s+/, ''))}</h3>;
  }
  if (line.startsWith('## ')) {
    return <h2 key={index}>{renderInlineMarkdown(line.replace(/^##\s+/, ''))}</h2>;
  }
  if (line.startsWith('> ')) {
    return <blockquote key={index}>{renderInlineMarkdown(line.slice(2))}</blockquote>;
  }
  return <p key={index}>{line ? renderInlineMarkdown(line) : '\u00a0'}</p>;
}

function renderText(lines: string[]) {
  const nodes: ReactNode[] = [];
  let orderedItems: string[] = [];
  let orderedStart = 1;
  let unorderedItems: string[] = [];

  const flushOrdered = () => {
    if (!orderedItems.length) return;
    nodes.push(
      <ol key={`ol-${nodes.length}`} start={orderedStart}>
        {orderedItems.map((item, index) => <li key={index}>{renderInlineMarkdown(item)}</li>)}
      </ol>,
    );
    orderedItems = [];
    orderedStart = 1;
  };
  const flushUnordered = () => {
    if (!unorderedItems.length) return;
    nodes.push(
      <ul key={`ul-${nodes.length}`}>
        {unorderedItems.map((item, index) => <li key={index}>{renderInlineMarkdown(item)}</li>)}
      </ul>,
    );
    unorderedItems = [];
  };

  lines.forEach((line, index) => {
    const ordered = line.match(/^\s*(\d+)[.、]\s*(.+)$/);
    const unordered = line.match(/^\s*[-*]\s+(.+)$/);
    if (ordered) {
      flushUnordered();
      if (!orderedItems.length) orderedStart = Number(ordered[1]);
      orderedItems.push(ordered[2]);
      return;
    }
    if (unordered) {
      flushOrdered();
      unorderedItems.push(unordered[1]);
      return;
    }
    flushOrdered();
    flushUnordered();
    nodes.push(renderLine(line, index));
  });
  flushOrdered();
  flushUnordered();
  return nodes;
}

function parseTable(lines: string[]) {
  const rows = lines.filter((line) => line.trim().startsWith('|') && line.trim().endsWith('|'));
  if (rows.length < 2) return null;
  return rows.map((row) => row.split('|').slice(1, -1).map((cell) => cell.trim()));
}

function numericValue(cell: string) {
  const normalized = cell.replace(/,/g, '').replace(/%$/, '').trim();
  if (!normalized || !/^-?\d+(\.\d+)?$/.test(normalized)) return null;
  return Number(normalized);
}

function buildChartData(rows: string[][]): ChartData | null {
  if (rows.length < 2 || rows[0].length < 2) return null;

  const dataRows = rows.slice(1);
  const series = rows[0].slice(1).map((name, columnIndex) => {
    const values = dataRows.map((row) => numericValue(row[columnIndex + 1] || ''));
    if (values.some((value) => value === null)) return null;
    return { name, values: values as number[] };
  }).filter((item): item is ChartData['series'][number] => item !== null);

  if (series.length === 0) return null;
  return {
    categories: dataRows.map((row) => row[0] || ''),
    series,
  };
}

export function ResultRenderer({ content }: Props) {
  const lines = content.split('\n');
  const table = parseTable(lines);
  if (table) {
    const tableLines = new Set(lines.filter((line) => line.trim().startsWith('|') && line.trim().endsWith('|')));
    const textLines = lines.filter((line) => !tableLines.has(line) && !/^\|\s*-/.test(line));
    const dataHeadingIndex = textLines.findIndex((line) => line.includes('数据查询结果') || line.includes('同环比计算数据'));
    const leadingTextLines = dataHeadingIndex >= 0 ? textLines.slice(0, dataHeadingIndex + 1) : [];
    const remainingTextLines = dataHeadingIndex >= 0 ? textLines.slice(dataHeadingIndex + 1) : textLines;
    const displayRows = [table[0], ...table.slice(2)];
    const chartData = buildChartData(displayRows);
    return (
      <div className="result-renderer">
        {renderText(leadingTextLines)}
        <DataTable rows={displayRows} />
        {chartData && <EChartsPanel data={chartData} />}
        {renderText(remainingTextLines)}
      </div>
    );
  }
  return <div className="result-renderer">{renderText(lines)}</div>;
}
