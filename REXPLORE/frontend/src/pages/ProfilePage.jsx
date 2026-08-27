import { useRef, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, Pencil, Check, X, Loader2, Camera, ShieldCheck,
  Mail, Lock, Trash2, AlertCircle, CheckCircle2, FileText, MessageSquareText, Database,
} from 'lucide-react'
import Header from '../components/Header'
import api from '../api'
import { useAuth } from '../context/AuthContext'

function Banner({ tone, children }) {
  if (!children) return null
  const Icon = tone === 'success' ? CheckCircle2 : AlertCircle
  return (
    <div className={`auth-banner auth-banner-${tone}`} role={tone === 'error' ? 'alert' : undefined} style={{ marginBottom: 'var(--sp-4)' }}>
      <Icon size={16} />
      {children}
    </div>
  )
}

/** A read/edit row: shows the value, and swaps to an input on pencil-click. */
function EditableField({ label, value, placeholder, onSave, type = 'text', disabled }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const startEdit = () => {
    setDraft(value || '')
    setError('')
    setEditing(true)
  }

  const cancel = () => {
    setEditing(false)
    setError('')
  }

  const save = async () => {
    setError('')
    setSaving(true)
    try {
      await onSave(draft.trim())
      setEditing(false)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not save this change.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="profile-field">
      <div className="profile-field-label">{label}</div>
      {editing ? (
        <div className="profile-field-edit">
          <input
            type={type}
            value={draft}
            placeholder={placeholder}
            onChange={(e) => setDraft(e.target.value)}
            disabled={saving}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') save()
              if (e.key === 'Escape') cancel()
            }}
          />
          <button className="icon-btn icon-btn-success" onClick={save} disabled={saving} aria-label="Save">
            {saving ? <Loader2 size={15} className="spin" /> : <Check size={15} />}
          </button>
          <button className="icon-btn" onClick={cancel} disabled={saving} aria-label="Cancel">
            <X size={15} />
          </button>
        </div>
      ) : (
        <div className="profile-field-value">
          <span className={value ? '' : 'profile-field-empty'}>{value || placeholder}</span>
          {!disabled && (
            <button className="icon-btn" onClick={startEdit} aria-label={`Edit ${label}`}>
              <Pencil size={14} />
            </button>
          )}
        </div>
      )}
      {error && <div className="profile-field-error">{error}</div>}
    </div>
  )
}

