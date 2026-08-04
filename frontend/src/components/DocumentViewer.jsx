import { useEffect, useState } from 'react'
import { getDocument } from '../api'

export default function DocumentViewer({ filename }) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!filename) {
      setContent('')
      setError(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    getDocument(filename)
      .then((data) => {
        if (!cancelled) setContent(data.content || '')
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [filename])

  if (!filename) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
        Select a document from the sidebar to preview its contents.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      <div className="border-b border-slate-200 px-4 py-2.5 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 truncate">
          {filename}
        </h3>
      </div>
      <div className="p-4 max-h-96 overflow-y-auto">
        {loading && <p className="text-sm text-slate-500">Loading…</p>}
        {error && <p className="text-sm text-rose-600">{error}</p>}
        {!loading && !error && (
          <pre className="whitespace-pre-wrap break-words text-xs text-slate-700 font-mono">
            {content || '(empty)'}
          </pre>
        )}
      </div>
    </div>
  )
}
