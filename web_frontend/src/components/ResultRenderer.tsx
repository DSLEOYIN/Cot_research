import { DataTable } from './DataTable';
import { ChartData, EChartsPanel } from './EChartsPanel';

type Props = {
  content: string;
};

function renderLine(line: string, index: number) {
  if (line.startsWith('### ')) {
    return <h3 key={index}>{line.replace(/^###\s+/, '')}</h3>;
  }
  if (line.startsWith('> ')) {
    return <blockquote key={index}>{line.slice(2)}</blockquote>;
  }
  return <p key={index}>{line || '\u00a0'}</p>;
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
    const displayRows = [table[0], ...table.slice(2)];
    const chartData = buildChartData(displayRows);
    return (
      <div className="result-renderer">
        {textLines.map(renderLine)}
        <DataTable rows={displayRows} />
        {chartData && <EChartsPanel data={chartData} />}
      </div>
    );
  }
  return <div className="result-renderer">{lines.map(renderLine)}</div>;
}
