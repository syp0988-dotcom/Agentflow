import React, { useState, useRef, useCallback, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Chat from './components/Chat'
import InputBox from './components/InputBox'
import WorkflowPanel from './components/WorkflowPanel'
import { postChat, uploadDocument, getDocuments, deleteDocument, searchKnowledge } from './api/client'

type Msg = { id: string; role: 'user' | 'agent'; text: string }

type Section = 'chat' | 'history' | 'knowledge' | 'agents' | 'settings'

type DebugData = {
  category?: string
  workflow?: string[]
  search_results?: Array<{ title: string; url: string; snippet?: string }>
  router?: Record<string, unknown>
}

type KnowledgeDoc = {
  id: number
  filename: string
  file_type: string
  file_size: number
  doc_metadata: string
  created_at: string
}

type SearchResult = {
  chunk_id: number
  document_id: number
  filename: string
  content: string
  score: number
}

export default function App() {
  const [messages, setMessages] = useState<Msg[]>([
    { id: '1', role: 'agent', text: '欢迎使用 OmniForge。' }
  ])
  const [thinking, setThinking] = useState(false)
  const [statusMessage, setStatusMessage] = useState('Ready')
  const [activeSection, setActiveSection] = useState<Section>('chat')
  const [debugData, setDebugData] = useState<DebugData | null>(null)
  const [showDebug, setShowDebug] = useState(false)

  const handleSend = async (text: string) => {
    const id = String(Date.now())
    setMessages(current => [...current, { id, role: 'user', text }])
    setThinking(true)
    setStatusMessage('Thinking...')

    try {
      const data = await postChat(text)
      const reply = data.reply || '[no reply]'
      setDebugData(data.debug || null)
      setMessages(current => [...current, { id: String(Date.now()), role: 'agent', text: reply }])
      setStatusMessage('Ready')
    } catch (error) {
      setMessages(current => [...current, { id: String(Date.now()), role: 'agent', text: '请求失败，请检查后端。' }])
      setStatusMessage('Error sending message')
    } finally {
      setThinking(false)
    }
  }

  // ---- Knowledge base state & handlers ----
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const folderInputRef = useRef<HTMLInputElement>(null)

  const loadDocs = useCallback(async () => {
    try {
      const docs = await getDocuments()
      setDocuments(docs)
    } catch {
      // silently fail
    }
  }, [])

  useEffect(() => {
    if (activeSection === 'knowledge') loadDocs()
  }, [activeSection, loadDocs])

  // -- Drag & drop helpers: traverse directory entries recursively --
  const traverseDir = async (entry: FileSystemEntry): Promise<File[]> => {
    const files: File[] = []
    if (entry.isFile) {
      const fileEntry = entry as FileSystemFileEntry
      const file = await new Promise<File>((resolve, reject) => {
        fileEntry.file(resolve, reject)
      })
      files.push(file)
    } else if (entry.isDirectory) {
      const dirEntry = entry as FileSystemDirectoryEntry
      const reader = dirEntry.createReader()
      const entries = await new Promise<FileSystemEntry[]>((resolve, reject) => {
        reader.readEntries(resolve, reject)
      })
      for (const child of entries) {
        const childFiles = await traverseDir(child)
        files.push(...childFiles)
      }
    }
    return files
  }

  const collectFilesFromDrop = async (items: DataTransferItemList): Promise<File[]> => {
    const allFiles: File[] = []
    for (let i = 0; i < items.length; i++) {
      const entry = items[i].webkitGetAsEntry()
      if (entry) {
        const files = await traverseDir(entry)
        allFiles.push(...files)
      } else if (items[i].kind === 'file') {
        const file = items[i].getAsFile()
        if (file) allFiles.push(file)
      }
    }
    return allFiles
  }

  const uploadFiles = async (files: File[]) => {
    if (files.length === 0) return
    const allowedExts = ['.pdf', '.docx', '.doc', '.txt', '.md', '.markdown']
    const filtered = files.filter(f => {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase()
      return allowedExts.includes(ext)
    })
    if (filtered.length === 0) {
      setUploadStatus('没有支持的文档格式（PDF、DOCX、TXT、MD）')
      return
    }
    setUploading(true)
    let successCount = 0
    let failCount = 0
    for (let i = 0; i < filtered.length; i++) {
      const file = filtered[i]
      setUploadStatus(`正在上传 ${i + 1}/${filtered.length}: ${file.name}...`)
      try {
        await uploadDocument(file)
        successCount++
      } catch {
        failCount++
      }
    }
    setUploadStatus(`上传完成：${successCount} 个成功${failCount > 0 ? `，${failCount} 个失败` : ''}`)
    setUploading(false)
    await loadDocs()
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    await uploadFiles(Array.from(files))
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (folderInputRef.current) folderInputRef.current.value = ''
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (!e.dataTransfer.items || e.dataTransfer.items.length === 0) return
    const files = await collectFilesFromDrop(e.dataTransfer.items)
    await uploadFiles(files)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDelete = async (docId: number, filename: string) => {
    if (!confirm(`确定删除 "${filename}"？`)) return
    try {
      await deleteDocument(docId)
      setDocuments(prev => prev.filter(d => d.id !== docId))
    } catch {
      setUploadStatus('删除失败')
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    try {
      const results = await searchKnowledge(searchQuery.trim(), 10)
      setSearchResults(results)
    } catch {
      setSearchResults([])
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr + 'Z')
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }

  // ---- Section rendering ----
  const renderSection = () => {
    switch (activeSection) {
      case 'history':
        return (
          <div className="space-y-4">
            <div className="text-lg font-semibold">聊天历史</div>
            <div className="text-sm text-muted">点击聊天历史可以快速查看过往对话和会话摘要。</div>
            <div className="grid gap-3">
              {messages.slice(-3).map(msg => (
                <div key={msg.id} className="p-4 bg-[#10101a] rounded-xl">
                  <div className="text-xs text-muted">{msg.role === 'user' ? '用户' : 'OmniForge'}</div>
                  <div className="mt-2 text-sm">{msg.text}</div>
                </div>
              ))}
            </div>
          </div>
        )

      case 'knowledge':
        return (
          <div className="space-y-6">
            <div className="text-lg font-semibold">知识库</div>
            <div className="text-sm text-muted">上传文档（PDF、Word、TXT、Markdown），系统将自动解析、分块并向量化存储。</div>

            {/* Upload area */}
            <div
              className={`border-2 border-dashed rounded-2xl p-8 text-center transition cursor-pointer ${
                dragOver
                  ? 'border-primary bg-primary/5'
                  : 'border-[#2d2d3a] hover:border-primary/50'
              }`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.txt,.md,.markdown"
                className="hidden"
                multiple
                onChange={handleFileSelect}
              />
              <input
                ref={folderInputRef}
                type="file"
                className="hidden"
                // @ts-ignore webkitdirectory is a non-standard attribute
                webkitdirectory=""
                onChange={handleFileSelect}
              />
              <div className="text-3xl mb-2 text-muted">{dragOver ? '📂' : '📄'}</div>
              <div className="text-sm text-muted">
                {uploading
                  ? '上传中...'
                  : '拖拽文件或文件夹到此处'}
              </div>
              <div className="text-xs text-muted mt-1">
                支持 PDF、DOCX、TXT、Markdown 格式（可多选或拖拽文件夹）
              </div>
              <div className="flex gap-3 justify-center mt-3">
                <button
                  type="button"
                  onClick={e => { e.stopPropagation(); fileInputRef.current?.click() }}
                  className="px-4 py-1.5 rounded-lg bg-primary text-black text-sm"
                >
                  选择文件
                </button>
                <button
                  type="button"
                  onClick={e => { e.stopPropagation(); folderInputRef.current?.click() }}
                  className="px-4 py-1.5 rounded-lg bg-[#2d2d3a] text-text text-sm"
                >
                  选择文件夹
                </button>
              </div>
            </div>

            {uploadStatus && (
              <div className={`text-sm p-3 rounded-xl ${uploadStatus.includes('成功') ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                {uploadStatus}
              </div>
            )}

            {/* Search */}
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="搜索知识库..."
                className="flex-1 px-4 py-2 rounded-xl bg-[#10101a] border border-[#2d2d3a] text-text placeholder:text-muted focus:outline-none focus:border-primary"
              />
              <button
                type="button"
                onClick={handleSearch}
                className="px-4 py-2 rounded-xl bg-primary text-black font-medium"
              >
                搜索
              </button>
            </div>

            {/* Search results */}
            {searchResults !== null && (
              <div className="space-y-2">
                <div className="text-sm font-semibold text-muted">
                  搜索结果 ({searchResults.length} 条)
                </div>
                {searchResults.length === 0 ? (
                  <div className="text-sm text-muted p-4 bg-[#10101a] rounded-xl">未找到相关结果</div>
                ) : (
                  searchResults.map(r => (
                    <div key={r.chunk_id} className="p-4 bg-[#10101a] rounded-xl space-y-1">
                      <div className="text-xs text-muted">
                        {r.filename} · 相似度: {(r.score * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm line-clamp-3">{r.content}</div>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Document list */}
            <div className="space-y-2">
              <div className="text-sm font-semibold text-muted">
                已索引文档 ({documents.length})
              </div>
              {documents.length === 0 ? (
                <div className="text-sm text-muted p-4 bg-[#10101a] rounded-xl">暂无文档</div>
              ) : (
                documents.map(doc => (
                  <div key={doc.id} className="p-4 bg-[#10101a] rounded-xl flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium truncate">{doc.filename}</div>
                      <div className="text-xs text-muted mt-1">
                        {doc.file_type.toUpperCase()} · {formatSize(doc.file_size)} · {formatDate(doc.created_at)}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      className="ml-4 px-3 py-1.5 rounded-lg text-xs bg-danger/20 text-danger hover:bg-danger/30 transition"
                    >
                      删除
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )

      case 'agents':
        return (
          <div className="space-y-4">
            <div className="text-lg font-semibold">Agent 管理</div>
            <div className="text-sm text-muted">管理 OmniForge 中的自定义智能 Agent，并配置它们的工作流。</div>
            <div className="grid gap-3">
              <div className="p-4 bg-[#10101a] rounded-xl flex items-center justify-between">
                <div>
                  <div className="font-medium">Code Assistant</div>
                  <div className="text-xs text-muted">擅长修复代码、生成测试用例和优化方案</div>
                </div>
                <button type="button" className="px-3 py-2 rounded-lg bg-primary text-black">管理</button>
              </div>
              <div className="p-4 bg-[#10101a] rounded-xl flex items-center justify-between">
                <div>
                  <div className="font-medium">Research Agent</div>
                  <div className="text-xs text-muted">擅长查找资料、总结背景和生成执行策略</div>
                </div>
                <button type="button" className="px-3 py-2 rounded-lg bg-primary text-black">管理</button>
              </div>
            </div>
          </div>
        )

      case 'settings':
        return (
          <div className="space-y-4">
            <div className="text-lg font-semibold">设置</div>
            <div className="text-sm text-muted">配置 API 端点、激活模式和工作流参数。</div>
            <div className="grid gap-3">
              <button type="button" className="w-full text-left p-4 rounded-xl bg-[#10101a] hover:bg-hover">更改模型与令牌限制</button>
              <button type="button" className="w-full text-left p-4 rounded-xl bg-[#10101a] hover:bg-hover">知识库源配置</button>
            </div>
          </div>
        )

      default:
        return <Chat messages={messages} thinking={thinking} />
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <div className="flex flex-1">
        <aside className="w-64 p-4 border-r border-[#19191b]">
          <Sidebar activeSection={activeSection} onSelect={setActiveSection} />
        </aside>
        <main className="flex-1 p-6 overflow-auto">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-muted">{statusMessage}</div>
            <div className="flex gap-2">
              {activeSection !== 'chat' && (
                <button
                  type="button"
                  onClick={() => setActiveSection('chat')}
                  className="px-3 py-2 rounded-lg bg-primary text-black"
                >
                  返回聊天
                </button>
              )}
              <button
                type="button"
                onClick={() => setShowDebug(current => !current)}
                className="px-3 py-2 rounded-lg bg-[#2d2d3a] text-white"
              >
                {showDebug ? '隐藏开发者模式' : '显示开发者模式'}
              </button>
            </div>
          </div>
          <div className="rounded-3xl bg-card h-full p-4">
            {renderSection()}
          </div>
        </main>
        {showDebug && (
          <aside className="w-96 p-4 border-l border-[#19191b] hidden lg:block">
            <div className="glass rounded-lg p-3 h-full overflow-auto">
              <WorkflowPanel debug={debugData} />
            </div>
          </aside>
        )}
      </div>
      <footer className="fixed bottom-4 left-1/2 transform -translate-x-1/2 w-[90%] max-w-6xl">
        <InputBox onSend={handleSend} />
      </footer>
    </div>
  )
}
