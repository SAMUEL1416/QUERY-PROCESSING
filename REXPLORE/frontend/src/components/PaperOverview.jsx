import { FileText, Layers, Cpu, Globe2 } from 'lucide-react'

const NOT_IDENTIFIED = 'Not identified in the available paper content.'

export default function PaperOverview({ paper }) {
  const abstractSection = paper.sections?.find((s) => s.name === 'Abstract')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="card">
        <span className="section-block-label">Abstract</span>
        <p className="simple-explanation">
          {abstractSection ? abstractSection.simple_explanation : NOT_IDENTIFIED}
        </p>
      </div>

      <div className="stats-grid" style={{ margin: 0, gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="stat-card">
          <div className="stat-icon"><FileText size={18} /></div>
          <div className="stat-value">{paper.page_count}</div>
          <div className="stat-label">Pages</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Layers size={18} /></div>
          <div className="stat-value">{paper.sections?.length || 0}</div>
          <div className="stat-label">Sections Detected</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Cpu size={18} /></div>
          <div className="stat-value">{paper.features?.length || 0}</div>
          <div className="stat-label">Features Extracted</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Globe2 size={18} /></div>
          <div className="stat-value" style={{ fontSize: 'var(--fs-md)' }}>{paper.research_domain || NOT_IDENTIFIED}</div>
          <div className="stat-label">Research Domain</div>
        </div>
      </div>
    </div>
  )
}
