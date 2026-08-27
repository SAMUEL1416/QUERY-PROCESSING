import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import SourceReference from './SourceReference'

export default function QueryAnswer({ query }) {
  return (
    <motion.div
      className="card answer-card"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <Sparkles size={16} color="var(--accent-primary)" />
        <span className="section-block-label" style={{ margin: 0 }}>
          {query.retrieval_method === 'semantic' ? 'Semantic Answer' : 'Keyword-Matched Answer'}
        </span>
      </div>
      <p className="answer-text">{query.answer_text}</p>
      {query.sources?.length > 0 && (
        <div className="source-list">
          {query.sources.map((s, i) => (
            <SourceReference key={i} sectionName={s.section_name} pageNumber={s.page_number} onClick={() => {}} />
          ))}
        </div>
      )}
    </motion.div>
  )
}
