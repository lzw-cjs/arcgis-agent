import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../types'
import { ToolCallCard } from './ToolCallCard'

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
      padding: '0 4px',
    }}>
      <div style={{
        maxWidth: '75%',
        padding: '12px 16px',
        borderRadius: 12,
        background: isUser ? '#1677FF' : '#F5F5F5',
        color: isUser ? '#FFFFFF' : '#262626',
        fontSize: 14,
        lineHeight: '1.5',
        wordBreak: 'break-word',
      }}>
        {isUser ? (
          <div>{message.content}</div>
        ) : (
          <div>
            {message.content ? (
              <div className="markdown-body" style={{ fontSize: 14 }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : (
              <div style={{ color: '#8C8C8C', fontStyle: 'italic' }}>
                AI 正在思考...
              </div>
            )}

            {/* Tool Call Cards */}
            {message.toolCalls?.map((tc, idx) => (
              <ToolCallCard key={`${tc.name}-${idx}`} toolCall={tc} />
            ))}

            {/* Suggestions */}
            {message.suggestions && message.suggestions.length > 0 && (
              <div style={{ marginTop: 12 }}>
                {/* Suggestions rendered by SuggestionBar */}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
