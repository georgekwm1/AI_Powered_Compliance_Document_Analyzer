const BASE = 'http://127.0.0.1:8002'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {}
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json()
}

export async function listDocuments() {
  return handle(await fetch(`${BASE}/list_documents`))
}

export async function uploadDocuments(files) {
  const form = new FormData()
  for (const f of files) form.append('files', f)
  return handle(
    await fetch(`${BASE}/upload_documents`, { method: 'POST', body: form }),
  )
}

export async function getDocument(filename) {
  const url = `${BASE}/get_document/?filename=${encodeURIComponent(filename)}`
  return handle(await fetch(url))
}

export async function deleteDocument(filename) {
  const url = `${BASE}/delete_document/?filename=${encodeURIComponent(filename)}`
  return handle(await fetch(url, { method: 'DELETE' }))
}

export async function queryAi(query) {
  return handle(
    await fetch(`${BASE}/query_ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    }),
  )
}
