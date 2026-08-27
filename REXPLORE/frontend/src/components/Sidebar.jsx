import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Library, UploadCloud, MessageSquareText,
  Database, Share2, BarChart3, GitCompare, X, Sun, Moon, LogOut, User,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/library', label: 'Research Library', icon: Library },
  { to: '/upload', label: 'Upload Paper', icon: UploadCloud },
  { to: '/comparison', label: 'Paper Comparison', icon: GitCompare },
  { to: '/analytics', label: 'Research Analytics', icon: BarChart3 },
]

export default function Sidebar({ open, onClose, theme, onToggleTheme }) {
  const { user, logout } = useAuth()

  const initials = (user?.full_name || user?.email || '?')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join('')

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">R</div>
        <div className="sidebar-brand-text">
          <strong>ReXplore</strong>
          <span>Research Intelligence</span>
        </div>
        <button className="btn-ghost btn-sm" style={{ marginLeft: 'auto', display: open ? 'inline-flex' : 'none' }} onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            onClick={onClose}
          >
            <Icon />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {user && (
          <NavLink to="/profile" className="sidebar-profile" onClick={onClose}>
            <div className="sidebar-profile-avatar">
              {user.avatar_url ? <img src={user.avatar_url} alt="" /> : (initials || <User size={16} />)}
            </div>
            <div className="sidebar-profile-info">
              <strong>{user.full_name}</strong>
              <span>{user.email}</span>
            </div>
          </NavLink>
        )}

        <button className="sidebar-link" onClick={onToggleTheme} style={{ width: '100%', border: 'none', background: 'transparent' }}>
          {theme === 'dark' ? <Sun /> : <Moon />}
          {theme === 'dark' ? 'Light mode' : 'Dark mode'}
        </button>

        <button
          className="sidebar-link sidebar-logout"
          onClick={logout}
          style={{ width: '100%', border: 'none', background: 'transparent' }}
        >
          <LogOut />
          Logout
        </button>
      </div>
    </aside>
  )
}
