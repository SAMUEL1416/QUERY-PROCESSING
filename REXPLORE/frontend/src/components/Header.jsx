import { motion } from 'framer-motion'
import { Menu } from 'lucide-react'

export default function Header({ title, subtitle, onOpenSidebar, actions }) {
  return (
    <>
      <button className="sidebar-toggle" onClick={onOpenSidebar} aria-label="Open navigation">
        <Menu size={20} />
      </button>
      <motion.div
        className="topbar"
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="topbar-title">
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {actions && <div className="topbar-actions">{actions}</div>}
      </motion.div>
    </>
  )
}
