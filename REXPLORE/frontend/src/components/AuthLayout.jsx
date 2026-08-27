import { motion } from 'framer-motion'
import { FileText, Search, Database, BarChart3 } from 'lucide-react'

const NODES = [
  { x: 12, y: 18, delay: 0 },
  { x: 34, y: 8, delay: 0.4 },
  { x: 58, y: 22, delay: 0.8 },
  { x: 80, y: 12, delay: 1.2 },
  { x: 20, y: 48, delay: 0.2 },
  { x: 46, y: 42, delay: 0.6 },
  { x: 70, y: 50, delay: 1.0 },
  { x: 88, y: 40, delay: 1.4 },
  { x: 14, y: 76, delay: 0.3 },
  { x: 40, y: 82, delay: 0.7 },
  { x: 64, y: 74, delay: 1.1 },
  { x: 84, y: 84, delay: 1.5 },
]

const EDGES = [
  [0, 1], [1, 2], [2, 3], [0, 4], [1, 5], [2, 5], [3, 6], [3, 7],
  [4, 5], [5, 6], [6, 7], [4, 8], [5, 9], [6, 10], [7, 11], [8, 9], [9, 10], [10, 11],
]

const FEATURES = [
  { icon: FileText, label: 'Understand papers in plain language' },
  { icon: Search, label: 'Ask grounded, cited questions' },
  { icon: Database, label: 'Discover real, matching datasets' },
  { icon: BarChart3, label: 'Track research analytics over time' },
]

export default function AuthLayout({ eyebrow, title, subtitle, children }) {
  return (
    <div className="auth-shell">
      <div className="auth-visual">
        <svg className="auth-network" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {EDGES.map(([a, b], i) => (
            <line
              key={i}
              x1={NODES[a].x} y1={NODES[a].y}
              x2={NODES[b].x} y2={NODES[b].y}
              className="auth-network-edge"
            />
          ))}
          {NODES.map((n, i) => (
            <circle key={i} cx={n.x} cy={n.y} r="0.9" className="auth-network-node" style={{ animationDelay: `${n.delay}s` }} />
          ))}
        </svg>

        <div className="auth-visual-content">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="sidebar-brand-mark auth-visual-mark">R</div>
            <h2>ReXplore</h2>
            <p>Intelligent Semantic Research Understanding &amp; Knowledge Discovery</p>

            <ul className="auth-feature-list">
              {FEATURES.map(({ icon: Icon, label }, i) => (
                <motion.li
                  key={label}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: 0.15 + i * 0.08 }}
                >
                  <Icon size={16} />
                  {label}
                </motion.li>
              ))}
            </ul>
          </motion.div>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form-inner">
          <span className="hero-eyebrow">{eyebrow}</span>
          <h1 className="auth-title">{title}</h1>
          {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  )
}
