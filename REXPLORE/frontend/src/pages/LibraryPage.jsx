import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, Link } from 'react-router-dom'
import { FileText, Layers, Clock, UploadCloud } from 'lucide-react'
import Header from '../components/Header'
import api from '../api'

const STATUS_BADGE = {
  ready: 'badge-success',
  processing: 'badge-info',
  uploading: 'badge-info',
  error: 'badge-danger',
}

export default function LibraryPage({ onOpenSidebar }) {
  const [papers, setPapers] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    // Poll while any paper is still processing so status badges update live;
    // stop once everything is in a terminal state (ready/error) instead of
    // polling GET /api/papers forever for the whole time this page stays
    // open. Re-opening the page (or uploading a new paper, which navigates
    // here) re-mounts this effect and resumes polling as needed.
    let cancelled = false
    let interval = null

    const hasActivePaper = (list) => list.some((p) => p.status !== 'ready' && p.status !== 'error')

    const load = () =>
      api.listPapers().then((r) => {
        if (cancelled) return
        setPapers(r.data)
        if (interval && !hasActivePaper(r.data)) {
          clearInterval(interval)
          interval = null
        }
      }).catch(() => { if (!cancelled) setPapers([]) })

    load()
    interval = setInterval(load, 4000)

    return () => {
      cancelled = true
      if (interval) clearInterval(interval)
    }
  }, [])

  return (
    <div>
      <Header
        title="Research Library"
        subtitle="All papers you've uploaded and analyzed"
        onOpenSidebar={onOpenSidebar}
        actions={<Link to="/upload" className="btn btn-primary"><UploadCloud size={16} /> Upload Paper</Link>}
      />
      <div className="app-content">
        {!papers && (
          <div className="paper-grid">
            {[0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 140, borderRadius: 16 }} />)}
          </div>
        )}

        {papers && papers.length === 0 && (
          <div className="state-block">
            <div className="state-block-icon"><FileText size={24} /></div>
            <h3>No papers yet</h3>
            <p>Upload your first research paper to start extracting structured knowledge from it.</p>
            <Link to="/upload" className="btn btn-primary" style={{ marginTop: 8 }}>Upload a Paper</Link>
          </div>
        )}

        {papers && papers.length > 0 && (
          <div className="paper-grid">
            {papers.map((p, i) => (
              <motion.div
                key={p.id}
                className="card card-hover paper-card"
                onClick={() => navigate(`/papers/${p.id}`)}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
              >
                <div className="paper-card-top">
                  <FileText size={18} color="var(--accent-primary)" />
                  <span className={`badge ${STATUS_BADGE[p.status] || 'badge-neutral'}`}>{p.status}</span>
                </div>
                <h3>{p.title || p.original_filename}</h3>
                <div className="meta-row">
                  <span><Layers size={12} /> {p.page_count || '—'} pages</span>
                  <span><Clock size={12} /> {new Date(p.uploaded_at).toLocaleDateString()}</span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
