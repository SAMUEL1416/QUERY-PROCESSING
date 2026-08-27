const TYPE_LABELS = {
  algorithm: 'Algorithms & Models',
  metric: 'Evaluation Metrics',
  dataset: 'Datasets Mentioned',
  concept: 'Concepts & Keywords',
}

const TYPE_BADGE_CLASS = {
  algorithm: 'badge-accent',
  metric: 'badge-info',
  dataset: 'badge-warning',
  concept: 'badge-neutral',
}

export default function FeatureList({ features }) {
  const grouped = features.reduce((acc, f) => {
    (acc[f.feature_type] = acc[f.feature_type] || []).push(f)
    return acc
  }, {})

  const types = Object.keys(TYPE_LABELS).filter((t) => grouped[t]?.length)

  if (types.length === 0) {
    return <p className="simple-explanation">Not identified in the available paper content.</p>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {types.map((type) => (
        <div key={type}>
          <span className="section-block-label">{TYPE_LABELS[type]}</span>
          <div className="chip-row">
            {grouped[type].map((f) => (
              <span key={f.id} className={`badge ${TYPE_BADGE_CLASS[type]}`} title={f.context}>
                {f.value}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
