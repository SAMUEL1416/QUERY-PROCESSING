import { useCallback, useRef, useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, CheckCircle2, Loader2, FileWarning } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

const STAGE_LABELS = [
  'Uploading',
  'Reading Paper',
  'Detecting Sections',
  'Extracting Features',
  'Understanding Research',
  'Detecting Datasets',
  'Building Semantic Index',
  'Ready',
]

export default function PaperUpload() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadPct, setUploadPct] = useState(0)
  const [paperId, setPaperId] = useState(null)
  const [statusDetail, setStatusDetail] = useState('')
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const pollRef = useRef(null)
  const navigate = useNavigate()

  const handleFiles = useCallback(async (files) => {
    const file = files?.[0]
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF file.')
      return
    }
    setError(null)
    setUploading(true)
    setUploadPct(0)
    try {
      const res = await api.uploadPaper(file, setUploadPct)
      setPaperId(res.data.id)
      setStatusDetail(res.data.status_detail || 'Uploading')
    } catch (err) {
      setUploading(false)
      if (err?.code === 'ECONNABORTED') {
        setError('This is taking longer than expected. Large or scanned PDFs can take a few minutes to process - please try again, and keep this tab open while it runs.')
      } else {
        setError(err?.response?.data?.detail || 'Upload failed. Please try again.')
      }
    }
  }, [])

  useEffect(() => {
    if (!paperId) return
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.getPaper(paperId)
        setStatusDetail(res.data.status_detail)
        if (res.data.status === 'ready') {
          clearInterval(pollRef.current)
          setTimeout(() => navigate(`/papers/${paperId}`), 600)
        } else if (res.data.status === 'error') {
          clearInterval(pollRef.current)
          setError(res.data.error_message || 'Processing failed.')
        }
      } catch {
        // transient error, keep polling
      }
    }, 1500)
    return () => clearInterval(pollRef.current)
  }, [paperId, navigate])

  const currentStageIndex = STAGE_LABELS.findIndex((s) => s === statusDetail)

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div>
      {!uploading && (
        <motion.div
          className={`dropzone ${dragging ? 'dragging' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="dropzone-icon">
            <UploadCloud size={28} />
          </div>
          <h3>Drag & drop a research paper PDF here</h3>
          <p>or click to browse — complete papers up to 50MB, including scanned PDFs (OCR fallback)</p>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </motion.div>
      )}

      {error && (
        <motion.div className="error-banner" style={{ marginTop: 20 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <FileWarning size={18} />
          <span>{error}</span>
        </motion.div>
      )}

      <AnimatePresence>
        {uploading && (
          <motion.div
            className="processing-stages"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {!paperId && (
              <div className="processing-stage current">
                <Loader2 className="stage-icon" size={16} style={{ animation: 'spin 0.8s linear infinite' }} />
                <span>
                  Uploading ({uploadPct}%)
                  <span className="processing-stage-hint">Large or scanned PDFs can take a few minutes - please keep this tab open.</span>
                </span>
              </div>
            )}
            {paperId && STAGE_LABELS.map((label, idx) => {
              const done = currentStageIndex > idx || (currentStageIndex === -1 && idx === 0)
              const current = idx === currentStageIndex
              return (
                <motion.div
                  key={label}
                  className={`processing-stage ${done ? 'done' : ''} ${current ? 'current' : ''}`}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.03 }}
                >
                  {done ? <CheckCircle2 className="stage-icon" size={16} /> : <Loader2 className="stage-icon" size={16} style={current ? { animation: 'spin 0.8s linear infinite' } : {}} />}
                  {label}
                </motion.div>
              )
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
