import { defineStore } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useParkingStore } from '@/stores/parking'
import { useDevicesStore } from '@/stores/devices'

export const useWebsocketStore = defineStore('websocket', {
  state: () => ({
    socket: null as WebSocket | null,
    connected: false,
    reconnectInterval: 5000,
    reconnectTimer: null as any | null
  }),
  actions: {
    connect() {
      const authStore = useAuthStore()
      if (!authStore.token) {
        console.warn('Cannot connect to WebSocket: JWT token is missing.')
        return
      }

      if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
        return
      }

      // Base URL from env config or fallback to gateway public port
      const wsBaseUrl = import.meta.env.VITE_GATEWAY_WS_URL || 'ws://localhost:8300/ws/web'
      const wsUrl = `${wsBaseUrl}?token=${authStore.token}`

      console.log(`Connecting to WebSocket Gateway: ${wsBaseUrl}`)
      this.socket = new WebSocket(wsUrl)

      this.socket.onopen = () => {
        console.log('WebSocket Gateway connected successfully.')
        this.connected = true
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer)
          this.reconnectTimer = null
        }
      }

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('Received realtime message:', data)
          
          const parkingStore = useParkingStore()
          const devicesStore = useDevicesStore()

          // Process realtime event router
          if (data.event_type) {
            parkingStore.handleRealtimeEvent(data)
            
            // Auto update device status locally if we receive heartbeat updates
            if (data.event_type.startsWith('device.')) {
              const deviceCode = data.source_id || data.payload?.device_code
              if (deviceCode) {
                devicesStore.updateDeviceStatus(deviceCode, 'online')
              }
            } else if (data.event_type.startsWith('camera.')) {
              const cameraCode = data.source_id || data.payload?.camera_code
              if (cameraCode) {
                devicesStore.updateCameraStatus(cameraCode, 'online')
              }
            }
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      this.socket.onclose = (event) => {
        console.warn(`WebSocket closed: Code ${event.code}. Reconnecting in 5s...`)
        this.connected = false
        this.socket = null
        this.scheduleReconnect()
      }

      this.socket.onerror = (err) => {
        console.error('WebSocket encountered an error:', err)
        this.connected = false
      }
    },
    disconnect() {
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
      if (this.socket) {
        this.socket.close()
        this.socket = null
      }
      this.connected = false
    },
    scheduleReconnect() {
      if (this.reconnectTimer) return
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null
        this.connect()
      }, this.reconnectInterval)
    }
  }
})
