import { Card, Tag, Spin } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import type { ToolCall } from '../types'

interface Props {
  toolCall: ToolCall
}

export function ToolCallCard({ toolCall }: Props) {
  const isRunning = toolCall.status === 'running'
  const isSuccess = toolCall.status === 'success'
  const isError = toolCall.status === 'error'

  const statusConfig = {
    running: {
      color: 'processing' as const,
      icon: <LoadingOutlined />,
      text: '执行中',
    },
    success: {
      color: 'success' as const,
      icon: <CheckCircleOutlined />,
      text: '成功',
    },
    error: {
      color: 'error' as const,
      icon: <CloseCircleOutlined />,
      text: '失败',
    },
  }

  const config = statusConfig[toolCall.status]

  return (
    <Card
      size="small"
      style={{
        marginTop: 8,
        background: '#FAFAFA',
        border: '1px solid #F0F0F0',
        borderRadius: 8,
      }}
      styles={{ body: { padding: '10px 12px', fontSize: 13 } }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        {isRunning && <Spin size="small" />}
        <span style={{ fontWeight: 600, color: '#1677FF', fontSize: 13 }}>
          {toolCall.name}
        </span>
        <Tag
          color={config.color}
          icon={config.icon}
          style={{ fontSize: 11, lineHeight: '18px', marginRight: 0 }}
        >
          {config.text}
        </Tag>
      </div>

      {/* Args summary */}
      {Object.keys(toolCall.args).length > 0 && (
        <div style={{ color: '#595959', fontSize: 12, marginBottom: 4, wordBreak: 'break-all' }}>
          {Object.entries(toolCall.args).map(([k, v]) => (
            <span key={k} style={{ marginRight: 12 }}>
              <span style={{ color: '#8C8C8C' }}>{k}:</span>{' '}
              <code style={{ fontSize: 11 }}>{String(v).slice(0, 80)}</code>
            </span>
          ))}
        </div>
      )}

      {/* Result */}
      {toolCall.result && (
        <div style={{
          color: isError ? '#FF4D4F' : '#595959',
          fontSize: 12,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
          maxHeight: 120,
          overflowY: 'auto',
          background: '#FFFFFF',
          padding: 6,
          borderRadius: 4,
          border: '1px solid #F0F0F0',
        }}>
          {toolCall.result.slice(0, 500)}
        </div>
      )}
    </Card>
  )
}
