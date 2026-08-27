import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import SourceReference from './SourceReference'

export default function SectionExplanation({ section, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <motion.div className="card section-card" layout>
      <div className="section-card-header" onClick={() => setOpen((o) => !o)}>
        <div className="section-card-title">
          <SourceReference sectionName={section.name} pageNumber={section.page_number} onClick={(e) => e.stopPropagation()} />
          <h3>{section.name}</h3>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={18} />
        </motion.div>
      </div>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className="section-card-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="section-card-body-inner">
              <div>
                <span className="section-block-label">Simple Explanation</span>
                <p className="simple-explanation">{section.simple_explanation}</p>
              </div>

              <div>
                <span className="section-block-label">Key Points</span>
                <ul className="key-points-list">
                  {section.key_points.map((kp, i) => <li key={i}>{kp}</li>)}
                </ul>
              </div>

              <div>
                <span className="section-block-label">Important Concepts</span>
                <div className="chip-row">
                  {section.concepts.map((c, i) => <span key={i} className="badge badge-accent">{c}</span>)}
                </div>
              </div>

              <div>
                <span className="section-block-label">Findings</span>
                <ul className="key-points-list">
                  {section.findings.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
