import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell } from 'recharts'
import { FileText, Database, Cpu, MessageSquareText } from 'lucide-react'

const COLORS = ['#5b5ff5', '#9c7dff', '#38bdf8', '#34d399', '#f0b429', '#fb7185']

function AnimatedCounter({ value }) {
  const [display, setDisplay] = useState(0)
  useEffect(() => {
    let frame
    const start = performance.now()
    const duration = 900
    const step = (now) => {
      const progress = Math.min(1, (now - start) / duration)
      setDisplay(Math.round(progress * value))
      if (progress < 1) frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [value])
  return <>{display}</>
}

function StatCard({ icon: Icon, value, label, delay }) {
  return (
    <motion.div
      className="stat-card"
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="stat-icon"><Icon size={18} /></div>
      <div className="stat-value"><AnimatedCounter value={value} /></div>
      <div className="stat-label">{label}</div>
    </motion.div>
  )
}

function BarChartCard({ title, sub, data }) {
  return (
    <motion.div className="card chart-card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <div>
        <h3>{title}</h3>
        <span className="chart-sub">{sub}</span>
      </div>
      {data.length === 0 ? (
        <p className="simple-explanation">Not identified.</p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} layout="vertical" margin={{ left: 12, right: 12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" horizontal={false} />
            <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
            <YAxis type="category" dataKey="label" stroke="var(--text-muted)" fontSize={11} width={110} />
            <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }} />
            <Bar dataKey="count" fill="var(--accent-primary)" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </motion.div>
  )
}

function PieChartCard({ title, sub, data }) {
  return (
    <motion.div className="card chart-card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <div>
        <h3>{title}</h3>
        <span className="chart-sub">{sub}</span>
      </div>
      {data.length === 0 ? (
        <p className="simple-explanation">Not identified.</p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie data={data} dataKey="count" nameKey="label" innerRadius={55} outerRadius={90} paddingAngle={3}>
              {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', borderRadius: 8, fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </motion.div>
  )
}

export default function AnalyticsDashboard({ overview, features }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <div className="stats-grid" style={{ margin: 0 }}>
        <StatCard icon={FileText} value={overview.papers_analyzed} label="Papers Analyzed" delay={0} />
        <StatCard icon={Database} value={overview.datasets_discovered} label="Datasets Discovered" delay={0.05} />
        <StatCard icon={Cpu} value={overview.features_extracted} label="Features Extracted" delay={0.1} />
        <StatCard icon={MessageSquareText} value={overview.queries_processed} label="Queries Processed" delay={0.15} />
      </div>

      <div className="analytics-grid">
        <BarChartCard title="Algorithm Distribution" sub="Top algorithms/models found across analyzed papers" data={features.algorithm_distribution} />
        <BarChartCard title="Metric Distribution" sub="Evaluation metrics found across analyzed papers" data={features.metric_distribution} />
        <PieChartCard title="Dataset Availability" sub="Original vs. alternative vs. synthetic vs. unresolved" data={features.dataset_availability} />
        <BarChartCard title="Concept Distribution" sub="Most frequent concepts/keywords" data={features.concept_distribution} />
      </div>
    </div>
  )
}
