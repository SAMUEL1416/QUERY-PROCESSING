import { FileText } from 'lucide-react'

export default function SourceReference({ sectionName, pageNumber, onClick }) {
  return (
    <button className="cite-chip" onClick={onClick} type="button">
      <FileText size={12} />
      {pageNumber ? `Page ${pageNumber}` : 'Page —'} <span className="dot">·</span> {sectionName}
    </button>
  )
}
