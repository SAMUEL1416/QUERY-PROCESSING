import { useState } from 'react'
import { Plus, Trash2, Download, FlaskConical } from 'lucide-react'
import api from '../api'

const COLUMN_TYPES = ['integer', 'float', 'category', 'boolean', 'date', 'text']

export default function SyntheticGenerator({ dataset, onGenerated }) {
  const [rowCount, setRowCount] = useState(100)
  const [seed, setSeed] = useState(42)
  const [columns, setColumns] = useState([{ name: 'id', type: 'integer', categories: '' }])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const addColumn = () => setColumns((c) => [...c, { name: '', type: 'integer', categories: '' }])
  const removeColumn = (idx) => setColumns((c) => c.filter((_, i) => i !== idx))
  const updateColumn = (idx, patch) => setColumns((c) => c.map((col, i) => (i === idx ? { ...col, ...patch } : col)))

  const generate = async () => {
    setError(null)
    setLoading(true)
    try {
      const payload = {
        row_count: Number(rowCount),
        seed: Number(seed),
        columns: columns.map((c) => ({
          name: c.name,
          type: c.type,
          categories: c.type === 'category' ? c.categories.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
        })),
      }
      const res = await api.createSyntheticDataset(dataset.id, payload)
      setResult(res.data)
      onGenerated?.(res.data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to generate synthetic dataset.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="synthetic-form">
      <div className="synthetic-banner">SYNTHETIC DATASET — NOT THE ORIGINAL RESEARCH DATA (last resort only)</div>

      <div className="column-spec-row" style={{ gridTemplateColumns: '1fr 1fr 90px' }}>
        <div className="form-row">
          <label>Number of Rows</label>
          <input type="number" min={1} max={100000} value={rowCount} onChange={(e) => setRowCount(e.target.value)} />
        </div>
        <div className="form-row">
          <label>Random Seed</label>
          <input type="number" value={seed} onChange={(e) => setSeed(e.target.value)} />
        </div>
      </div>

      <div>
        <span className="section-block-label">Columns</span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {columns.map((col, idx) => (
            <div className="column-spec-row" key={idx}>
              <div className="form-row">
                <label>Name</label>
                <input value={col.name} onChange={(e) => updateColumn(idx, { name: e.target.value })} placeholder="column_name" />
              </div>
              <div className="form-row">
                <label>Type</label>
                <select value={col.type} onChange={(e) => updateColumn(idx, { type: e.target.value })}>
                  {COLUMN_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Categories (if category)</label>
                <input value={col.categories} onChange={(e) => updateColumn(idx, { categories: e.target.value })} placeholder="a, b, c" />
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => removeColumn(idx)}><Trash2 size={14} /></button>
            </div>
          ))}
        </div>
        <button className="btn btn-secondary btn-sm" style={{ marginTop: 10 }} onClick={addColumn}>
          <Plus size={14} /> Add Column
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <button className="btn btn-primary" onClick={generate} disabled={loading || columns.length === 0}>
        <FlaskConical size={16} /> {loading ? 'Generating…' : 'Generate Synthetic Dataset'}
      </button>

      {result && (
        <div>
          <span className="section-block-label">CSV Preview (first rows)</span>
          <div className="table-scroll">
            <table className="csv-preview-table">
              <thead>
                <tr>{Object.keys(result.preview[0] || {}).map((k) => <th key={k}>{k}</th>)}</tr>
              </thead>
              <tbody>
                {result.preview.map((row, i) => (
                  <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{String(v)}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="btn btn-secondary btn-sm" style={{ marginTop: 12 }} onClick={() => api.downloadSyntheticDataset(result.id)}>
            <Download size={14} /> Download CSV
          </button>
        </div>
      )}
    </div>
  )
}
