import axios from 'axios'

import type { AgentInfo, CreatedFile, Session } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export async function postChat(message: string, history?: Array<{ role: string; content: string }>, sessionId?: number) {
  const resp = await axios.post(`${API_BASE}/chat`, { message, history: history || [], session_id: sessionId })
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

/* ---- Agents introspection ------------------------------------------- */

export async function getAgents() {
  const resp = await axios.get(`${API_BASE}/agents`)
  return resp.data as AgentInfo[]
}

/* ---- Sessions ----------------------------------------------------------- */

export async function createSession() {
  const resp = await axios.post(`${API_BASE}/sessions/create`)
  return resp.data as Session
}

export async function listSessions(limit = 50) {
  const resp = await axios.get(`${API_BASE}/sessions`, { params: { limit } })
  return resp.data as Session[]
}

export async function getSessionMessages(sessionId: number) {
  const resp = await axios.get(`${API_BASE}/sessions/${sessionId}/messages`)
  return resp.data as Array<{ id: number; role: string; content: string; created_at: string }>
}

export async function renameSession(sessionId: number, title: string) {
  const resp = await axios.put(`${API_BASE}/sessions/${sessionId}/rename`, { title })
  return resp.data as { status: string }
}

export async function deleteSession(sessionId: number) {
  const resp = await axios.delete(`${API_BASE}/sessions/${sessionId}`)
  return resp.data as { status: string }
}

/* ---- Chat history ------------------------------------------------------- */

export async function getHistory(limit = 50) {
  const resp = await axios.get(`${API_BASE}/history`, { params: { limit } })
  return resp.data as Array<{ role: string; content: string; created_at: string }>
}

/* ---- Agent-generated file operations ------------------------------------ */

export async function createFile(filename: string, content: string, workspacePath?: string) {
  const resp = await axios.post(`${API_BASE}/files/create`, { filename, content, workspace_path: workspacePath })
  return resp.data as { status: string; filename: string; path: string }
}

export async function getOutputFiles(workspacePath?: string) {
  const params = workspacePath ? { workspace_path: workspacePath } : {}
  const resp = await axios.get(`${API_BASE}/files`, { params })
  return resp.data as CreatedFile[]
}

/* ---- Workspace operations ----------------------------------------------- */

export async function setWorkspace(path: string) {
  const resp = await axios.post(`${API_BASE}/workspace/set`, { path })
  return resp.data as { status: string; path: string }
}

export async function createServerFolder(parentPath: string, folderName: string) {
  const resp = await axios.post(`${API_BASE}/workspace/create-folder`, {
    parent_path: parentPath,
    folder_name: folderName,
  })
  return resp.data as { status: string; path: string }
}

export async function browseDirectory(path: string) {
  const resp = await axios.get(`${API_BASE}/workspace/browse`, { params: { path } })
  return resp.data as {
    current_path: string
    entries: Array<{ name: string; is_dir: boolean; path: string }>
  }
}

/* ---- Model configuration ---- */

export async function getModels() {
  const resp = await axios.get(`${API_BASE}/models`)
  return resp.data as Array<{
    id: number
    name: string
    provider: string
    base_url: string
    model_name: string
    temperature: number
    max_tokens: number
    is_active: boolean
    created_at: string
    updated_at: string
  }>
}

export async function createModel(data: {
  name: string
  provider?: string
  base_url: string
  api_key: string
  model_name: string
  temperature?: number
  max_tokens?: number
}) {
  const resp = await axios.post(`${API_BASE}/models`, data)
  return resp.data as { id: number; status: string }
}

export async function updateModel(id: number, data: Record<string, unknown>) {
  const resp = await axios.put(`${API_BASE}/models/${id}`, data)
  return resp.data as { status: string }
}

export async function deleteModel(id: number) {
  const resp = await axios.delete(`${API_BASE}/models/${id}`)
  return resp.data as { status: string }
}

export async function activateModel(id: number) {
  const resp = await axios.post(`${API_BASE}/models/${id}/activate`)
  return resp.data as { status: string; model_name: string }
}
