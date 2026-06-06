type Props = {
  rows: string[][];
};

export function DataTable({ rows }: Props) {
  if (rows.length === 0) return null;
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead><tr>{rows[0].map((cell) => <th key={cell}>{cell}</th>)}</tr></thead>
        <tbody>
          {rows.slice(1).map((row, rowIndex) => (
            <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={`${rowIndex}-${cellIndex}`}>{cell}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
