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
  if (!line.trim()) return null;
  if (line.startsWith('#### ')) {
    return <h4 key={index}>{renderInlineMarkdown(line.replace(/^####\s+/, ''))}</h4>;
  }
  if (line.startsWith('### ')) {
    return <h3 key={index}>{renderInlineMarkdown(line.replace(/^###\s+/, ''))}</h3>;
  }
  if (line.startsWith('## ')) {
    return <h2 key={index}>{renderInlineMarkdown(line.replace(/^##\s+/, ''))}</h2>;
  }
  if (/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)) {
    return <hr key={index} />;
  }
  if (line.startsWith('> ')) {
    return <blockquote key={index}>{renderInlineMarkdown(line.slice(2))}</blockquote>;
  }
  return <p key={index}>{renderInlineMarkdown(line)}</p>;
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

type ContentBlock =
  | { type: 'text'; lines: string[] }
  | { type: 'table'; lines: string[] };

function isTableLine(line: string) {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|');
}

function isTableSeparator(row: string[]) {
  return row.every((cell) => /^:?-{3,}:?$/.test(cell.replace(/\s/g, '')));
}

function parseTable(lines: string[]) {
  if (lines.length < 2) return null;
  const rows = lines.map((row) => row.split('|').slice(1, -1).map((cell) => cell.trim()));
  if (!isTableSeparator(rows[1])) return null;
  return [rows[0], ...rows.slice(2)];
}

function parseBlocks(lines: string[]): ContentBlock[] {
  const blocks: ContentBlock[] = [];
  let currentType: ContentBlock['type'] | null = null;
  let currentLines: string[] = [];

  const flush = () => {
    if (currentType && currentLines.length) blocks.push({ type: currentType, lines: currentLines });
    currentLines = [];
  };

  lines.forEach((line) => {
    const nextType: ContentBlock['type'] = isTableLine(line) ? 'table' : 'text';
    if (currentType !== nextType) {
      flush();
      currentType = nextType;
    }
    currentLines.push(line);
  });
  flush();
  return blocks;
}

function numericValue(cell: string) {
  const normalized = cell.replace(/,/g, '').replace(/%$/, '').trim();
  if (!normalized || !/^-?\d+(\.\d+)?$/.test(normalized)) return null;
  return Number(normalized);
}

function buildChartData(rows: string[][]): ChartData | null {
  if (rows.length < 2 || rows[0].length < 2) return null;

  const dataRows = rows.slice(1);
  const categoryColumnIndex = rows[0].findIndex((_, columnIndex) => (
    dataRows.every((row) => numericValue(row[columnIndex] || '') === null)
  ));
  const safeCategoryColumnIndex = categoryColumnIndex >= 0 ? categoryColumnIndex : 0;
  const series = rows[0].map((name, columnIndex) => {
    if (columnIndex === safeCategoryColumnIndex) return null;
    const values = dataRows.map((row) => numericValue(row[columnIndex] || ''));
    if (values.some((value) => value === null)) return null;
    return { name, values: values as number[] };
  }).filter((item): item is ChartData['series'][number] => item !== null);

  if (series.length === 0) return null;
  return {
    categories: dataRows.map((row) => row[safeCategoryColumnIndex] || ''),
    series,
  };
}

export function ResultRenderer({ content }: Props) {
  const blocks = parseBlocks(content.split('\n'));
  return (
    <div className="result-renderer">
      {blocks.map((block, index) => {
        if (block.type === 'table') {
          const rows = parseTable(block.lines);
          if (!rows) return <Fragment key={`table-text-${index}`}>{renderText(block.lines)}</Fragment>;
          const chartData = buildChartData(rows);
          return (
            <Fragment key={`table-${index}`}>
              <DataTable rows={rows} />
              {chartData && <EChartsPanel data={chartData} />}
            </Fragment>
          );
        }
        return <Fragment key={`text-${index}`}>{renderText(block.lines)}</Fragment>;
      })}
    </div>
  );
}
