import { Search, ArrowRight } from 'lucide-react'

const EXAMPLE_QUESTIONS = [
  'What problem does this paper address?',
  'Explain the methodology simply.',
  'What dataset was used?',
  'What model was proposed?',
  'What are the main findings?',
  'What metrics were used?',
  'What are the limitations?',
  'What is the main contribution?',
]

export default function QueryBox({ value, onChange, onSubmit, disabled }) {
  return (
    <div className="query-box">
      <div className="query-input-row">
        <Search size={18} color="var(--text-muted)" />
        <input
          placeholder="Ask ReXplore about this paper…"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && value.trim()) onSubmit() }}
          disabled={disabled}
        />
        <button className="btn btn-primary btn-sm" onClick={onSubmit} disabled={disabled || !value.trim()}>
          Ask <ArrowRight size={14} />
        </button>
      </div>
      <div className="example-questions">
        {EXAMPLE_QUESTIONS.map((q) => (
          <button key={q} className="example-question-chip" onClick={() => onChange(q)} type="button">
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
