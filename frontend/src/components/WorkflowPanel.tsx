import React, { useState } from 'react'
import { motion } from 'framer-motion'
import Thinking from './Thinking'

const defaultSteps = [
  { key: 'planner', label: 'Planning', done: false },
  { key: 'search', label: 'Searching', done: false },
  { key: 'knowledge', label: 'Reading Knowledge', done: false },
  { key: 'python', label: 'Running Python', done: false },
  { key: 'report', label: 'Generating Report', done: false }
]

type WorkflowPanelProps = {
  workflow?: string[]
  onReset?: () => void
}

export default function WorkflowPanel({ workflow = [], onReset }: WorkflowPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(null)

  const steps = defaultSteps.map(s => ({ ...s, done: workflow.includes(s.key) }))

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm text-muted">Workflow</div>
          <div className="text-lg font-semibold">执行步骤</div>
        </div>
        {workflow.length > 0 && onReset && (
          <button
            type="button"
            onClick={onReset}
            className="px-3 py-2 rounded-lg bg-primary text-black text-sm"
          >
            重置
          </button>
        )}
      </div>

      <Thinking steps={steps} />

      <div className="mt-2">
        {steps.map(s => (
          <motion.div key={s.key} layout className="mb-2">
            <button
              type="button"
              onClick={() => setExpanded(expanded === s.key ? null : s.key)}
              className="w-full text-left"
            >
              <div className="flex items-center justify-between p-2 rounded-lg hover:bg-hover transition">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${s.done ? 'bg-success' : 'bg-[#444]'}`} />
                  <div className="text-sm">{s.label}</div>
                </div>
                <div className="text-xs text-muted">{expanded === s.key ? '收起' : s.done ? '完成' : '展开'}</div>
              </div>
            </button>

            {expanded === s.key && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 bg-card rounded mt-2">
                <div className="text-xs text-muted">Prompt</div>
                <pre className="text-sm whitespace-pre-wrap">当前步骤：{s.label}</pre>
                <div className="text-xs text-muted mt-2">Output</div>
                <pre className="text-sm whitespace-pre-wrap">{s.done ? '已完成输出' : '等待运行结果...'}</pre>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}
