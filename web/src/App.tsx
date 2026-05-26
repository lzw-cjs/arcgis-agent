import { Routes, Route } from 'react-router-dom'
import { Layout, ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ChatPanel } from './components/ChatPanel'
import { MapPanel } from './components/MapPanel'
import { useChatStore } from './stores/chatStore'

const { Header, Content } = Layout

function App() {
  const mapPanelOpen = useChatStore((s) => s.mapPanelOpen)
  const toggleMapPanel = useChatStore((s) => s.toggleMapPanel)

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1677FF',
          colorError: '#FF4D4F',
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif",
          fontSize: 14,
          paddingContentHorizontal: 16,
          paddingContentVertical: 12,
        },
      }}
    >
      <Layout style={{ height: '100vh', background: '#FFFFFF' }}>
        <Header style={{
          background: '#FFFFFF',
          borderBottom: '1px solid #F0F0F0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          height: 56,
        }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>GIS 智能助手</span>
          <button
            onClick={toggleMapPanel}
            style={{
              padding: '4px 12px',
              cursor: 'pointer',
              background: 'transparent',
              border: '1px solid #D9D9D9',
              borderRadius: 6,
              fontSize: 14,
            }}
          >
            {mapPanelOpen ? '隐藏地图' : '查看地图'}
          </button>
        </Header>
        <Layout style={{ background: '#FFFFFF' }}>
          <Content style={{ background: '#FFFFFF', position: 'relative' }}>
            <Routes>
              <Route path="/" element={<ChatPanel />} />
            </Routes>
          </Content>
          {mapPanelOpen && (
            <div style={{ width: '40%', minWidth: 360, borderLeft: '1px solid #F0F0F0' }}>
              <MapPanel />
            </div>
          )}
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}

export default App
