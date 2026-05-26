import { useState, KeyboardEvent } from 'react'
import { Input, Button, Space } from 'antd'
import { SendOutlined } from '@ant-design/icons'

const { TextArea } = Input

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
}

export function InputBox({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      padding: '12px 0 16px',
      borderTop: '1px solid #F0F0F0',
      background: '#FFFFFF',
    }}>
      <Space.Compact style={{ width: '100%', display: 'flex' }}>
        <TextArea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="描述您的 GIS 操作需求..."
          autoSize={{ minRows: 1, maxRows: 4 }}
          style={{
            flex: 1,
            borderRadius: 8,
            fontSize: 14,
            borderColor: disabled ? '#D9D9D9' : undefined,
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          style={{
            borderRadius: 8,
            marginLeft: 8,
            height: 'auto',
            minHeight: 40,
          }}
        >
          发送
        </Button>
      </Space.Compact>
    </div>
  )
}
