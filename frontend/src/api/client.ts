import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export async function postChat(message: string) {
  const resp = await axios.post(`${API_BASE}/chat`, { message })
  return resp.data
}

export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  const resp = await axios.post(`${API_BASE}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return resp.data
}

export async function getDocuments() {
  const resp = await axios.get(`${API_BASE}/knowledge/documents`)
  return resp.data as Array<{
    id: number
    filename: string
    file_type: string
    file_size: number
    doc_metadata: string
    created_at: string
  }>
}

export async function deleteDocument(docId: number) {
  const resp = await axios.delete(`${API_BASE}/knowledge/documents/${docId}`)
  return resp.data
}

export async function searchKnowledge(query: string, topK = 5) {
  const resp = await axios.post(`${API_BASE}/knowledge/search`, null, {
    params: { query, top_k: topK }
  })
  return resp.data as Array<{
    chunk_id: number
    document_id: number
    filename: string
    content: string
    score: number
  }>
}
