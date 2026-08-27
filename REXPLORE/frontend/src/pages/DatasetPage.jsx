import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import DatasetCard from '../components/DatasetCard'
import SyntheticGenerator from '../components/SyntheticGenerator'
import api from '../api'

export default function DatasetPage({ paperId }) {
  const [datasets, setDatasets] = useState(null)
  const [refreshingId, setRefreshingId] = useState(null)
  const [syntheticTarget, setSyntheticTarget] = useState(null)

  const load = () => api.getDatasetsForPaper(paperId).then((r) => setDatasets(r.data)).catch(() => setDatasets([]))

  useEffect(() => { load() }, [paperId])

  const refresh = async (datasetId) => {
    setRefreshingId(datasetId)
    try {
      await api.refreshDatasetSearch(datasetId)
      await load()
    } finally {
      setRefreshingId(null)
    }
  }

  if (!datasets) {
    return <div className="dataset-grid">{[0, 1].map((i) => <div key={i} className="skeleton" style={{ height: 200, borderRadius: 16 }} />)}</div>
  }

  if (datasets.length === 0) {
    return (
      <div className="state-block">
        <h3>No datasets detected</h3>
        <p>ReXplore did not find explicit dataset mentions in this paper's text.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="dataset-grid">
        {datasets.map((d) => (
          <DatasetCard
            key={d.id}
            dataset={d}
            refreshing={refreshingId === d.id}
            onRefresh={() => refresh(d.id)}
            onGenerateSynthetic={() => setSyntheticTarget(d)}
          />
        ))}
      </div>

      {syntheticTarget && (
        <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={() => setSyntheticTarget(null)}>
          <motion.div
            className="modal-panel"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>Generate Synthetic Dataset — {syntheticTarget.mentioned_name}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setSyntheticTarget(null)}>Close</button>
            </div>
            <SyntheticGenerator dataset={syntheticTarget} onGenerated={() => load()} />
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}
