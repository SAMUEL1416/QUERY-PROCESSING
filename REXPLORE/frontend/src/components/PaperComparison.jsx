const DIMENSIONS = [
  'Problem', 'Research Gap', 'Objective', 'Methodology',
  'Algorithms', 'Datasets', 'Metrics', 'Results', 'Limitations', 'Future Work',
]

export default function PaperComparison({ rows }) {
  if (!rows || rows.length === 0) return null

  return (
    <div className="card comparison-table-wrap">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Dimension</th>
            {rows.map((r) => <th key={r.paper_id}>{r.title || r.error}</th>)}
          </tr>
        </thead>
        <tbody>
          {DIMENSIONS.map((dim) => (
            <tr key={dim}>
              <td className="dimension-label">{dim}</td>
              {rows.map((r) => <td key={r.paper_id}>{r.error ? '—' : r[dim]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
