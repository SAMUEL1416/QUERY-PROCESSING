import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Loader2 } from 'lucide-react'
import Header from '../components/Header'
import PaperOverview from '../components/PaperOverview'
import SectionExplanation from '../components/SectionExplanation'
import FeatureList from '../components/FeatureList'
import QueryPage from './QueryPage'
import DatasetPage from './DatasetPage'
import api from '../api'

const TABS = ['Overview', 'Research Understanding', 'Query Processing', 'Dataset Intelligence', 'Knowledge Discovery', 'Analytics']

const KNOWLEDGE_CHAIN = [
  { key: 'Problem', names: ['Problem Statement'] },
  { key: 'Objective', names: ['Objectives'] },
  { key: 'Method', names: ['Methodology', 'Method', 'Proposed Method', 'Proposed Approach'] },
  { key: 'Model', types: ['algorithm'] },
  { key: 'Dataset', types: ['dataset'] },
  { key: 'Evaluation', types: ['metric'] },
  { key: 'Results', names: ['Results', 'Experiments'] },
]

function KnowledgeDiscoveryPanel({ paper }) {
  const findValue = (node) => {
    if (node.names) {
      const sec = paper.sections.find((s) => node.names.includes(s.name))
      return sec ? (sec.key_points[0] || sec.simple_explanation) : null
    }
    if (node.types) {
      const feats = paper.features.filter((f) => node.types.includes(f.feature_type)).slice(0, 3)
      return feats.length ? feats.map((f) => f.value).join(', ') : null
    }
    return null
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: 8 }}>Supported Knowledge Chain</h3>
      <p className="simple-explanation" style={{ marginBottom: 8 }}>
        Only relationships directly supported by the paper's extracted content are shown below.
      </p>
      <div className="knowledge-flow">
        {KNOWLEDGE_CHAIN.map((node, i) => {
          const value = findValue(node)
          if (!value) return null
          return (
            <div key={node.key} style={{ display: 'flex', alignItems: 'center' }}>
              <div className="knowledge-node">
                <span className="node-label">{node.key}</span>
                <span className="node-value">{value}</span>
              </div>
              {i < KNOWLEDGE_CHAIN.length - 1 && <div className="knowledge-arrow"><ArrowRight size={18} /></div>}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function PaperPage({ onOpenSidebar }) {
  const { id } = useParams()
  const [paper, setPaper] = useState(null)
  const [tab, setTab] = useState('Overview')

  useEffect(() => {
    // Poll for live status_detail updates while the paper is processing.
    // Keyed only on `id` (not on paper.status) so a status transition
    // doesn't tear down and recreate this effect - that previously fired an
    // extra immediate fetch on every transition and left a dangling 2s
    // timer ticking forever even after the paper was ready. Same polling
    // behavior and UI updates, just without the redundant requests/timer.
    let cancelled = false
    const load = () =>
      api.getPaper(id).then((r) => {
        if (cancelled) return
        setPaper(r.data)
        if (r.data.status === 'ready' || r.data.status === 'error') {
          clearInterval(interval)
        }
      }).catch(() => {})

    load()
    const interval = setInterval(load, 2000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [id])

  if (!paper) {
    return (
      <div>
        <Header title="Loading…" onOpenSidebar={onOpenSidebar} />
        <div className="app-content"><div className="skeleton" style={{ height: 300, borderRadius: 16 }} /></div>
      </div>
    )
  }

  if (paper.status !== 'ready') {
    return (
      <div>
        <Header title={paper.original_filename} onOpenSidebar={onOpenSidebar} />
        <div className="app-content">
          <div className="state-block">
            <Loader2 size={28} style={{ animation: 'spin 0.8s linear infinite' }} color="var(--accent-primary)" />
            <h3>{paper.status === 'error' ? 'Processing failed' : paper.status_detail || 'Processing…'}</h3>
            <p>{paper.status === 'error' ? paper.error_message : 'This page will update automatically once analysis is complete.'}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <Header title={paper.title || paper.original_filename} onOpenSidebar={onOpenSidebar} />
      <div className="app-content">
        <div className="workspace-header">
          <div>
            <div className="workspace-meta">
              <span className="meta-item">{paper.page_count} pages</span>
              <span className="meta-item badge badge-success">{paper.status}</span>
              {paper.research_domain && <span className="meta-item badge badge-accent">{paper.research_domain}</span>}
              {paper.used_ocr && <span className="meta-item badge badge-info">OCR used</span>}
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => api.openPaperFile(paper.id)}>
            View Original PDF
          </button>
        </div>

        <div className="tabs">
          {TABS.map((t) => (
            <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)} style={{ cursor: 'pointer' }}>
              {t}
              {tab === t && <motion.div className="tab-underline" layoutId="tab-underline" />}
            </div>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.2 }}>
            {tab === 'Overview' && <PaperOverview paper={paper} />}

            {tab === 'Research Understanding' && (
              <div>
                {paper.sections.map((s, i) => <SectionExplanation key={s.id} section={s} defaultOpen={i === 0} />)}
              </div>
            )}

            {tab === 'Query Processing' && <QueryPage paperId={paper.id} />}

            {tab === 'Dataset Intelligence' && <DatasetPage paperId={paper.id} />}

            {tab === 'Knowledge Discovery' && <KnowledgeDiscoveryPanel paper={paper} />}

            {tab === 'Analytics' && (
              <div className="card">
                <h3 style={{ marginBottom: 16 }}>Extracted Features for This Paper</h3>
                <FeatureList features={paper.features} />
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
