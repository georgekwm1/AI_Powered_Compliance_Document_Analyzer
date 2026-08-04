import { useEffect, useState } from 'react'
import { listDocuments, deleteDocument } from '../api'

export default function Sidebar({ selected, onSelect, refreshKey, onChange }) {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function refresh() {
    setLoading(true)
    setError(null)
    try {
      const data = await listDocuments()
      setDocs(data.documents || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [refreshKey])

  async function handleDelete(name, e) {
    e.stopPropagation()
    if (!confirm(`Delete "${name}"?`)) return
    try {
      await deleteDocument(name)
      if (selected === name) onSelect(null)
      onChange?.()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <aside className="w-72 shrink-0 border-r border-slate-200 bg-white flex flex-col">
      <div className="px-4 py-4 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-900 uppercase tracking-wide">
          Documents
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          {docs.length} file{docs.length === 1 ? '' : 's'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading && (
          <p className="px-4 py-3 text-sm text-slate-500">Loading…</p>
        )}
        {error && (
          <p className="px-4 py-3 text-sm text-rose-600">{error}</p>
        )}
        {!loading && !error && docs.length === 0 && (
          <p className="px-4 py-3 text-sm text-slate-500">No documents yet.</p>
        )}
        <ul>
          {docs.map((name) => {
            const isActive = selected === name
            return (
              <li key={name}>
                <button
                  onClick={() => onSelect(name)}
                  className={`w-full text-left px-4 py-2.5 flex items-center gap-2 border-l-2 transition ${
                    isActive
                      ? 'bg-indigo-50 border-indigo-500 text-indigo-900'
                      : 'border-transparent hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <span className="truncate flex-1 text-sm">{name}</span>
                  <span
                    onClick={(e) => handleDelete(name, e)}
                    className="text-xs text-slate-400 hover:text-rose-600 px-1"
                    title="Delete"
                  >
                    ✕
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>

      <button
        onClick={refresh}
        className="border-t border-slate-200 py-2 text-xs text-slate-500 hover:bg-slate-50"
      >
        Refresh
      </button>
    </aside>
  )
}
