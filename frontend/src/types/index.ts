export interface Msg {
  id: string
  role: 'user' | 'agent'
  text: string
}

export type Section = 'chat' | 'agents' | 'knowledge' | 'artifacts'

export interface DebugData {
  category?: string
  workflow?: string[]
  search_results?: Array<{ title: string; url: string; snippet?: string }>
  router?: Record<string, unknown>
}

export interface KnowledgeDoc {
  id: number
  filename: string
  file_type: string
  file_size: number
  doc_metadata: string
  created_at: string
}

export interface SearchResult {
  chunk_id: number
  document_id: number
  filename: string
  content: string
  score: number
}
