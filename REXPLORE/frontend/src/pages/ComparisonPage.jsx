import { useEffect, useState } from 'react'
import Header from '../components/Header'
import PaperComparisonTable from '../components/PaperComparison'
import api from '../api'

export default function ComparisonPage({ onOpenSidebar }) {
  const [papers, setPapers] = useState([])
  const [selected, setSelected] = useState([])
  const [rows, setRows] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listPapers().then((r) => setPapers(r.data.filter((p) => p.status === 'ready')))
  }, [])

  const toggle = (id) => {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  }

  const compare = async () => {
    if (selected.length < 2) return
    setLoading(true)
    try {
      const res = await api.comparePapers(selected)
      setRows(res.data.comparison)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Header title="Paper Comparison" subtitle="Compare multiple analyzed papers side by side" onOpenSidebar={onOpenSidebar} />
      <div className="app-content">
        {papers.length < 2 ? (
          <div className="state-block">
            <h3>Not enough analyzed papers yet</h3>
            <p>Upload and fully process at least two papers to compare them.</p>
          </div>
        ) : (
          <>
            <div className="paper-picker">
              {papers.map((p) => (
                <button
                  key={p.id}
                  className={`paper-picker-chip ${selected.includes(p.id) ? 'selected' : ''}`}
                  onClick={() => toggle(p.id)}
                >
                  {p.title || p.original_filename}
                </button>
              ))}
            </div>
            <button className="btn btn-primary" onClick={compare} disabled={selected.length < 2 || loading} style={{ marginBottom: 24 }}>
              {loading ? 'Comparing…' : `Compare ${selected.length} Papers`}
            </button>
            {rows && <PaperComparisonTable rows={rows} />}
          </>
        )}
      </div>
    </div>
  )
}
