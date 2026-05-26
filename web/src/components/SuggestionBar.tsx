import { Button, Space } from 'antd'
import { BulbOutlined } from '@ant-design/icons'
import { useChatStore } from '../stores/chatStore'

interface Props {
  onSelect: (text: string) => void
}

export function SuggestionBar({ onSelect }: Props) {
  const messages = useChatStore((s) => s.messages)
  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === 'assistant')

  if (!lastAssistantMsg?.suggestions?.length) {
    return null
  }

  return (
    <div style={{
      padding: '8px 0',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      overflowX: 'auto',
    }}>
      <BulbOutlined style={{ color: '#1677FF', fontSize: 14, flexShrink: 0 }} />
      <Space size={8} style={{ flexWrap: 'nowrap' }}>
        {lastAssistantMsg.suggestions.map((text, idx) => (
          <Button
            key={idx}
            size="small"
            type="default"
            onClick={() => onSelect(text)}
            style={{
              whiteSpace: 'nowrap',
              fontSize: 13,
              borderRadius: 16,
              borderColor: '#D9D9D9',
            }}
          >
            {text}
          </Button>
        ))}
      </Space>
    </div>
  )
}
