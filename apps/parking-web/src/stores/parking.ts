import { defineStore } from 'pinia'
import api from '@/services/api'

export interface ParkingSession {
  id: string
  session_code: string
  card_uid: string
  entry_time: string
  exit_time: string | null
  entry_plate_number: string | null
  exit_plate_number: string | null
  calculated_fee: number
  status: string // active, completed
  payment_status: string // unpaid, paid
}

export interface RealtimeLog {
  id: string
  time: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

export const useParkingStore = defineStore('parking', {
  state: () => ({
    sessions: [] as ParkingSession[],
    // Lane Monitor states
    activeEntrySession: null as any | null,
    activeExitSession: null as any | null,
    realtimeLogs: [] as RealtimeLog[],
    loading: false,
    error: null as string | null
  }),
  actions: {
    async fetchSessions(filters: { plate_number?: string, status?: string } = {}) {
      this.loading = true
      try {
        const params = new URLSearchParams()
        if (filters.plate_number) params.append('plate_number', filters.plate_number)
        if (filters.status) params.append('status', filters.status)
        
        const response = await api.get('/api/v1/parking/sessions', { params })
        this.sessions = response.data
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    // Trực tiếp checkout qua REST API
    async checkoutSession(cardUid: string, gateCode: string, plateNumber?: string) {
      try {
        const response = await api.post('/api/v1/parking/check-out', {
          card_uid: cardUid,
          gate_code: gateCode,
          plate_number: plateNumber
        })
        this.addLog({
          message: `Xác nhận cho xe ra thành công: ${cardUid} (${plateNumber || ''})`,
          type: 'success'
        })
        return response.data
      } catch (err: any) {
        this.addLog({
          message: `Lỗi xác nhận xe ra: ${err.response?.data?.detail || err.message}`,
          type: 'error'
        })
        throw err
      }
    },
    addLog(log: Omit<RealtimeLog, 'id' | 'time'>) {
      const newLog: RealtimeLog = {
        id: Math.random().toString(36).substring(7),
        time: new Date().toLocaleTimeString(),
        ...log
      }
      this.realtimeLogs.unshift(newLog)
      if (this.realtimeLogs.length > 50) {
        this.realtimeLogs.pop()
      }
    },
    handleRealtimeEvent(event: { event_type: string, payload: any, gate_id?: string }) {
      const { event_type, payload } = event
      
      const getStreamUrl = (mediaId?: string) => {
        if (!mediaId) return ''
        const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        return `${baseURL}/api/v1/media/${mediaId}/stream`
      }

      if (event_type === 'parking.checkin.created') {
        this.activeEntrySession = {
          ...payload,
          timestamp: new Date().toLocaleTimeString(),
          plate_image_url: getStreamUrl(payload.entry_plate_image_id),
          overview_image_url: getStreamUrl(payload.entry_overview_image_id),
          image_url: getStreamUrl(payload.entry_plate_image_id) || `https://picsum.photos/seed/${payload.session_code}/640/480`
        }
        this.addLog({
          message: `Xe vào: Thẻ ${payload.card_uid} | Biển số: ${payload.entry_plate_number || 'Không rõ'}`,
          type: 'success'
        })
      } else if (event_type === 'parking.checkout.completed') {
        this.activeExitSession = {
          ...payload,
          timestamp: new Date().toLocaleTimeString(),
          entry_plate_image_url: getStreamUrl(payload.entry_plate_image_id),
          entry_overview_image_url: getStreamUrl(payload.entry_overview_image_id),
          exit_plate_image_url: getStreamUrl(payload.exit_plate_image_id),
          exit_overview_image_url: getStreamUrl(payload.exit_overview_image_id),
          image_entry_url: getStreamUrl(payload.entry_plate_image_id) || `https://picsum.photos/seed/${payload.session_code}/640/480`,
          image_exit_url: getStreamUrl(payload.exit_plate_image_id) || `https://picsum.photos/seed/${payload.session_code}_out/640/480`
        }
        this.addLog({
          message: `Xe ra: Thẻ ${payload.card_uid} | Biển số: ${payload.exit_plate_number || 'Không rõ'} | Phí: ${payload.calculated_fee.toLocaleString()}đ`,
          type: 'info'
        })
      }
    }
  }
})
