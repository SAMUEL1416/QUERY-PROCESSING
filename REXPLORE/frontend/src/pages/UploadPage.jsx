import Header from '../components/Header'
import PaperUpload from '../components/PaperUpload'

export default function UploadPage({ onOpenSidebar }) {
  return (
    <div>
      <Header title="Upload Paper" subtitle="Upload a complete research-paper PDF for full-text analysis" onOpenSidebar={onOpenSidebar} />
      <div className="app-content" style={{ maxWidth: 720 }}>
        <PaperUpload />
      </div>
    </div>
  )
}
