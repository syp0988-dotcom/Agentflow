import React, { useEffect, useRef } from 'react'
import Thinking from './Thinking'
import MarkdownMessage from './MarkdownMessage'

type Msg = { id: string; role: 'user' | 'agent'; text: string }

type ChatProps = {
  messages: Msg[]
  thinking: boolean
}

function Message({ side = 'left', children }: { side?: 'left' | 'right'; children: React.ReactNode }) {
  return (
    <div className={`flex ${side === 'right' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] p-4 rounded-lg ${side === 'right' ? 'bg-primary text-black' : 'bg-card text-text'}`}>
        {children}
      </div>
    </div>
  )
}

export default function Chat({ messages, thinking }: ChatProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  return (
    <div className="h-[70vh] overflow-auto" ref={containerRef}>
      {messages.map(m => (
        <Message key={m.id} side={m.role === 'user' ? 'right' : 'left'}>
          <MarkdownMessage content={m.text} />
        </Message>
      ))}

      {thinking && <Thinking steps={[{ key: 'planner', label: 'Planning' }, { key: 'search', label: 'Searching' }, { key: 'report', label: 'Generating Report' }]} />}
    </div>
  )
}
