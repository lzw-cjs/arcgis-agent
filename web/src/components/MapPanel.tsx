import { useRef, useEffect } from 'react'
import { Spin } from 'antd'

export function MapPanel() {
  const mapRef = useRef<HTMLDivElement>(null)
  const apiKey = import.meta.env.VITE_ARCGIS_API_KEY || ''

  useEffect(() => {
    if (!apiKey || !mapRef.current) return

    // Dynamically load ArcGIS Maps SDK
    const loadMap = async () => {
      try {
        // Using @arcgis/core for vanilla JS integration
        const esriConfig = (await import('@arcgis/core/config')).default
        esriConfig.apiKey = apiKey

        const Map = (await import('@arcgis/core/Map')).default
        const MapView = (await import('@arcgis/core/views/MapView')).default

        const map = new Map({
          basemap: 'topo-vector',
        })

        const view = new MapView({
          container: mapRef.current!,
          map,
          center: [116.4074, 39.9042], // Beijing
          zoom: 10,
        })

        return () => {
          view.destroy()
        }
      } catch (err) {
        console.error('Failed to load ArcGIS map:', err)
      }
    }

    loadMap()
  }, [apiKey])

  if (!apiKey) {
    return (
      <div style={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        color: '#8C8C8C',
        fontSize: 14,
        background: '#FFFFFF',
      }}>
        <div style={{ textAlign: 'center' }}>
          <p>未设置 ArcGIS API Key</p>
          <p style={{ fontSize: 12 }}>
            请在 web/.env.local 中设置 VITE_ARCGIS_API_KEY
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', position: 'relative', background: '#F5F5F5' }}>
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 0,
      }}>
        <Spin tip="地图加载中..." />
      </div>
      <div ref={mapRef} style={{ width: '100%', height: '100%', zIndex: 1 }} />
    </div>
  )
}
