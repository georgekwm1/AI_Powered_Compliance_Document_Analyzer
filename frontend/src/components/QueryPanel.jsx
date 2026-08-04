import { useState } from 'react'
import { queryAi } from '../api'

export default function QueryPanel() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await queryAi(q)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-4 py-2.5">
        <h3 className="text-sm font-semibold text-slate-800">Query the AI</h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Ask a question about the uploaded compliance documents.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-4 space-y-3">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          placeholder="e.g. What is the policy on vehicle inspections?"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <div className="flex items-center justify-between">
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="inline-flex items-center px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Thinking…' : 'Ask'}
          </button>
          {loading && (
            <span className="text-xs text-slate-500">
              Embedding & retrieving relevant chunks…
            </span>
          )}
        </div>
      </form>

      {error && (
        <div className="mx-4 mb-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {error}
        </div>
      )}

      {result && (
        <div className="border-t border-slate-200 p-4 space-y-3">
          <div>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
              Response
            </h4>
            <div className="rounded-md bg-slate-50 border border-slate-200 p-3 text-sm text-slate-800 whitespace-pre-wrap">
              {typeof result.response === 'string'
                ? result.response
                : JSON.stringify(result.response, null, 2)}
            </div>
          </div>
          {Array.isArray(result.distances) && result.distances.length > 0 && (
            <details className="text-xs text-slate-500">
              <summary className="cursor-pointer hover:text-slate-700">
                Retrieval distances ({result.distances.flat().length})
              </summary>
              <pre className="mt-2 rounded-md bg-slate-50 border border-slate-200 p-2 overflow-x-auto">
                {JSON.stringify(result.distances, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  )
}
