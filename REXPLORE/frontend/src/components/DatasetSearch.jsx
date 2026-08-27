import { ExternalLink } from 'lucide-react'

export default function DatasetSearch({ candidates }) {
  if (!candidates || candidates.length === 0) {
    return <p className="simple-explanation">No public repository results were found for this dataset name.</p>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {candidates.map((c, i) => (
        <div key={i} className="card card-tight" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 'var(--fs-sm)' }}>{c.name}</div>
            <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>{c.repository}{c.doi ? ` · DOI: ${c.doi}` : ''}</div>
          </div>
          {c.url && (
            <a className="btn btn-ghost btn-sm" href={c.url} target="_blank" rel="noreferrer">
              <ExternalLink size={14} />
            </a>
          )}
        </div>
      ))}
    </div>
  )
}
