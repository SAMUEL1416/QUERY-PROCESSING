import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { UploadCloud, Library } from 'lucide-react'
import Header from '../components/Header'
import AnalyticsDashboard from '../components/AnalyticsDashboard'
import api from '../api'

const WORKFLOW = ['Upload', 'Extract', 'Understand', 'Query', 'Discover', 'Analyze']

export default function Dashboard({ onOpenSidebar }) {
  const [overview, setOverview] = useState(null)
  const [features, setFeatures] = useState(null)
  const [activeNode, setActiveNode] = useState(0)

  useEffect(() => {
    api.getAnalyticsOverview().then((r) => setOverview(r.data)).catch(() => setOverview({
      papers_analyzed: 0, datasets_discovered: 0, features_extracted: 0, queries_processed: 0,
    }))
    api.getAnalyticsFeatures().then((r) => setFeatures(r.data)).catch(() => setFeatures({
      algorithm_distribution: [], metric_distribution: [], dataset_availability: [], concept_distribution: [],
    }))
  }, [])

  useEffect(() => {
    const interval = setInterval(() => setActiveNode((n) => (n + 1) % WORKFLOW.length), 1400)
    return () => clearInterval(interval)
  }, [])

  return (
    <div>
      <Header title="Dashboard" onOpenSidebar={onOpenSidebar} />
      <div className="app-content" style={{ paddingTop: 0 }}>
        <motion.section className="hero" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
          <span className="hero-eyebrow">Research Intelligence Platform</span>
          <h1>ReXplore: Intelligent Research Understanding &amp; Knowledge Discovery</h1>
          <p className="lede">
            Transform complex research papers into structured, searchable and understandable research knowledge.
          </p>
          <div className="hero-cta">
            <Link to="/upload" className="btn btn-primary"><UploadCloud size={16} /> Upload a Paper</Link>
            <Link to="/library" className="btn btn-secondary"><Library size={16} /> Browse Library</Link>
          </div>
        </motion.section>

        <div className="workflow-rail">
          {WORKFLOW.map((step, i) => (
            <div key={step} style={{ display: 'flex', alignItems: 'center' }}>
              <div className={`workflow-node ${i === activeNode ? 'active' : ''}`}>
                <div className="workflow-node-dot">{String(i + 1).padStart(2, '0')}</div>
                <span className="label">{step}</span>
              </div>
              {i < WORKFLOW.length - 1 && <div className="workflow-connector" />}
            </div>
          ))}
        </div>

        {overview && features ? (
          <AnalyticsDashboard overview={overview} features={features} />
        ) : (
          <div className="stats-grid">
            {[0, 1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 16 }} />)}
          </div>
        )}
      </div>
    </div>
  )
}
