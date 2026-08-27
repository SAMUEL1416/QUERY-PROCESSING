import { motion } from 'framer-motion'
import { Database, ExternalLink, RefreshCw, FlaskConical } from 'lucide-react'

const KIND_BADGE = {
  original: { label: 'Original Dataset', cls: 'badge-success' },
  alternative: { label: 'Alternative — Not the Original', cls: 'badge-warning' },
  synthetic: { label: 'Synthetic — Not Original Research Data', cls: 'badge-danger' },
  not_found: { label: 'Not Found Publicly', cls: 'badge-neutral' },
}

export default function DatasetCard({ dataset, onRefresh, onGenerateSynthetic, refreshing }) {
  const badge = KIND_BADGE[dataset.kind] || KIND_BADGE.not_found

  return (
    <motion.div className="card card-hover dataset-card" layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <div className="dataset-card-top">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Database size={18} color="var(--accent-primary)" />
          <h3>{dataset.mentioned_name}</h3>
        </div>
        <span className={`badge ${badge.cls}`}>{badge.label}</span>
      </div>

      {dataset.kind === 'synthetic' && (
        <div className="synthetic-banner">SYNTHETIC DATASET — NOT THE ORIGINAL RESEARCH DATA</div>
      )}
      {dataset.kind === 'alternative' && dataset.relevance_reason && (
        <p className="simple-explanation">{dataset.relevance_reason}</p>
      )}

      {(dataset.kind === 'original' || dataset.kind === 'alternative') && (
        <div className="dataset-meta-row">
          <div><span className="k">Name</span> {dataset.name}</div>
          <div><span className="k">Repository</span> {dataset.repository}</div>
          <div><span className="k">DOI</span> {dataset.doi || 'Not available'}</div>
          <div><span className="k">Description</span> {dataset.description}</div>
        </div>
      )}

      <div className="dataset-actions">
        <button className="btn btn-secondary btn-sm" onClick={onRefresh} disabled={refreshing}>
          <RefreshCw size={14} style={refreshing ? { animation: 'spin 0.8s linear infinite' } : {}} />
          {refreshing ? 'Searching…' : 'Find Public Sources'}
        </button>
        {dataset.url && (
          <a className="btn btn-primary btn-sm" href={dataset.url} target="_blank" rel="noreferrer">
            <ExternalLink size={14} /> Open Source
          </a>
        )}
        {dataset.kind === 'not_found' && (
          <button className="btn btn-secondary btn-sm" onClick={onGenerateSynthetic}>
            <FlaskConical size={14} /> Generate Synthetic Dataset
          </button>
        )}
      </div>
    </motion.div>
  )
}
