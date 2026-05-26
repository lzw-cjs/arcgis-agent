import { useEffect, useRef, useCallback } from 'react'
import { Alert, Empty, Button } from 'antd'
import { useChatStore } from '../stores/chatStore'
import { sendMessage } from '../api/chat'
import { MessageBubble } from './MessageBubble'
import { InputBox } from './InputBox'
import { SuggestionBar } from './SuggestionBar'
import type { Message, ToolCall } from '../types'

export function ChatPanel() {
  const {
    messages, sessionId, loading, error,
    addMessage, appendContent, setLoading,
    addToolCallToLastMessage, updateLastToolCall,
    setSuggestions, setError,
  } = useChatStore()

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  const handleSend = async (text: string) => {
    if (!text.trim() || loading) return

    // Add user message
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    }
    addMessage(userMsg)
    setLoading(true)
    setError(null)

    // Add placeholder assistant message
    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    addMessage(assistantMsg)

    let fullContent = ''

    try {
      for await (const evt of sendMessage(sessionId, text)) {
        switch (evt.event) {
          case 'token': {
            const content = (evt.data as { content: string }).content || ''
            fullContent += content
            appendContent(content)
            scrollToBottom()
            break
          }
          case 'tool_start': {
            const call: ToolCall = {
              name: (evt.data as { name: string }).name,
              args: (evt.data as { args: Record<string, unknown> }).args || {},
              status: 'running',
            }
            addToolCallToLastMessage(call)
            break
          }
          case 'tool_end': {
            const data = evt.data as { name: string; success: boolean; result: string }
            updateLastToolCall({
              status: data.success ? 'success' : 'error',
              success: data.success,
              result: data.result,
            })
            break
          }
          case 'suggestions': {
            const items = (evt.data as { items: string[] }).items || []
            setSuggestions(items)
            break
          }
          case 'error': {
            const msg = (evt.data as { message: string }).message || 'Unknown error'
            setError(msg)
            break
          }
          case 'done':
            // Stream complete
            break
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 56px)',
      maxWidth: 860,
      margin: '0 auto',
      padding: '0 16px',
    }}>
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 0',
      }}>
        {error && (
          <Alert
            type="error"
            message="连接失败"
            description={error}
            closable
            onClose={() => setError(null)}
            action={<Button size="small" onClick={() => setError(null)}>重试</Button>}
            style={{ marginBottom: 16 }}
          />
        )}

        {messages.length === 0 && !loading && (
          <div style={{
            textAlign: 'center',
            padding: '64px 16px',
          }}>
            <Empty description={false}>
              <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
                GIS 智能助手
              </h2>
              <p style={{ color: '#8C8C8C', fontSize: 14, maxWidth: 400, margin: '0 auto' }}>
                在下方输入您的 GIS 操作需求，AI 助手将帮助您完成空间分析和地图制作。
              </p>
            </Empty>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && messages.length > 0 && (
          <div style={{ padding: 12, color: '#8C8C8C', fontSize: 13 }}>
            AI 正在思考...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Bar */}
      {!loading && messages.length > 0 && (
        <SuggestionBar onSelect={handleSend} />
      )}

      {/* Input Box */}
      <InputBox onSend={handleSend} disabled={loading} />
    </div>
  )
}
