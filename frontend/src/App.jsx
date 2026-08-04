import { useState } from 'react'
import Sidebar from './components/Sidebar'
import UploadPanel from './components/UploadPanel'
import DocumentViewer from './components/DocumentViewer'
import QueryPanel from './components/QueryPanel'

export default function App() {
  const [selected, setSelected] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const bumpRefresh = () => setRefreshKey((k) => k + 1)

  return (
    <div className="h-full flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">
            Compliance Document Analyzer
          </h1>
          <p className="text-xs text-slate-500">
            Upload, browse, and query your compliance documents.
          </p>
        </div>
        <span className="text-xs text-slate-400 font-mono">FastAPI · React · Tailwind</span>
      </header>

      <div className="flex-1 flex min-h-0">
        <Sidebar
          selected={selected}
          onSelect={setSelected}
          refreshKey={refreshKey}
          onChange={bumpRefresh}
        />
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          <section>
            <h2 className="text-sm font-semibold text-slate-700 mb-2">
              Upload documents
            </h2>
            <UploadPanel onUploaded={bumpRefresh} />
          </section>

          <section>
            <h2 className="text-sm font-semibold text-slate-700 mb-2">
              Preview
            </h2>
            <DocumentViewer filename={selected} />
          </section>

          <section>
            <h2 className="text-sm font-semibold text-slate-700 mb-2">
              Ask questions
            </h2>
            <QueryPanel />
          </section>
        </main>
      </div>
    </div>
  )
}
