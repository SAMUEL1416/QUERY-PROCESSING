import { AlertTriangle } from 'lucide-react'

export default function DatasetAlternative({ dataset }) {
  if (dataset.kind !== 'alternative') return null
  return (
    <div className="error-banner" style={{ background: 'rgba(240,180,41,0.08)', borderColor: 'rgba(240,180,41,0.3)', color: 'var(--status-warning)' }}>
      <AlertTriangle size={16} />
      <div>
        <strong>Alternative Dataset — Not the Original Dataset.</strong>{' '}
        {dataset.relevance_reason}
      </div>
    </div>
  )
}
