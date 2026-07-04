import React from 'react'

type SidebarProps = {
  activeSection: string
  onSelect: (section: string) => void
}

const items = [
  { key: 'chat', label: '聊天历史' },
  { key: 'knowledge', label: '知识库' },
  { key: 'agents', label: 'Agent 管理' },
  { key: 'settings', label: '设置' }
]

export default function Sidebar({ activeSection, onSelect }: SidebarProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center text-black font-bold">OF</div>
        <div>
          <div className="text-white font-semibold">OmniForge</div>
          <div className="text-muted text-sm">Developer AI Workspace</div>
        </div>
      </div>

      <nav className="mt-6">
        <ul className="space-y-2 text-sm">
          {items.map(item => (
            <li key={item.key}>
              <button
                type="button"
                onClick={() => onSelect(item.key)}
                className={`w-full text-left p-2 rounded-lg transition ${
                  activeSection === item.key
                    ? 'bg-primary text-black'
                    : 'hover:bg-hover text-text'
                }`}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}
