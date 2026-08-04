import { useRef, useState } from 'react'
import { uploadDocuments } from '../api'

export default function UploadPanel({ onUploaded }) {
  const inputRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  async function handleFiles(fileList) {
    const files = Array.from(fileList).filter((f) => f.size > 0)
    if (files.length === 0) return
    setUploading(true)
    setMessage(null)
    try {
      const res = await uploadDocuments(files)
      setMessage({ type: 'ok', text: res.message || 'Uploaded.' })
      onUploaded?.()
    } catch (e) {
      setMessage({ type: 'err', text: e.message })
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      className={`rounded-lg border-2 border-dashed p-6 text-center transition ${
        isDragging
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-slate-300 bg-white'
      }`}
    >
      <p className="text-sm text-slate-600">
        Drag & drop <span className="font-medium">.txt</span> or{' '}
        <span className="font-medium">.pdf</span> files here, or
      </p>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="mt-3 inline-flex items-center px-4 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {uploading ? 'Uploading…' : 'Choose files'}
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".txt,.pdf"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {message && (
        <p
          className={`mt-3 text-sm ${
            message.type === 'ok' ? 'text-emerald-700' : 'text-rose-600'
          }`}
        >
          {message.text}
        </p>
      )}
    </div>
  )
}
