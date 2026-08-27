import { useEffect, useState } from 'react'
import Header from '../components/Header'
import AnalyticsDashboard from '../components/AnalyticsDashboard'
import api from '../api'

export default function AnalyticsPage({ onOpenSidebar }) {
  const [overview, setOverview] = useState(null)
  const [features, setFeatures] = useState(null)

  useEffect(() => {
    api.getAnalyticsOverview().then((r) => setOverview(r.data))
    api.getAnalyticsFeatures().then((r) => setFeatures(r.data))
  }, [])

  return (
    <div>
      <Header title="Research Analytics" subtitle="Real, backend-derived statistics across every paper you've analyzed" onOpenSidebar={onOpenSidebar} />
      <div className="app-content">
        {overview && features ? (
          <AnalyticsDashboard overview={overview} features={features} />
        ) : (
          <div className="stats-grid">{[0, 1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 16 }} />)}</div>
        )}
      </div>
    </div>
  )
}
