import { Fragment, ReactNode, useState } from 'react';

type Props = {
  rows: string[][];
};

function stripInlineMarkdown(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/`([^`]+)`/g, '$1');
}

function normalizeCellText(text: string) {
  return stripInlineMarkdown(text).replace(/<br\s*\/?>/gi, '\n');
}

function renderCellContent(text: string): ReactNode[] {
  const parts = text.split(/<br\s*\/?>/gi);
  return parts.map((part, index) => (
    <Fragment key={`${index}-${part}`}>
      {stripInlineMarkdown(part)}
      {index < parts.length - 1 && <br key={`break-${index}`} />}
    </Fragment>
  ));
}

export function DataTable({ rows }: Props) {
  const [copied, setCopied] = useState(false);
  if (rows.length === 0) return null;

  async function copyTable() {
    const tsv = rows
      .map((row) => row.map((cell) => normalizeCellText(cell).replace(/[\t\r\n]+/g, ' ').trim()).join('\t'))
      .join('\n');
    try {
      await navigator.clipboard.writeText(tsv);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = tsv;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      textarea.remove();
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="data-table-wrap">
      <div className="data-table-toolbar">
        <button className="data-table-copy" type="button" onClick={copyTable}>
          {copied ? '已复制，可粘贴到 Excel' : '复制表格'}
        </button>
      </div>
      <table className="data-table">
        <thead><tr>{rows[0].map((cell) => <th key={cell}>{renderCellContent(cell)}</th>)}</tr></thead>
        <tbody>
          {rows.slice(1).map((row, rowIndex) => (
            <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`}>{renderCellContent(cell)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