function ProfileView({ user, updateUser, onOpenAccountSettings, stats }) {
  const fileInputRef = useRef(null)
  const [avatarUploading, setAvatarUploading] = useState(false)
  const [avatarError, setAvatarError] = useState('')

  const initials = (user.full_name || user.email || '?')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join('')

  const handleAvatarPick = () => fileInputRef.current?.click()

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setAvatarError('')
    setAvatarUploading(true)
    try {
      const res = await api.uploadAvatar(file)
      updateUser(res.data)
    } catch (err) {
      setAvatarError(err?.response?.data?.detail || 'Could not upload that image.')
    } finally {
      setAvatarUploading(false)
    }
  }

  const handleRemoveAvatar = async () => {
    setAvatarError('')
    setAvatarUploading(true)
    try {
      const res = await api.removeAvatar()
      updateUser(res.data)
    } catch (err) {
      setAvatarError(err?.response?.data?.detail || 'Could not remove the photo.')
    } finally {
      setAvatarUploading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <div className="card profile-hero">
        <div className="profile-avatar-block">
          <div className="profile-avatar-large">
            {user.avatar_url ? <img src={user.avatar_url} alt="" /> : <span>{initials}</span>}
            {avatarUploading && (
              <div className="profile-avatar-overlay"><Loader2 size={20} className="spin" /></div>
            )}
          </div>
          <div className="profile-avatar-actions">
            <button className="btn btn-secondary btn-sm" onClick={handleAvatarPick} disabled={avatarUploading}>
              <Camera size={14} /> {user.avatar_url ? 'Change photo' : 'Add image'}
            </button>
            {user.avatar_url && (
              <button className="btn btn-ghost btn-sm" onClick={handleRemoveAvatar} disabled={avatarUploading}>
                Remove
              </button>
            )}
            <input ref={fileInputRef} type="file" accept="image/*" hidden onChange={handleAvatarChange} />
          </div>
          {avatarError && <div className="profile-field-error" style={{ marginTop: 6 }}>{avatarError}</div>}
        </div>

        <div className="profile-hero-info">
          <h2>{user.full_name}</h2>
          <span className="profile-hero-email">{user.email}</span>
          <span className="profile-hero-since">
            Member since {new Date(user.created_at).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
          </span>
        </div>
      </div>

      {stats && (
        <div className="stats-grid profile-stats">
          <div className="card card-tight profile-stat">
            <FileText size={18} />
            <div>
              <strong>{stats.papers_analyzed}</strong>
              <span>Papers analyzed</span>
            </div>
          </div>
          <div className="card card-tight profile-stat">
            <MessageSquareText size={18} />
            <div>
              <strong>{stats.queries_processed}</strong>
              <span>Queries run</span>
            </div>
          </div>
          <div className="card card-tight profile-stat">
            <Database size={18} />
            <div>
              <strong>{stats.datasets_discovered}</strong>
              <span>Datasets discovered</span>
            </div>
          </div>
        </div>
      )}

      <div className="card profile-details">
        <h3 className="profile-section-title">Personal information</h3>
        <EditableField
          label="Full name"
          value={user.full_name}
          placeholder="Add your name"
          onSave={async (val) => {
            if (!val) throw { response: { data: { detail: 'Full name is required.' } } }
            const res = await api.updateProfile(val, user.affiliation)
            updateUser(res.data)
          }}
        />
        <EditableField
          label="Affiliation / Organization"
          value={user.affiliation}
          placeholder="e.g. MIT, Independent Researcher"
          onSave={async (val) => {
            const res = await api.updateProfile(user.full_name, val || null)
            updateUser(res.data)
          }}
        />
        <div className="profile-field">
          <div className="profile-field-label">Email</div>
          <div className="profile-field-value">
            <span>{user.email}</span>
            <span className="badge badge-neutral" style={{ marginLeft: 8 }}>Managed in Account settings</span>
          </div>
        </div>
      </div>

      <button className="card profile-settings-link" onClick={onOpenAccountSettings}>
        <div className="profile-settings-link-icon"><ShieldCheck size={18} /></div>
        <div>
          <strong>Account settings</strong>
          <span>Change your login email, password, or delete your account</span>
        </div>
        <ArrowLeft size={16} className="profile-settings-link-arrow" />
      </button>
    </motion.div>
  )
}

function AccountSettingsView({ user, updateUser, onLoggedOut }) {
  const { logout } = useAuth()

  const [emailModalOpen, setEmailModalOpen] = useState(false)
  const [emailForm, setEmailForm] = useState({ newEmail: '', password: '' })
  const [emailError, setEmailError] = useState('')
  const [emailBanner, setEmailBanner] = useState(null)
  const [savingEmail, setSavingEmail] = useState(false)

  const [passwordBanner, setPasswordBanner] = useState(null)
  const [passwordForm, setPasswordForm] = useState({ current: '', next: '', confirm: '' })
  const [savingPassword, setSavingPassword] = useState(false)

  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const openEmailModal = () => {
    setEmailForm({ newEmail: user.email, password: '' })
    setEmailError('')
    setEmailModalOpen(true)
  }

  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setEmailError('')
    setSavingEmail(true)
    try {
      const res = await api.updateEmail(emailForm.newEmail.trim(), emailForm.password)
      updateUser(res.data)
      setEmailModalOpen(false)
      setEmailBanner({ tone: 'success', text: 'Login email updated successfully.' })
    } catch (err) {
      setEmailError(err?.response?.data?.detail || 'Could not update your email.')
    } finally {
      setSavingEmail(false)
    }
  }

  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPasswordBanner(null)
    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordBanner({ tone: 'error', text: 'New passwords do not match.' })
      return
    }
    if (passwordForm.next.length < 8) {
      setPasswordBanner({ tone: 'error', text: 'New password must be at least 8 characters.' })
      return
    }
    setSavingPassword(true)
    try {
      await api.updatePassword(passwordForm.current, passwordForm.next, passwordForm.confirm)
      setPasswordBanner({ tone: 'success', text: 'Password updated successfully.' })
      setPasswordForm({ current: '', next: '', confirm: '' })
    } catch (err) {
      setPasswordBanner({ tone: 'error', text: err?.response?.data?.detail || 'Could not update your password.' })
    } finally {
      setSavingPassword(false)
    }
  }

  const handleDelete = async () => {
    setDeleteError('')
    setDeleting(true)
    try {
      await api.deleteAccount(deletePassword)
      await logout()
      onLoggedOut()
    } catch (err) {
      setDeleteError(err?.response?.data?.detail || 'Could not delete your account.')
      setDeleting(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <div className="card profile-details">
        <h3 className="profile-section-title"><Mail size={16} /> Login email</h3>
        <Banner tone={emailBanner?.tone}>{emailBanner?.text}</Banner>
        <div className="profile-field">
          <div className="profile-field-label">Login email</div>
          <div className="profile-field-value">
            <span>{user.email}</span>
            <button className="icon-btn" onClick={openEmailModal} aria-label="Change login email">
              <Pencil size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="card profile-details">
        <h3 className="profile-section-title"><Lock size={16} /> Password</h3>
        <Banner tone={passwordBanner?.tone}>{passwordBanner?.text}</Banner>
        <form className="profile-password-form" onSubmit={handlePasswordSubmit}>
          <label className="auth-field">
            <span>Current password</span>
            <input
              type="password"
              value={passwordForm.current}
              onChange={(e) => setPasswordForm((f) => ({ ...f, current: e.target.value }))}
              disabled={savingPassword}
              required
            />
          </label>
          <label className="auth-field">
            <span>New password</span>
            <input
              type="password"
              value={passwordForm.next}
              onChange={(e) => setPasswordForm((f) => ({ ...f, next: e.target.value }))}
              disabled={savingPassword}
              minLength={8}
              required
            />
          </label>
          <label className="auth-field">
            <span>Confirm new password</span>
            <input
              type="password"
              value={passwordForm.confirm}
              onChange={(e) => setPasswordForm((f) => ({ ...f, confirm: e.target.value }))}
              disabled={savingPassword}
              required
            />
          </label>
          <button type="submit" className="btn btn-primary btn-sm" disabled={savingPassword} style={{ alignSelf: 'flex-start' }}>
            {savingPassword ? <Loader2 size={14} className="spin" /> : null}
            {savingPassword ? 'Updating…' : 'Update password'}
          </button>
        </form>
      </div>

      <div className="card profile-details profile-danger-zone">
        <h3 className="profile-section-title profile-danger-title"><Trash2 size={16} /> Delete account</h3>
        <p className="profile-danger-copy">
          Permanently deletes your account and every paper, query, dataset, and analytics record associated with it. This cannot be undone.
        </p>
        <button className="btn btn-danger btn-sm" onClick={() => setDeleteOpen(true)}>
          Delete my account
        </button>
      </div>

      <AnimatePresence>
        {emailModalOpen && (
          <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => !savingEmail && setEmailModalOpen(false)}>
            <motion.div
              className="modal-panel"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>Change login email</h3>
                <button className="btn btn-ghost btn-sm" onClick={() => setEmailModalOpen(false)} disabled={savingEmail}>Close</button>
              </div>
              {emailError && <Banner tone="error">{emailError}</Banner>}
              <form onSubmit={handleEmailSubmit} className="profile-password-form">
                <label className="auth-field">
                  <span>New email</span>
                  <input
                    type="email"
                    value={emailForm.newEmail}
                    onChange={(e) => setEmailForm((f) => ({ ...f, newEmail: e.target.value }))}
                    disabled={savingEmail}
                    autoFocus
                    required
                  />
                </label>
                <label className="auth-field">
                  <span>Current password</span>
                  <input
                    type="password"
                    value={emailForm.password}
                    onChange={(e) => setEmailForm((f) => ({ ...f, password: e.target.value }))}
                    disabled={savingEmail}
                    required
                  />
                </label>
                <div style={{ display: 'flex', gap: 'var(--sp-3)', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEmailModalOpen(false)} disabled={savingEmail}>Cancel</button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={savingEmail}>
                    {savingEmail ? <Loader2 size={14} className="spin" /> : null}
                    {savingEmail ? 'Saving…' : 'Save email'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {deleteOpen && (
          <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => !deleting && setDeleteOpen(false)}>
            <motion.div
              className="modal-panel"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3>Delete your account?</h3>
                <button className="btn btn-ghost btn-sm" onClick={() => setDeleteOpen(false)} disabled={deleting}>Close</button>
              </div>
              <p className="profile-danger-copy" style={{ marginBottom: 'var(--sp-4)' }}>
                This will permanently remove your ReXplore account and all of your research data. Enter your password to confirm.
              </p>
              {deleteError && <Banner tone="error">{deleteError}</Banner>}
              <label className="auth-field" style={{ marginBottom: 'var(--sp-4)' }}>
                <span>Password</span>
                <input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  disabled={deleting}
                  autoFocus
                />
              </label>
              <div style={{ display: 'flex', gap: 'var(--sp-3)', justifyContent: 'flex-end' }}>
                <button className="btn btn-ghost btn-sm" onClick={() => setDeleteOpen(false)} disabled={deleting}>Cancel</button>
                <button className="btn btn-danger btn-sm" onClick={handleDelete} disabled={deleting || !deletePassword}>
                  {deleting ? <Loader2 size={14} className="spin" /> : null}
                  {deleting ? 'Deleting…' : 'Permanently delete'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default function ProfilePage({ onOpenSidebar }) {
  const { user, updateUser } = useAuth()
  const navigate = useNavigate()
  const [view, setView] = useState('profile') // 'profile' | 'account'
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.getAnalyticsOverview().then((r) => setStats(r.data)).catch(() => {})
  }, [])

  if (!user) return null

  const goBack = () => {
    if (view === 'account') setView('profile')
    else navigate(-1)
  }

  return (
    <div>
      <Header
        title={view === 'account' ? 'Account settings' : 'Profile'}
        subtitle={view === 'account' ? 'Manage how you sign in to ReXplore' : 'Your ReXplore identity and research activity'}
        onOpenSidebar={onOpenSidebar}
        actions={
          <button className="btn btn-ghost btn-sm" onClick={goBack}>
            <ArrowLeft size={15} /> Back
          </button>
        }
      />
      <div className="app-content profile-page">
        {view === 'profile' ? (
          <ProfileView user={user} updateUser={updateUser} onOpenAccountSettings={() => setView('account')} stats={stats} />
        ) : (
          <AccountSettingsView user={user} updateUser={updateUser} onLoggedOut={() => navigate('/login', { replace: true })} />
        )}
      </div>
    </div>
  )
}
