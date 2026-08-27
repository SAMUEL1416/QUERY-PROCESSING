import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import QueryBox from '../components/QueryBox'
import QueryAnswer from '../components/QueryAnswer'
import api from '../api'

const PROCESSING_STATES = ['Understanding query...', 'Searching paper...', 'Ranking relevant sections...', 'Preparing answer...']

export default function QueryPage({ paperId }) {
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [processingStateIdx, setProcessingStateIdx] = useState(0)
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getQueryHistory(paperId).then((r) => setHistory(r.data)).catch(() => {})
  }, [paperId])

  useEffect(() => {
    if (!asking) return
    const interval = setInterval(() => {
      setProcessingStateIdx((i) => (i + 1 < PROCESSING_STATES.length ? i + 1 : i))
    }, 500)
    return () => clearInterval(interval)
  }, [asking])

  const ask = async () => {
    if (!question.trim()) return
    setError(null)
    setAsking(true)
    setProcessingStateIdx(0)
    try {
      const res = await api.askQuestion(paperId, question)
      setHistory((h) => [res.data, ...h])
      setQuestion('')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not process this question.')
    } finally {
      setAsking(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="card">
        <h3 style={{ marginBottom: 16 }}>Ask ReXplore about this paper</h3>
        <QueryBox value={question} onChange={setQuestion} onSubmit={ask} disabled={asking} />
        <AnimatePresence>
          {asking && (
            <motion.div className="query-processing-state" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Loader2 size={16} style={{ animation: 'spin 0.8s linear infinite' }} />
              {PROCESSING_STATES[processingStateIdx]}
            </motion.div>
          )}
        </AnimatePresence>
        {error && <div className="error-banner" style={{ marginTop: 12 }}>{error}</div>}
      </div>

      <AnimatePresence>
        {history.map((q) => <QueryAnswer key={q.id} query={q} />)}
      </AnimatePresence>

      {history.length === 0 && !asking && (
        <div className="state-block">
          <h3>No questions asked yet</h3>
          <p>Try one of the example questions above, or ask your own — answers are grounded only in this paper's content.</p>
        </div>
      )}
    </div>
  )
}
